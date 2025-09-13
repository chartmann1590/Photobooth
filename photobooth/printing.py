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

def get_available_usb_printers() -> List[Dict[str, Any]]:
    """Get list of available USB printers that can be configured"""
    if not CUPS_AVAILABLE:
        return []
    
    try:
        conn = get_cups_connection()
        devices = conn.getDevices()
        
        usb_printers = []
        for device_uri, device_info in devices.items():
            # Look for USB printers
            if 'usb' in device_uri.lower():
                device_class = device_info.get('device-class', '')
                device_info_str = device_info.get('device-info', '')
                device_make_model = device_info.get('device-make-and-model', '')
                
                usb_printers.append({
                    'device_uri': device_uri,
                    'device_info': device_info_str,
                    'make_model': device_make_model,
                    'device_class': device_class,
                    'configured': False
                })
        
        logger.info(f"Found {len(usb_printers)} available USB printer devices")
        return usb_printers
        
    except Exception as e:
        logger.error(f"Failed to get USB printers: {e}")
        return []

def get_printer_driver(make_model: str) -> Optional[str]:
    """Find best driver for a printer make/model"""
    if not CUPS_AVAILABLE:
        return None
    
    try:
        conn = get_cups_connection()
        drivers = conn.getPPDs()
        
        # Try to find exact match first
        make_model_lower = make_model.lower()
        best_driver = None
        best_score = 0
        
        for ppd_name, ppd_info in drivers.items():
            ppd_make_model = ppd_info.get('ppd-make-and-model', '').lower()
            
            # Calculate match score
            score = 0
            for word in make_model_lower.split():
                if word in ppd_make_model:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_driver = ppd_name
        
        # For Canon SELPHY printers, prefer Gutenprint drivers
        if 'canon' in make_model_lower and 'selphy' in make_model_lower:
            for ppd_name, ppd_info in drivers.items():
                if 'gutenprint' in ppd_name.lower() and 'canon' in ppd_name.lower():
                    ppd_make_model = ppd_info.get('ppd-make-and-model', '').lower()
                    if any(model in ppd_make_model for model in make_model_lower.split()):
                        return ppd_name
        
        return best_driver
        
    except Exception as e:
        logger.error(f"Failed to find driver for {make_model}: {e}")
        return None

def auto_configure_usb_printer(device_uri: str, make_model: str, printer_name: str = None) -> Dict[str, Any]:
    """Automatically configure a USB printer"""
    if not CUPS_AVAILABLE:
        return {'success': False, 'error': 'CUPS not available'}
    
    try:
        # Generate printer name if not provided
        if not printer_name:
            printer_name = make_model.replace(' ', '_').replace('-', '_')
        
        # Find best driver
        driver = get_printer_driver(make_model)
        if not driver:
            return {'success': False, 'error': f'No driver found for {make_model}'}
        
        # Configure printer
        conn = get_cups_connection()
        conn.addPrinter(
            name=printer_name,
            device=device_uri,
            ppdname=driver,
            info=f"Auto-configured {make_model}",
            location="USB"
        )
        
        # Enable printer
        conn.enablePrinter(printer_name)
        conn.acceptJobs(printer_name)
        
        logger.info(f"Auto-configured printer: {printer_name} with driver {driver}")
        
        return {
            'success': True,
            'printer_name': printer_name,
            'driver': driver,
            'device_uri': device_uri
        }
        
    except Exception as e:
        logger.error(f"Failed to auto-configure printer {make_model}: {e}")
        return {'success': False, 'error': str(e)}

def get_printers() -> List[Dict[str, Any]]:
    """Get list of available printers (configured and available for setup)"""
    if not CUPS_AVAILABLE:
        return []
    
    try:
        conn = get_cups_connection()
        printers = conn.getPrinters()
        
        printer_list = []
        
        # Add configured printers
        for name, info in printers.items():
            printer_list.append({
                'name': name,
                'description': info.get('printer-info', name),
                'location': info.get('printer-location', ''),
                'state': info.get('printer-state', 0),
                'state_message': info.get('printer-state-message', ''),
                'accepting_jobs': info.get('printer-is-accepting-jobs', False),
                'device_uri': info.get('device-uri', ''),
                'configured': True,
                'available': True
            })
        
        # Add available USB printers that aren't configured
        usb_printers = get_available_usb_printers()
        configured_device_uris = {p['device_uri'] for p in printer_list}
        
        for usb_printer in usb_printers:
            if usb_printer['device_uri'] not in configured_device_uris:
                printer_list.append({
                    'name': f"Setup_{usb_printer['make_model'].replace(' ', '_')}",
                    'description': f"Available: {usb_printer['make_model']}",
                    'location': 'USB',
                    'state': 0,
                    'state_message': 'Ready to configure',
                    'accepting_jobs': False,
                    'device_uri': usb_printer['device_uri'],
                    'make_model': usb_printer['make_model'],
                    'configured': False,
                    'available': True,
                    'can_auto_configure': True
                })
        
        logger.info(f"Found {len(printer_list)} total printers ({len([p for p in printer_list if p['configured']])} configured, {len([p for p in printer_list if not p['configured']])} available)")
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
        state_message = printer_info.get('printer-state-message', '')
        
        # Check for paper mismatch errors
        paper_error = None
        ready = printer_info.get('printer-state') == 3 and printer_info.get('printer-is-accepting-jobs', False)
        
        if 'Incorrect paper loaded' in state_message:
            paper_error = state_message
            ready = False
            if 'CP760' in printer_name or 'SELPHY' in printer_name:
                paper_error += " - Please check that the correct Canon paper cartridge is loaded"
        
        return {
            'available': True,
            'name': printer_name,
            'description': printer_info.get('printer-info', printer_name),
            'state': printer_info.get('printer-state', 0),
            'state_message': state_message,
            'paper_error': paper_error,
            'accepting_jobs': printer_info.get('printer-is-accepting-jobs', False),
            'ready': ready
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
        
        # Set up print options based on printer
        if 'CP760' in printer_name or 'SELPHY' in printer_name:
            # Canon SELPHY CP760 specific options
            options = {
                'PageSize': 'Postcard',
                'media': 'Postcard', 
                'ColorModel': 'RGB',
                'StpBorderless': 'True',
                'StpImageType': 'Photo',
                'Resolution': '300dpi',
                'orientation-requested': '3'  # Portrait
            }
        else:
            # Generic printer options
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

def get_all_print_jobs(include_completed: bool = True) -> List[Dict[str, Any]]:
    """Get all print jobs from CUPS queue with real-time status"""
    if not CUPS_AVAILABLE:
        return []
    
    try:
        conn = get_cups_connection()
        all_jobs = []
        
        # Get active jobs
        active_jobs = conn.getJobs(which_jobs='not-completed')
        for job_id, job_info in active_jobs.items():
            job_data = _format_cups_job(job_id, job_info)
            job_data['source'] = 'cups_active'
            all_jobs.append(job_data)
        
        # Get completed jobs if requested
        if include_completed:
            completed_jobs = conn.getJobs(which_jobs='completed', limit=20)
            for job_id, job_info in completed_jobs.items():
                job_data = _format_cups_job(job_id, job_info)
                job_data['source'] = 'cups_completed'
                all_jobs.append(job_data)
        
        # Sort by creation time (newest first)
        all_jobs.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        return all_jobs
        
    except Exception as e:
        logger.error(f"Failed to get all print jobs: {e}")
        return []

def _format_cups_job(job_id: int, job_info: Dict[str, Any]) -> Dict[str, Any]:
    """Format a CUPS job into our standard format"""
    state = job_info.get('job-state', 0)
    state_reasons = job_info.get('job-state-reasons', [])
    
    # Map CUPS job states to our status
    status_map = {
        3: 'pending',      # IPP_JOB_PENDING
        4: 'processing',   # IPP_JOB_PROCESSING
        5: 'stopped',      # IPP_JOB_STOPPED
        6: 'cancelled',    # IPP_JOB_CANCELLED
        7: 'aborted',      # IPP_JOB_ABORTED
        8: 'completed'     # IPP_JOB_COMPLETED
    }
    
    status = status_map.get(state, 'unknown')
    
    # Check for errors
    error_message = None
    if state == 7:  # Aborted
        error_message = job_info.get('job-state-message', 'Job aborted')
    elif state_reasons and any('error' in reason.lower() for reason in state_reasons):
        error_message = ', '.join(state_reasons)
    
    return {
        'job_id': job_id,
        'filename': job_info.get('job-name', 'Unknown'),
        'printer': job_info.get('job-printer-uri', '').split('/')[-1] if job_info.get('job-printer-uri') else 'Unknown',
        'status': status,
        'state': state,
        'state_reasons': state_reasons,
        'error_message': error_message,
        'created_at': job_info.get('time-at-creation', 0),
        'completed_at': job_info.get('time-at-completed', 0),
        'processing_at': job_info.get('time-at-processing', 0),
        'size': job_info.get('job-k-octets', 0),
        'pages': job_info.get('job-media-sheets-completed', 0),
        'priority': job_info.get('job-priority', 50)
    }

def cancel_job(job_id: int) -> Dict[str, Any]:
    """Cancel a specific print job"""
    if not CUPS_AVAILABLE:
        return {'success': False, 'error': 'CUPS not available'}
    
    try:
        conn = get_cups_connection()
        conn.cancelJob(job_id)
        
        # Update database if this job exists there
        update_print_job_status(job_id, 'cancelled', 'Cancelled by user')
        
        logger.info(f"Cancelled print job: {job_id}")
        return {'success': True, 'message': f'Job {job_id} cancelled'}
        
    except Exception as e:
        error_msg = f"Failed to cancel job {job_id}: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def clear_completed_jobs(printer_name: str = None) -> Dict[str, Any]:
    """Clear all completed jobs from the queue"""
    if not CUPS_AVAILABLE:
        return {'success': False, 'error': 'CUPS not available'}
    
    try:
        conn = get_cups_connection()
        
        # Get completed jobs
        completed_jobs = conn.getJobs(which_jobs='completed')
        cleared_count = 0
        
        for job_id, job_info in completed_jobs.items():
            # Filter by printer if specified
            if printer_name:
                job_printer = job_info.get('job-printer-uri', '').split('/')[-1]
                if job_printer != printer_name:
                    continue
            
            try:
                conn.cancelJob(job_id)
                cleared_count += 1
            except:
                pass  # Job might already be cleared
        
        logger.info(f"Cleared {cleared_count} completed print jobs")
        return {
            'success': True, 
            'message': f'Cleared {cleared_count} completed jobs',
            'count': cleared_count
        }
        
    except Exception as e:
        error_msg = f"Failed to clear completed jobs: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def cleanup_old_jobs(max_age_seconds: int = 90) -> Dict[str, Any]:
    """Automatically cleanup old print jobs"""
    if not CUPS_AVAILABLE:
        return {'success': False, 'error': 'CUPS not available'}
    
    import time
    current_time = int(time.time())
    
    try:
        conn = get_cups_connection()
        all_jobs = conn.getJobs(which_jobs='all')
        
        cleaned_jobs = []
        
        for job_id, job_info in all_jobs.items():
            job_state = job_info.get('job-state', 0)
            created_at = job_info.get('time-at-creation', current_time)
            completed_at = job_info.get('time-at-completed', 0)
            
            # Calculate age
            if job_state >= 6:  # Completed, cancelled, or aborted
                reference_time = completed_at if completed_at > 0 else created_at
            else:
                reference_time = created_at
            
            job_age = current_time - reference_time
            
            # Clean up old jobs
            if job_age > max_age_seconds:
                try:
                    job_name = job_info.get('job-name', f'Job {job_id}')
                    conn.cancelJob(job_id)
                    
                    # Update database status
                    if job_state < 6:  # Was still active
                        update_print_job_status(job_id, 'timeout', f'Auto-cancelled after {max_age_seconds}s')
                        logger.warning(f"Auto-cancelled print job {job_id} ({job_name}) after {job_age}s")
                    else:
                        logger.info(f"Auto-cleared completed job {job_id} ({job_name}) after {job_age}s")
                    
                    cleaned_jobs.append({
                        'job_id': job_id,
                        'name': job_name,
                        'age': job_age,
                        'was_active': job_state < 6
                    })
                    
                except Exception as job_error:
                    logger.warning(f"Failed to cleanup job {job_id}: {job_error}")
        
        return {
            'success': True,
            'cleaned_jobs': cleaned_jobs,
            'count': len(cleaned_jobs)
        }
        
    except Exception as e:
        error_msg = f"Failed to cleanup old jobs: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}