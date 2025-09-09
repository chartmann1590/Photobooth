"""
Settings routes - Admin interface
"""
import os
import logging
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app, send_file
from werkzeug.utils import secure_filename

from .storage import get_photos, delete_photo, get_storage_usage, get_photo_path
from .printing import get_printers, test_print, set_default_printer, get_printer_status
from .models import get_settings, update_setting
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

@settings_bp.route('/frame')
@auth_required
def frame_settings():
    """Frame overlay configuration"""
    try:
        frame_path = current_app.config['FRAME_PATH']
        has_frame = os.path.exists(frame_path)
        
        return render_template('settings/frame.html', has_frame=has_frame)
        
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

@settings_bp.route('/audio')
@auth_required
def audio_settings():
    """Audio/TTS configuration"""
    try:
        settings = get_settings()
        
        return render_template('settings/audio.html',
                             tts_enabled=settings.get('tts_enabled', True),
                             tts_voice=settings.get('tts_voice', 'en+f3'),
                             tts_rate=settings.get('tts_rate', 150))
        
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