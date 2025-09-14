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
from .models import log_print_job, update_print_job_status, get_setting, get_print_count_status, increment_print_count, log_printer_error, mark_error_announced, resolve_printer_errors, get_printer_error_status
from .imaging import create_test_print_image, optimize_image_for_print

logger = logging.getLogger(__name__)

def is_printing_allowed() -> Dict[str, Any]:
    """Check if printing is allowed based on print count status and printer errors"""
    try:
        # Check print count status
        count_status = get_print_count_status()
        
        # Check printer error status  
        default_printer = get_setting('default_printer', '')
        printer_error_status = get_printer_error_status(default_printer) if default_printer else {'printing_disabled': False}
        
        # Check if printer errors disable printing
        if printer_error_status['printing_disabled']:
            latest_error = printer_error_status.get('latest_error')
            error_msg = latest_error['error_message'] if latest_error else 'Printer has active errors'
            return {
                'allowed': False,
                'reason': f'Printer error: {error_msg}',
                'count_status': count_status,
                'error_status': printer_error_status
            }
        
        # Check ink cartridge status
        if count_status['enabled'] and count_status['is_empty']:
            return {
                'allowed': False,
                'reason': 'Ink cartridge is empty. Please replace the cartridge.',
                'count_status': count_status,
                'error_status': printer_error_status
            }
        
        return {
            'allowed': True,
            'reason': None,
            'count_status': count_status,
            'error_status': printer_error_status
        }
        
    except Exception as e:
        logger.error(f"Failed to check printing allowance: {e}")
        # If there's an error, allow printing to not break functionality
        return {
            'allowed': True,
            'reason': None,
            'count_status': {'enabled': False},
            'error_status': {'printing_disabled': False}
        }

def poll_printer_status_and_announce():
    """Poll printer status and announce errors if found"""
    if not CUPS_AVAILABLE:
        return
    
    try:
        # Get polling settings
        polling_enabled = get_setting('printer_status_polling_enabled', True)
        if not polling_enabled:
            return
        
        default_printer = get_setting('default_printer', '')
        if not default_printer:
            return
        
        # Get current printer status
        current_status = get_printer_status(default_printer)
        if not current_status:
            return
        
        printer_state = current_status.get('state', '')
        if isinstance(printer_state, int):
            # Convert CUPS printer state codes to strings
            state_map = {3: 'idle', 4: 'printing', 5: 'stopped'}
            printer_state = state_map.get(printer_state, str(printer_state))
        else:
            printer_state = str(printer_state).lower()
        
        state_message = current_status.get('state_message', '')
        if isinstance(state_message, str):
            state_message = state_message.strip()
        else:
            state_message = str(state_message)
        
        # Check if printer has errors
        if printer_state in ['stopped', 'error'] or 'error' in str(state_message).lower():
            # Log the error
            error_msg = state_message or f"Printer is in {printer_state} state"
            log_printer_error(default_printer, error_msg, printer_state)
            
            # Check if we should announce this error
            from .audio import should_announce_printer_error, speak_printer_error
            
            # Get the last announcement details for this error
            error_status = get_printer_error_status(default_printer)
            if error_status['has_errors']:
                latest_error = error_status['latest_error']
                last_announced_time = None
                
                if latest_error and latest_error['last_announced']:
                    from datetime import datetime
                    last_announced_time = int(datetime.fromisoformat(latest_error['last_announced'].replace(' ', 'T')).timestamp())
                
                if should_announce_printer_error(error_msg, None, last_announced_time):
                    # Announce the error
                    if speak_printer_error(error_msg, default_printer):
                        mark_error_announced(default_printer, error_msg)
                        logger.info(f"Announced printer error: {error_msg}")
        
        elif printer_state in ['idle', 'printing']:
            # Printer seems to be working, resolve any existing errors
            resolve_printer_errors(default_printer)
            
    except Exception as e:
        logger.error(f"Error polling printer status: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

def start_printer_status_polling(app):
    """Start background printer status polling with app context"""
    try:
        import threading
        import time
        
        def polling_loop():
            while True:
                try:
                    with app.app_context():
                        polling_enabled = get_setting('printer_status_polling_enabled', True)
                        if not polling_enabled:
                            time.sleep(60)  # Check again in 1 minute
                            continue
                        
                        interval = get_setting('printer_status_polling_interval_seconds', 30)
                        poll_printer_status_and_announce()
                        time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error in printer status polling loop: {e}")
                    time.sleep(30)  # Wait 30 seconds before retrying
        
        # Start polling in background thread
        polling_thread = threading.Thread(target=polling_loop, daemon=True)
        polling_thread.start()
        logger.info("Printer status polling started")
        
    except Exception as e:
        logger.error(f"Failed to start printer status polling: {e}")

def get_enhanced_printer_status(printer_name: str = None) -> Dict[str, Any]:
    """Get enhanced printer status including error tracking"""
    try:
        if printer_name is None:
            # Try to get default printer, with fallback to direct DB access
            try:
                printer_name = get_setting('default_printer', '')
            except:
                # Fallback: read directly from database without Flask context
                import sqlite3
                try:
                    conn = sqlite3.connect('/opt/photobooth/data/photobooth.db')
                    cursor = conn.execute('SELECT value FROM settings WHERE key = ?', ('default_printer',))
                    row = cursor.fetchone()
                    printer_name = row[0] if row else ''
                    conn.close()
                except Exception as db_e:
                    logger.warning(f"Could not read printer setting from database: {db_e}")
                    printer_name = ''
        
        if not printer_name:
            return {
                'available': False,
                'ready': False,
                'error': 'No default printer configured',
                'has_errors': False,
                'printing_disabled': False
            }
        
        # Get basic CUPS status
        cups_status = get_printer_status(printer_name)
        
        # Get error status from database
        error_status = get_printer_error_status(printer_name)
        
        # Combine the information
        enhanced_status = {
            'printer_name': printer_name,
            'available': cups_status.get('available', False),
            'name': cups_status.get('name', printer_name),
            'description': cups_status.get('description', printer_name),
            'ready': cups_status.get('ready', False) and not error_status['printing_disabled'],
            'state': cups_status.get('state', 'unknown'),
            'state_message': cups_status.get('state_message', ''),
            'paper_error': cups_status.get('paper_error'),
            'has_errors': error_status['has_errors'],
            'error_count': error_status['error_count'],
            'errors': error_status['errors'],
            'printing_disabled': error_status['printing_disabled'],
            'latest_error': error_status.get('latest_error')
        }
        
        # If printer has errors that disable printing, override ready state
        if error_status['printing_disabled']:
            enhanced_status['ready'] = False
            enhanced_status['error'] = error_status['latest_error']['error_message'] if error_status['latest_error'] else 'Printer has active errors'
        
        return enhanced_status
        
    except Exception as e:
        logger.error(f"Failed to get enhanced printer status: {e}")
        return {
            'available': False,
            'ready': False,
            'error': str(e),
            'has_errors': True,
            'printing_disabled': True
        }

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
        
        # For accepting jobs, we'll assume the printer is accepting if it's in idle state (3)
        # The printer-is-accepting-jobs field isn't always present in CUPS responses.
        printer_state = printer_info.get('printer-state')
        is_accepting = printer_state == 3  # idle state means accepting jobs
        
        ready = printer_state == 3
        
        if 'Incorrect paper loaded' in state_message:
            paper_error = state_message
            ready = False
            if 'CP760' in printer_name or 'SELPHY' in printer_name:
                # Parse the paper type mismatch
                if 'vs' in state_message:
                    parts = state_message.split('vs')
                    if len(parts) == 2:
                        loaded_type = parts[0].split('(')[-1].strip()
                        expected_type = parts[1].split(')')[0].strip()
                        
                        # Canon SELPHY paper type mapping
                        paper_types = {
                            '01': 'KP-36IN (36 sheets, credit card size)',
                            '11': 'KP-108IN (108 sheets, 4x6 inch glossy)', 
                            '22': 'KP-72IN (72 sheets, 2x3 inch)',
                            '33': 'Unknown paper type',
                            '44': 'Large format paper'
                        }
                        
                        loaded_desc = paper_types.get(loaded_type, f'Unknown type {loaded_type}')
                        expected_desc = paper_types.get(expected_type, f'Unknown type {expected_type}')
                        
                        paper_error = f"Paper cartridge mismatch: Loaded {loaded_desc}, but software expects {expected_desc}. "
                        
                        if loaded_type == '01' and expected_type in ['11', '22', '33', '44']:
                            paper_error += "You have KP-36IN (credit card size) loaded, but need KP-108IN (4x6 inch) for photobooth printing. Please replace the paper cartridge."
                        elif loaded_type == '11':
                            paper_error += "You have the correct KP-108IN cartridge loaded. Try resetting the printer."
                        else:
                            paper_error += "Please load the KP-108IN (4x6 inch glossy) paper cartridge for photobooth printing."
                    else:
                        paper_error += " - Please check that the correct Canon paper cartridge is loaded"
                else:
                    paper_error += " - Please check that the correct Canon paper cartridge is loaded"
        
        result = {
            'available': True,
            'name': printer_name,
            'description': printer_info.get('printer-info', printer_name),
            'state': printer_info.get('printer-state', 0),
            'state_message': state_message,
            'paper_error': paper_error,
            'accepting_jobs': is_accepting,
            'ready': ready
        }
        
        logger.info(f"get_printer_status({printer_name}): state={printer_state}, accepting={is_accepting}, ready={ready}")
        return result
        
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
    
    # Check if printing is allowed (ink cartridge not empty)
    print_allowance = is_printing_allowed()
    if not print_allowance['allowed']:
        return {
            'success': False,
            'error': print_allowance['reason'],
            'count_status': print_allowance['count_status']
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
            # Canon SELPHY CP760 specific options for KP-108IN paper
            # Based on research: KP-108IN is 100x148mm (4x6 inch) glossy paper
            options = {
                'PageSize': 'Postcard',  # Should correspond to 4x6 inch
                'media': 'Postcard',     # Alternative media specification
                'ColorModel': 'RGB',
                'StpBorderless': 'True', # Enable borderless printing
                'StpImageType': 'Photo', # Optimize for photo printing
                'Resolution': '300dpi',
                'orientation-requested': '3'  # Portrait
            }
            
            # If we detect a paper mismatch, try alternative settings
            printer_status = get_printer_status(printer_name)
            if printer_status.get('paper_error') and '01 vs' in printer_status.get('state_message', ''):
                logger.warning(f"Paper type 01 detected, but no CUPS setting matches. Using Postcard anyway.")
                # Could try alternative settings here if needed
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
        
        # Increment print count
        try:
            increment_print_count()
            logger.info(f"Print count incremented for job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to increment print count: {e}")
        
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
            if job_data is not None:  # Skip empty/invalid jobs
                job_data['source'] = 'cups_active'
                all_jobs.append(job_data)
        
        # Get completed jobs if requested
        if include_completed:
            completed_jobs = conn.getJobs(which_jobs='completed', limit=20)
            for job_id, job_info in completed_jobs.items():
                job_data = _format_cups_job(job_id, job_info)
                if job_data is not None:  # Skip empty/invalid jobs
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
    
    # Skip jobs with no meaningful data (old cleaned up jobs)
    job_name = job_info.get('job-name', '')
    job_uri = job_info.get('job-printer-uri', '')
    
    if not job_name and not job_uri and state == 0:
        # This is likely an old cleaned up job, return None to skip
        return None
    
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
    
    # If state is 0 and we have job data, it might be completed but state not set
    if state == 0 and job_name:
        status = 'completed'
    
    # Check for errors
    error_message = None
    if state == 7:  # Aborted
        error_message = job_info.get('job-state-message', 'Job aborted')
    elif state_reasons and any('error' in reason.lower() for reason in state_reasons):
        error_message = ', '.join(state_reasons)
    
    # Extract printer name from URI
    printer_name = 'Unknown'
    if job_uri and '/' in job_uri:
        printer_name = job_uri.split('/')[-1]
    
    return {
        'job_id': job_id,
        'filename': job_name or f'Job-{job_id}',
        'printer': printer_name,
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

def reset_printer(printer_name: str = None) -> Dict[str, Any]:
    """Reset/restart a printer to clear error states"""
    if not CUPS_AVAILABLE:
        return {'success': False, 'error': 'CUPS not available'}
    
    if printer_name is None:
        printer_name = get_default_printer()
    
    if not printer_name:
        return {'success': False, 'error': 'No printer configured'}
    
    try:
        conn = get_cups_connection()
        
        # Disable printer, then re-enable to reset state
        conn.disablePrinter(printer_name)
        conn.enablePrinter(printer_name)
        
        # Also make sure it's accepting jobs
        conn.acceptJobs(printer_name)
        
        logger.info(f"Reset printer: {printer_name}")
        return {'success': True, 'message': f'Printer {printer_name} reset successfully'}
        
    except Exception as e:
        error_msg = f"Failed to reset printer {printer_name}: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def purge_printer_queue(printer_name: str = None) -> Dict[str, Any]:
    """Purge all jobs from a specific printer queue"""
    if not CUPS_AVAILABLE:
        return {'success': False, 'error': 'CUPS not available'}
    
    if printer_name is None:
        printer_name = get_default_printer()
    
    if not printer_name:
        return {'success': False, 'error': 'No printer configured'}
    
    try:
        conn = get_cups_connection()
        
        # Get all jobs for this printer
        all_jobs = conn.getJobs(which_jobs='all')
        purged_count = 0
        
        for job_id, job_info in all_jobs.items():
            job_printer = job_info.get('job-printer-uri', '').split('/')[-1]
            if job_printer == printer_name:
                try:
                    conn.cancelJob(job_id)
                    purged_count += 1
                except:
                    pass  # Job might already be gone
        
        logger.info(f"Purged {purged_count} jobs from printer: {printer_name}")
        return {
            'success': True, 
            'message': f'Purged {purged_count} jobs from {printer_name}',
            'count': purged_count
        }
        
    except Exception as e:
        error_msg = f"Failed to purge printer queue: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def restart_cups_service() -> Dict[str, Any]:
    """Restart the CUPS service (requires system permissions)"""
    try:
        import subprocess
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'cups'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("CUPS service restarted successfully")
            return {'success': True, 'message': 'CUPS service restarted successfully'}
        else:
            error_msg = f"Failed to restart CUPS: {result.stderr}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'CUPS restart timed out'}
    except Exception as e:
        error_msg = f"Failed to restart CUPS service: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}