"""
Settings routes - Admin interface
"""
import os
import logging
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app, send_file, flash
from werkzeug.utils import secure_filename

from .storage import get_photos, delete_photo, get_storage_usage, get_photo_path
from .printing import get_printers, test_print, set_default_printer, get_printer_status, auto_configure_usb_printer, get_print_jobs, get_all_print_jobs, cancel_job, clear_completed_jobs, cleanup_old_jobs
from .models import get_settings, update_setting, get_print_job_logs
from .imaging import validate_frame

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

logger = logging.getLogger(__name__)

def auth_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('settings.login'))
        return f(*args, **kwargs)
    return decorated_function

@settings_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Settings login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        password = data.get('password', '')
        
        if password == current_app.config['SETTINGS_PASSWORD']:
            session['authenticated'] = True
            session['login_time'] = datetime.now().isoformat()
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': '/settings/'})
            else:
                return redirect(url_for('settings.dashboard'))
        else:
            logger.warning("Failed login attempt")
            error = 'Invalid password'
            
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 401
            else:
                return render_template('settings/login.html', error=error)
    
    return render_template('settings/login.html')

@settings_bp.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('settings.login'))

@settings_bp.route('/')
@auth_required
def dashboard():
    """Main settings dashboard"""
    try:
        # Get system info
        storage_info = get_storage_usage()
        photos = get_photos()
        printer_status = get_printer_status()
        
        return render_template('settings/dashboard.html',
                             storage_info=storage_info,
                             photos_count=len(photos),
                             printer_status=printer_status)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('settings/dashboard.html', error=str(e))

@settings_bp.route('/printer')
@auth_required
def printer_settings():
    """Printer configuration"""
    try:
        printers = get_printers()
        current_printer = get_settings().get('default_printer', '')
        printer_status = get_printer_status()
        
        return render_template('settings/printer.html',
                             printers=printers,
                             current_printer=current_printer,
                             printer_status=printer_status)
        
    except Exception as e:
        logger.error(f"Error loading printer settings: {e}")
        return render_template('settings/printer.html', error=str(e))

@settings_bp.route('/api/printer/set', methods=['POST'])
@auth_required
def set_printer():
    """Set default printer"""
    try:
        data = request.get_json()
        printer_name = data.get('printer')
        
        if not printer_name:
            return jsonify({'error': 'No printer specified'}), 400
        
        # Update setting
        update_setting('default_printer', printer_name)
        set_default_printer(printer_name)
        
        logger.info(f"Default printer set to: {printer_name}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error setting printer: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/printer/test', methods=['POST'])
@auth_required
def test_printer():
    """Test print"""
    try:
        result = test_print()
        
        if result['success']:
            logger.info("Test print successful")
            return jsonify({'success': True, 'message': 'Test page sent to printer'})
        else:
            logger.error(f"Test print failed: {result.get('error')}")
            return jsonify({'error': result.get('error', 'Test print failed')}), 500
            
    except Exception as e:
        logger.error(f"Error during test print: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/printer/configure', methods=['POST'])
@auth_required
def configure_printer():
    """Auto-configure a USB printer"""
    try:
        data = request.get_json()
        device_uri = data.get('device_uri')
        make_model = data.get('make_model')
        printer_name = data.get('printer_name')
        
        if not device_uri or not make_model:
            return jsonify({'success': False, 'error': 'Missing device_uri or make_model'}), 400
        
        # Auto-configure the printer
        result = auto_configure_usb_printer(device_uri, make_model, printer_name)
        
        if result['success']:
            # Set as default printer if no default is set
            current_default = get_settings().get('default_printer', '')
            if not current_default:
                update_setting('default_printer', result['printer_name'])
                set_default_printer(result['printer_name'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error configuring printer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_bp.route('/api/printer/log', methods=['GET'])
@auth_required
def printer_log():
    """Get real-time print job log from CUPS"""
    try:
        # Automatically cleanup old jobs (90 seconds)
        cleanup_result = cleanup_old_jobs(90)
        if not cleanup_result['success']:
            logger.warning(f"Cleanup failed: {cleanup_result.get('error')}")
        elif cleanup_result.get('count', 0) > 0:
            logger.info(f"Auto-cleaned {cleanup_result['count']} old print jobs")
        
        # Get all jobs from CUPS with real-time status
        all_jobs = get_all_print_jobs(include_completed=True)
        
        # Also get database jobs for historical data
        db_jobs = get_print_job_logs(10)
        
        # Merge with database jobs, prioritizing CUPS data for active jobs
        cups_job_ids = {job['job_id'] for job in all_jobs if job.get('job_id')}
        
        for db_job in db_jobs:
            if db_job['job_id'] not in cups_job_ids:
                # Add historical database job not found in CUPS
                all_jobs.append({
                    'job_id': db_job['job_id'],
                    'filename': db_job['filename'],
                    'printer': db_job['printer'],
                    'status': db_job['status'],
                    'error_message': db_job['error_message'],
                    'created_at': db_job['created_at'],
                    'completed_at': db_job['completed_at'],
                    'source': 'database_historical'
                })
        
        # Sort by creation time (most recent first)
        all_jobs.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        # Limit to 25 most recent
        all_jobs = all_jobs[:25]
        
        return jsonify({
            'success': True,
            'jobs': all_jobs,
            'total': len(all_jobs),
            'cleanup': {
                'success': cleanup_result['success'],
                'cleaned_count': cleanup_result.get('count', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting print log: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'jobs': []
        }), 500

@settings_bp.route('/api/printer/cancel/<int:job_id>', methods=['POST'])
@auth_required
def cancel_print_job(job_id):
    """Cancel a specific print job"""
    try:
        result = cancel_job(job_id)
        
        if result['success']:
            logger.info(f"User cancelled print job {job_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/printer/clear', methods=['POST'])
@auth_required
def clear_print_jobs():
    """Clear all completed print jobs"""
    try:
        data = request.get_json() or {}
        printer_name = data.get('printer_name')
        
        result = clear_completed_jobs(printer_name)
        
        if result['success']:
            logger.info(f"User cleared {result['count']} completed jobs")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error clearing jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/printer/cleanup', methods=['POST'])
@auth_required
def manual_cleanup():
    """Manually trigger job cleanup"""
    try:
        data = request.get_json() or {}
        max_age = data.get('max_age_seconds', 90)
        
        result = cleanup_old_jobs(max_age)
        
        if result['success']:
            logger.info(f"Manual cleanup: {result['count']} jobs cleaned")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in manual cleanup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/frame')
@auth_required
def frame_settings():
    """Frame overlay configuration"""
    try:
        frame_path = current_app.config['FRAME_PATH']
        has_frame = os.path.exists(frame_path)
        timestamp = int(datetime.now().timestamp())
        
        return render_template('settings/frame.html', has_frame=has_frame, timestamp=timestamp)
        
    except Exception as e:
        logger.error(f"Error loading frame settings: {e}")
        return render_template('settings/frame.html', error=str(e))

@settings_bp.route('/api/frame/upload', methods=['POST'])
@auth_required
def upload_frame():
    """Upload frame overlay"""
    try:
        if 'frame' not in request.files:
            return jsonify({'error': 'No frame file provided'}), 400
        
        frame_file = request.files['frame']
        if frame_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate frame
        validation_result = validate_frame(frame_file)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
        
        # Reset file pointer after validation
        frame_file.seek(0)
        
        # Save frame
        frame_path = current_app.config['FRAME_PATH']
        os.makedirs(os.path.dirname(frame_path), exist_ok=True)
        frame_file.save(frame_path)
        
        logger.info("Frame overlay uploaded successfully")
        
        return jsonify({'success': True, 'message': 'Frame uploaded successfully'})
        
    except Exception as e:
        logger.error(f"Error uploading frame: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/frame/remove', methods=['POST'])
@auth_required
def remove_frame():
    """Remove frame overlay"""
    try:
        frame_path = current_app.config['FRAME_PATH']
        if os.path.exists(frame_path):
            os.remove(frame_path)
            logger.info("Frame overlay removed")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error removing frame: {e}")
        return jsonify({'error': str(e)}), 500

# Frame API route removed - using direct static file access

@settings_bp.route('/gallery')
@auth_required
def gallery():
    """Photo gallery management"""
    try:
        photos = get_photos()
        
        return render_template('settings/gallery.html', photos=photos)
        
    except Exception as e:
        logger.error(f"Error loading gallery: {e}")
        return render_template('settings/gallery.html', error=str(e))

@settings_bp.route('/api/photo/<filename>/download')
@auth_required
def download_photo(filename):
    """Download photo"""
    try:
        photo_path = get_photo_path(filename, 'all')
        if not os.path.exists(photo_path):
            return jsonify({'error': 'Photo not found'}), 404
        
        return send_file(photo_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error downloading photo: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/photo/<filename>/delete', methods=['POST'])
@auth_required
def delete_photo_endpoint(filename):
    """Delete photo"""
    try:
        if delete_photo(filename):
            logger.info(f"Photo deleted: {filename}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to delete photo'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting photo: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/audio', methods=['GET', 'POST'])
@auth_required
def audio_settings():
    """Audio/TTS configuration"""
    try:
        if request.method == 'POST':
            # Handle form submission
            try:
                # Get form data
                tts_enabled = request.form.get('tts_enabled') == 'true'
                tts_voice = request.form.get('tts_voice', 'en+f3')
                tts_rate = int(request.form.get('tts_rate', 150))
                
                # Get custom messages
                countdown_message = request.form.get('countdown_message', '')
                capture_message = request.form.get('capture_message', '')
                print_message = request.form.get('print_message', '')
                welcome_message = request.form.get('welcome_message', '')
                
                # Update settings
                update_setting('tts_enabled', tts_enabled)
                update_setting('tts_voice', tts_voice)
                update_setting('tts_rate', tts_rate)
                
                # Update custom messages if provided
                if countdown_message:
                    update_setting('countdown_message', countdown_message)
                if capture_message:
                    update_setting('capture_message', capture_message)
                if print_message:
                    update_setting('print_message', print_message)
                if welcome_message:
                    update_setting('welcome_message', welcome_message)
                
                flash('Audio settings saved successfully!', 'success')
                
            except Exception as e:
                logger.error(f"Error saving audio settings: {e}")
                flash(f'Error saving settings: {str(e)}', 'error')
        
        # Load current settings
        settings = get_settings()
        
        return render_template('settings/audio.html',
                             tts_enabled=settings.get('tts_enabled', True),
                             tts_voice=settings.get('tts_voice', 'en+f3'),
                             tts_rate=settings.get('tts_rate', 150),
                             countdown_message=settings.get('countdown_message', ''),
                             capture_message=settings.get('capture_message', ''),
                             print_message=settings.get('print_message', ''),
                             welcome_message=settings.get('welcome_message', ''))
        
    except Exception as e:
        logger.error(f"Error loading audio settings: {e}")
        return render_template('settings/audio.html', error=str(e))

@settings_bp.route('/api/audio/update', methods=['POST'])
@auth_required
def update_audio():
    """Update audio settings"""
    try:
        data = request.get_json()
        
        # Update settings
        if 'tts_enabled' in data:
            update_setting('tts_enabled', data['tts_enabled'])
        if 'tts_voice' in data:
            update_setting('tts_voice', data['tts_voice'])
        if 'tts_rate' in data:
            update_setting('tts_rate', data['tts_rate'])
        
        logger.info("Audio settings updated")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating audio settings: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/system')
@auth_required
def system_settings():
    """System information and controls"""
    try:
        # Get app version (if available)
        version = "1.0.0"  # Could read from version file
        
        # Get storage info
        storage_info = get_storage_usage()
        
        return render_template('settings/system.html',
                             version=version,
                             storage_info=storage_info)
        
    except Exception as e:
        logger.error(f"Error loading system settings: {e}")
        return render_template('settings/system.html', error=str(e))

@settings_bp.route('/api/system/restart', methods=['POST'])
@auth_required
def restart_system():
    """Restart application services"""
    try:
        # This would typically restart the systemd service
        # For now, just log the action
        logger.warning("System restart requested by admin")
        
        return jsonify({
            'success': True,
            'message': 'Restart command sent. Please wait a moment before reconnecting.'
        })
        
    except Exception as e:
        logger.error(f"Error restarting system: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/system/health', methods=['GET'])
@auth_required
def system_health():
    """Get system health status"""
    try:
        import subprocess
        import psutil
        
        # Check if services are running
        services_running = True
        try:
            result = subprocess.run(['systemctl', 'is-active', 'photobooth'], 
                                  capture_output=True, text=True, timeout=5)
            services_running = result.returncode == 0
        except:
            services_running = False
        
        # Check storage
        try:
            disk_usage = psutil.disk_usage('/opt/photobooth')
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            storage_status = f"{free_gb:.1f}GB free of {total_gb:.1f}GB ({usage_percent:.1f}% used)"
        except:
            storage_status = "Unknown"
        
        return jsonify({
            'success': True,
            'status': 'Healthy' if services_running else 'Warning',
            'services_running': services_running,
            'storage_status': storage_status,
            'network_status': 'Connected'
        })
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/system/clear-cache', methods=['POST'])
@auth_required
def clear_cache():
    """Clear thumbnail cache"""
    try:
        import shutil
        
        cache_path = os.path.join(current_app.config['PHOTO_DIR'], 'thumbnails')
        space_freed = 0
        
        if os.path.exists(cache_path):
            # Calculate space before deletion
            for root, dirs, files in os.walk(cache_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        space_freed += os.path.getsize(file_path)
                    except:
                        pass
            
            # Clear cache
            shutil.rmtree(cache_path, ignore_errors=True)
            os.makedirs(cache_path, exist_ok=True)
        
        space_freed_mb = space_freed / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully',
            'space_freed': f"{space_freed_mb:.1f}MB"
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/system/network-info', methods=['GET'])
@auth_required
def network_info():
    """Get network information"""
    try:
        import socket
        import subprocess
        
        # Get local IP - try hostname command first
        local_ip = "Unknown"
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                local_ip = result.stdout.strip().split()[0]
        except:
            # Fallback to socket method
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                pass
        
        # Get WiFi SSID - check if we're running an access point
        ssid = "Unknown"
        wifi_mode = "Unknown"
        try:
            # First check if we're running as an access point
            result = subprocess.run(['systemctl', 'is-active', 'hostapd'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                # We're running hostapd, get SSID from config
                with open('/etc/hostapd/hostapd.conf', 'r') as f:
                    for line in f:
                        if line.startswith('ssid='):
                            ssid = line.split('=', 1)[1].strip()
                            wifi_mode = "Access Point"
                            break
            else:
                # Try to get connected WiFi SSID
                result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and result.stdout.strip():
                    ssid = result.stdout.strip()
                    wifi_mode = "Client"
        except Exception as e:
            logger.debug(f"Error getting WiFi info: {e}")
        
        # Count connected devices (from DHCP leases or ARP table)
        connected_devices = "Unknown"
        try:
            # Try to get DHCP leases first (for access point mode)
            lease_count = 0
            dhcp_lease_files = ['/var/lib/dhcp/dhcpd.leases', '/var/lib/dhcpcd5/dhcpcd.leases']
            for lease_file in dhcp_lease_files:
                try:
                    if os.path.exists(lease_file):
                        result = subprocess.run(['grep', '-c', 'lease', lease_file], 
                                              capture_output=True, text=True, timeout=3)
                        if result.returncode == 0:
                            lease_count = int(result.stdout.strip())
                            break
                except:
                    continue
            
            if lease_count > 0:
                connected_devices = str(lease_count)
            else:
                # Fallback to ARP table
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    device_count = len([line for line in result.stdout.split('\n') if '(' in line and 'incomplete' not in line])
                    connected_devices = str(device_count)
        except Exception as e:
            logger.debug(f"Error counting devices: {e}")
        
        return jsonify({
            'success': True,
            'ip': local_ip,
            'ssid': ssid,
            'wifi_mode': wifi_mode,
            'connected_devices': connected_devices
        })
        
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/system/export', methods=['POST'])
@auth_required
def export_settings():
    """Export system settings"""
    try:
        import json
        import tempfile
        
        # Get all settings from database
        settings = get_settings()
        
        # Create export data
        export_data = {
            'version': '1.0.0',
            'exported_at': datetime.utcnow().isoformat(),
            'settings': settings
        }
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(export_data, temp_file, indent=2)
        temp_file.close()
        
        return send_file(temp_file.name, 
                        as_attachment=True, 
                        download_name=f'photobooth-settings-{datetime.now().strftime("%Y%m%d")}.json',
                        mimetype='application/json')
        
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/system/import', methods=['POST'])
@auth_required
def import_settings():
    """Import system settings"""
    try:
        import json
        
        if 'settings' not in request.files:
            return jsonify({'error': 'No settings file provided'}), 400
        
        settings_file = request.files['settings']
        if settings_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read and parse JSON
        try:
            settings_data = json.load(settings_file.stream)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON file'}), 400
        
        if 'settings' not in settings_data:
            return jsonify({'error': 'Invalid settings file format'}), 400
        
        # Import settings
        settings = settings_data['settings']
        for key, value in settings.items():
            update_setting(key, value)
        
        logger.info(f"Settings imported successfully: {len(settings)} settings")
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {len(settings)} settings'
        })
        
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        return jsonify({'error': str(e)}), 500

# Audio API routes
@settings_bp.route('/api/audio/test', methods=['POST'])
@auth_required
def test_audio():
    """Test TTS with custom text and settings"""
    try:
        from .audio import speak_text
        
        data = request.get_json() or {}
        text = data.get('text', 'This is a test of the text-to-speech system')
        voice = data.get('voice', 'en+f3')
        rate = data.get('rate', 150)
        
        # Test the TTS
        success = speak_text(text, voice=voice, rate=rate)
        
        return jsonify({
            'success': success,
            'message': 'TTS test completed' if success else 'TTS test failed'
        })
        
    except Exception as e:
        logger.error(f"Error testing audio: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/audio/test-messages', methods=['POST'])
@auth_required
def test_audio_messages():
    """Test all custom messages"""
    try:
        from .audio import speak_text
        import time
        
        data = request.get_json() or {}
        messages = data.get('messages', {})
        voice = data.get('voice', 'en+f3')
        rate = data.get('rate', 150)
        
        # Test each message with a delay between them
        for msg_type, text in messages.items():
            if text.strip():
                speak_text(f"{msg_type}: {text}", voice=voice, rate=rate)
                time.sleep(1)  # Brief pause between messages
        
        return jsonify({
            'success': True,
            'message': 'All messages tested successfully'
        })
        
    except Exception as e:
        logger.error(f"Error testing audio messages: {e}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/audio/status', methods=['GET'])
@auth_required 
def audio_status():
    """Get audio system status"""
    try:
        from .audio import get_tts_status, get_available_voices
        
        # Check if TTS engines are available
        tts_status = get_tts_status()
        voices = get_available_voices()
        current_voice = get_settings().get('tts_voice', 'en+f3')
        
        return jsonify({
            'success': True,
            'engines': {
                'available': tts_status.get('available', False),
                'engine': tts_status.get('engine', 'Unknown')
            },
            'voices': voices,
            'current_voice': current_voice
        })
        
    except Exception as e:
        logger.error(f"Error getting audio status: {e}")
        return jsonify({
            'success': True,  # Don't fail the page load
            'engines': {'available': False},
            'error': str(e)
        })

@settings_bp.route('/api/audio/voices', methods=['GET'])
@auth_required
def get_voices():
    """Get available voices for the voice selection dropdown"""
    try:
        from .audio import get_available_voices
        
        voices = get_available_voices()
        
        return jsonify({
            'success': True,
            'voices': voices
        })
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'voices': []
        })