"""
Booth routes - Main photobooth functionality
"""
import os
import logging
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from .storage import save_photo, delete_photo, get_photos, get_photo_path
from .imaging import apply_frame_overlay, create_thumbnail
from .printing import print_photo
from .audio import speak_countdown

booth_bp = Blueprint('booth', __name__, url_prefix='/booth')

logger = logging.getLogger(__name__)

@booth_bp.route('/')
def booth():
    """Main booth interface"""
    return render_template('booth.html')

@booth_bp.route('/api/capture', methods=['POST'])
def capture_photo():
    """Capture photo from camera"""
    try:
        # Get the uploaded photo blob
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo data received'}), 400
        
        photo_file = request.files['photo']
        if photo_file.filename == '':
            return jsonify({'error': 'No photo selected'}), 400
        
        # Generate unique filename
        photo_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{photo_id}.jpg"
        
        # Save the raw photo
        photo_path = save_photo(photo_file, filename)
        
        # Apply frame overlay if available
        frame_path = current_app.config['FRAME_PATH']
        if os.path.exists(frame_path):
            try:
                photo_path = apply_frame_overlay(photo_path, frame_path)
                logger.info(f"Applied frame overlay to {filename}")
            except Exception as e:
                logger.warning(f"Failed to apply frame overlay: {e}")
        
        # Create thumbnail
        try:
            create_thumbnail(photo_path)
            logger.info(f"Created thumbnail for {filename}")
        except Exception as e:
            logger.warning(f"Failed to create thumbnail: {e}")
        
        # Log the event
        logger.info(f"Photo captured: {filename}")
        
        # Return preview URL
        preview_url = f"/booth/api/preview/{filename}"
        
        return jsonify({
            'success': True,
            'photo_id': photo_id,
            'filename': filename,
            'preview_url': preview_url,
            'timestamp': timestamp
        })
        
    except Exception as e:
        logger.error(f"Error capturing photo: {e}")
        return jsonify({'error': 'Failed to capture photo'}), 500

@booth_bp.route('/api/preview/<filename>')
def preview_photo(filename):
    """Serve photo preview"""
    try:
        photo_path = get_photo_path(filename, 'all')
        if not os.path.exists(photo_path):
            return jsonify({'error': 'Photo not found'}), 404
        
        return send_file(photo_path, mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Error serving preview: {e}")
        return jsonify({'error': 'Failed to load preview'}), 500

@booth_bp.route('/api/print', methods=['POST'])
def print_photo_endpoint():
    """Print photo"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Get photo path
        photo_path = get_photo_path(filename, 'all')
        if not os.path.exists(photo_path):
            return jsonify({'error': 'Photo not found'}), 404
        
        # Print the photo
        print_result = print_photo(photo_path, filename)
        
        if print_result['success']:
            # Copy to printed directory
            from shutil import copy2
            printed_dir = current_app.config['PHOTOS_PRINTED_DIR']
            copy2(photo_path, os.path.join(printed_dir, filename))
            
            logger.info(f"Photo printed: {filename}")
            
            return jsonify({
                'success': True,
                'message': 'Photo sent to printer',
                'job_id': print_result.get('job_id')
            })
        else:
            logger.error(f"Failed to print photo {filename}: {print_result.get('error')}")
            return jsonify({
                'success': False,
                'error': print_result.get('error', 'Print failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error printing photo: {e}")
        return jsonify({'error': 'Failed to print photo'}), 500

@booth_bp.route('/api/retake', methods=['POST'])
def retake_photo():
    """Delete photo and retake"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Delete the photo
        if delete_photo(filename):
            logger.info(f"Photo deleted for retake: {filename}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to delete photo'}), 500
            
    except Exception as e:
        logger.error(f"Error during retake: {e}")
        return jsonify({'error': 'Failed to retake photo'}), 500

@booth_bp.route('/api/countdown', methods=['POST'])
def countdown_tts():
    """Trigger countdown TTS"""
    try:
        data = request.get_json()
        countdown_text = data.get('text', '3, 2, 1, smile!')
        
        # Speak countdown in background
        speak_countdown(countdown_text)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.warning(f"TTS countdown failed: {e}")
        # Don't fail the request if TTS fails
        return jsonify({'success': True})

@booth_bp.route('/api/status')
def booth_status():
    """Get booth status"""
    try:
        # Check printer status
        from .printing import get_printer_status
        printer_status = get_printer_status()
        
        # Check storage
        photos_count = len(get_photos())
        
        return jsonify({
            'success': True,
            'printer': printer_status,
            'photos_count': photos_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting booth status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500