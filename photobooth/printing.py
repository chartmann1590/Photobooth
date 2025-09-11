"""
Printing functionality using CUPS/pycups
"""
import os
import logging
from typing import Dict, List, Any, Optional
import tempfile

try:
    import cups
    CUPS_AVAILABLE = True
except ImportError:
    CUPS_AVAILABLE = False
    logging.warning("pycups not available - printing disabled")

from flask import current_app
from .models import log_print_job, update_print_job_status, get_setting
from .imaging import create_test_print_image, optimize_image_for_print

logger = logging.getLogger(__name__)

def get_cups_connection():
    """Get CUPS connection"""
    if not CUPS_AVAILABLE:
        raise RuntimeError("CUPS/pycups not available")
    
    try:
        conn = cups.Connection()
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to CUPS: {e}")
        raise

def get_printers() -> List[Dict[str, Any]]:
    """Get list of available printers"""
    if not CUPS_AVAILABLE:
        return []
    
    try:
        conn = get_cups_connection()
        printers = conn.getPrinters()
        
        printer_list = []
        for name, info in printers.items():
            printer_list.append({
                'name': name,
                'description': info.get('printer-info', name),
                'location': info.get('printer-location', ''),
                'state': info.get('printer-state', 0),
                'state_message': info.get('printer-state-message', ''),
                'accepting_jobs': info.get('printer-is-accepting-jobs', False),
                'device_uri': info.get('device-uri', '')
            })
        
        logger.info(f"Found {len(printer_list)} printers")
        return printer_list
        
    except Exception as e:
        logger.error(f"Failed to get printers: {e}")
        return []

def get_default_printer() -> Optional[str]:
    """Get default printer name"""
    if not CUPS_AVAILABLE:
        return None
    
    try:
        # First check database setting
        default_printer = get_setting('default_printer')
        if default_printer:
            return default_printer
        
        # Fall back to system default
        conn = get_cups_connection()
        return conn.getDefault()
        
    except Exception as e:
        logger.error(f"Failed to get default printer: {e}")
        return None

def set_default_printer(printer_name: str) -> bool:
    """Set default printer"""
    if not CUPS_AVAILABLE:
        return False
    
    try:
        conn = get_cups_connection()
        conn.setDefault(printer_name)
        logger.info(f"Set default printer to: {printer_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set default printer {printer_name}: {e}")
        return False

def get_printer_status(printer_name: str = None) -> Dict[str, Any]:
    """Get printer status"""
    if not CUPS_AVAILABLE:
        return {
            'available': False,
            'error': 'CUPS not available'
        }
    
    try:
        if printer_name is None:
            printer_name = get_default_printer()
        
        if not printer_name:
            return {
                'available': False,
                'error': 'No printer configured'
            }
        
        conn = get_cups_connection()
        printers = conn.getPrinters()
        
        if printer_name not in printers:
            return {
                'available': False,
                'error': f'Printer {printer_name} not found'
            }
        
        printer_info = printers[printer_name]
        
        return {
            'available': True,
            'name': printer_name,
            'description': printer_info.get('printer-info', printer_name),
            'state': printer_info.get('printer-state', 0),
            'state_message': printer_info.get('printer-state-message', ''),
            'accepting_jobs': printer_info.get('printer-is-accepting-jobs', False),
            'ready': printer_info.get('printer-state') == 3 and printer_info.get('printer-is-accepting-jobs', False)
        }
        
    except Exception as e:
        logger.error(f"Failed to get printer status: {e}")
        return {
            'available': False,
            'error': str(e)
        }

def print_photo(photo_path: str, filename: str, printer_name: str = None) -> Dict[str, Any]:
    """Print a photo"""
    if not CUPS_AVAILABLE:
        return {
            'success': False,
            'error': 'CUPS not available'
        }
    
    try:
        # Get printer
        if printer_name is None:
            printer_name = get_default_printer()
        
        if not printer_name:
            return {
                'success': False,
                'error': 'No printer configured'
            }
        
        # Check if file exists
        if not os.path.exists(photo_path):
            return {
                'success': False,
                'error': 'Photo file not found'
            }
        
        # Optimize image for printing
        try:
            optimized_path = optimize_image_for_print(photo_path)
            print_path = optimized_path
        except Exception as e:
            logger.warning(f"Failed to optimize image, using original: {e}")
            print_path = photo_path
        
        # Get print options
        paper_size = get_setting('print_paper_size', '4x6')
        
        # Set up print options
        options = {
            'media': paper_size,
            'print-quality': '5',  # High quality
            'ColorModel': 'RGB',
            'orientation-requested': '3',  # Portrait
            'fit-to-page': 'true'
        }
        
        # Send print job
        conn = get_cups_connection()
        job_id = conn.printFile(printer_name, print_path, f"PhotoBooth - {filename}", options)
        
        # Log print job
        log_print_job(filename, printer_name, job_id, 'submitted')
        
        logger.info(f"Print job submitted: {job_id} for {filename} on {printer_name}")
        
        return {
            'success': True,
            'job_id': job_id,
            'printer': printer_name
        }
        
    except Exception as e:
        logger.error(f"Failed to print photo {filename}: {e}")
        
        # Log failed print job
        try:
            log_print_job(filename, printer_name, None, 'failed')
        except:
            pass
        
        return {
            'success': False,
            'error': str(e)
        }

def test_print(printer_name: str = None) -> Dict[str, Any]:
    """Print a test page"""
    if not CUPS_AVAILABLE:
        return {
            'success': False,
            'error': 'CUPS not available'
        }
    
    try:
        # Get printer
        if printer_name is None:
            printer_name = get_default_printer()
        
        if not printer_name:
            return {
                'success': False,
                'error': 'No printer configured'
            }
        
        # Create test image
        test_image_path = create_test_print_image()
        
        # Print test image
        result = print_photo(test_image_path, "test_print.jpg", printer_name)
        
        # Clean up test image
        try:
            os.remove(test_image_path)
        except:
            pass
        
        if result['success']:
            logger.info(f"Test print sent to {printer_name}")
            return {
                'success': True,
                'message': f'Test page sent to printer {printer_name}',
                'job_id': result['job_id']
            }
        else:
            return result
        
    except Exception as e:
        logger.error(f"Test print failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_print_jobs(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent print jobs"""
    if not CUPS_AVAILABLE:
        return []
    
    try:
        conn = get_cups_connection()
        
        # Get completed jobs
        jobs = conn.getJobs(which_jobs='completed', limit=limit)
        
        job_list = []
        for job_id, job_info in jobs.items():
            job_list.append({
                'id': job_id,
                'name': job_info.get('job-name', ''),
                'printer': job_info.get('job-printer-uri', '').split('/')[-1] if job_info.get('job-printer-uri') else '',
                'state': job_info.get('job-state', 0),
                'state_message': job_info.get('job-state-message', ''),
                'created_at': job_info.get('time-at-creation', 0),
                'completed_at': job_info.get('time-at-completed', 0)
            })
        
        return sorted(job_list, key=lambda x: x['created_at'], reverse=True)
        
    except Exception as e:
        logger.error(f"Failed to get print jobs: {e}")
        return []

def cancel_print_job(job_id: int, printer_name: str = None) -> bool:
    """Cancel a print job"""
    if not CUPS_AVAILABLE:
        return False
    
    try:
        conn = get_cups_connection()
        conn.cancelJob(job_id)
        
        # Update job status in database
        update_print_job_status(job_id, 'cancelled', 'Cancelled by user')
        
        logger.info(f"Cancelled print job: {job_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to cancel print job {job_id}: {e}")
        return False

def get_printer_capabilities(printer_name: str) -> Dict[str, Any]:
    """Get printer capabilities and options"""
    if not CUPS_AVAILABLE:
        return {}
    
    try:
        conn = get_cups_connection()
        
        # Get printer attributes
        attrs = conn.getPrinterAttributes(printer_name)
        
        # Extract useful capabilities
        capabilities = {
            'media_supported': attrs.get('media-supported', []),
            'print_quality_supported': attrs.get('print-quality-supported', []),
            'color_supported': attrs.get('color-supported', False),
            'duplex_supported': attrs.get('sides-supported', []),
            'resolution_supported': attrs.get('printer-resolution-supported', [])
        }
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get printer capabilities for {printer_name}: {e}")
        return {}

def check_printer_supplies(printer_name: str = None) -> Dict[str, Any]:
    """Check printer supply levels (if supported)"""
    if not CUPS_AVAILABLE:
        return {'supported': False}
    
    try:
        if printer_name is None:
            printer_name = get_default_printer()
        
        if not printer_name:
            return {'supported': False, 'error': 'No printer configured'}
        
        conn = get_cups_connection()
        attrs = conn.getPrinterAttributes(printer_name)
        
        supplies = {}
        
        # Try to get supply information (not all printers support this)
        supply_names = attrs.get('marker-names', [])
        supply_levels = attrs.get('marker-levels', [])
        supply_types = attrs.get('marker-types', [])
        
        if supply_names and supply_levels:
            for i, name in enumerate(supply_names):
                if i < len(supply_levels):
                    supplies[name] = {
                        'level': supply_levels[i],
                        'type': supply_types[i] if i < len(supply_types) else 'unknown'
                    }
        
        return {
            'supported': len(supplies) > 0,
            'supplies': supplies
        }
        
    except Exception as e:
        logger.warning(f"Failed to check printer supplies: {e}")
        return {'supported': False, 'error': str(e)}

def validate_print_settings() -> Dict[str, Any]:
    """Validate current print configuration"""
    issues = []
    
    # Check if CUPS is available
    if not CUPS_AVAILABLE:
        issues.append("CUPS/pycups not installed")
        return {'valid': False, 'issues': issues}
    
    # Check if default printer is set
    default_printer = get_default_printer()
    if not default_printer:
        issues.append("No default printer configured")
    else:
        # Check printer status
        status = get_printer_status(default_printer)
        if not status['available']:
            issues.append(f"Printer not available: {status.get('error', 'Unknown error')}")
        elif not status.get('accepting_jobs', False):
            issues.append("Printer not accepting jobs")
        elif status.get('state', 0) != 3:  # IPP_PRINTER_IDLE
            issues.append(f"Printer not ready: {status.get('state_message', 'Unknown state')}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'printer': default_printer
    }