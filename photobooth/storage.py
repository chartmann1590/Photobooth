"""
Photo storage and management utilities
"""
import os
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image
from flask import current_app

from .models import log_photo

logger = logging.getLogger(__name__)

def save_photo(photo_file, filename: str) -> str:
    """Save uploaded photo to storage"""
    try:
        # Get photo directory
        photos_dir = current_app.config['PHOTOS_ALL_DIR']
        os.makedirs(photos_dir, exist_ok=True)
        
        # Save the file
        photo_path = os.path.join(photos_dir, filename)
        photo_file.save(photo_path)
        
        # Get image info
        try:
            with Image.open(photo_path) as img:
                width, height = img.size
                file_size = os.path.getsize(photo_path)
                
                # Log to database
                log_photo(filename, photo_file.filename, width, height, file_size)
                
        except Exception as e:
            logger.warning(f"Failed to get image info for {filename}: {e}")
        
        logger.info(f"Photo saved: {filename} ({file_size} bytes)")
        
        # Sync to Immich if enabled
        try:
            from .immich import sync_photo_to_immich
            from .models import get_setting
            
            # Check if sync on capture is enabled
            sync_on_capture = get_setting('immich_sync_on_capture', 'true')
            if sync_on_capture.lower() in ('true', '1', 'yes', 'on'):
                # Sync in background (non-blocking)
                import threading
                
                def sync_in_background():
                    try:
                        result = sync_photo_to_immich(photo_path)
                        if result['success']:
                            logger.info(f"Photo '{filename}' synced to Immich successfully")
                        else:
                            logger.warning(f"Failed to sync photo '{filename}' to Immich: {result.get('error')}")
                    except Exception as e:
                        logger.error(f"Error syncing photo '{filename}' to Immich: {e}")
                
                # Start background sync
                sync_thread = threading.Thread(target=sync_in_background, daemon=True)
                sync_thread.start()
                
        except Exception as e:
            # Don't fail photo save if Immich sync fails
            logger.warning(f"Failed to trigger Immich sync for {filename}: {e}")
        
        return photo_path
        
    except Exception as e:
        logger.error(f"Failed to save photo {filename}: {e}")
        raise

def get_photo_path(filename: str, directory: str = 'all') -> str:
    """Get full path to photo"""
    if directory == 'all':
        photos_dir = current_app.config['PHOTOS_ALL_DIR']
    elif directory == 'printed':
        photos_dir = current_app.config['PHOTOS_PRINTED_DIR']
    else:
        photos_dir = current_app.config['PHOTOS_ALL_DIR']
    
    return os.path.join(photos_dir, filename)

def get_photos(directory: str = 'all') -> List[Dict[str, Any]]:
    """Get list of photos with metadata"""
    try:
        if directory == 'all':
            photos_dir = current_app.config['PHOTOS_ALL_DIR']
        elif directory == 'printed':
            photos_dir = current_app.config['PHOTOS_PRINTED_DIR']
        else:
            photos_dir = current_app.config['PHOTOS_ALL_DIR']
        
        if not os.path.exists(photos_dir):
            return []
        
        photos = []
        
        for filename in os.listdir(photos_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_path = os.path.join(photos_dir, filename)
                
                try:
                    # Get file stats
                    stat = os.stat(photo_path)
                    file_size = stat.st_size
                    created_at = datetime.fromtimestamp(stat.st_ctime)
                    
                    # Get image dimensions
                    width, height = None, None
                    try:
                        with Image.open(photo_path) as img:
                            width, height = img.size
                    except Exception:
                        pass
                    
                    photos.append({
                        'filename': filename,
                        'file_size': file_size,
                        'width': width,
                        'height': height,
                        'created_at': created_at,
                        'thumbnail_url': f'/settings/api/photo/{filename}/thumbnail',
                        'download_url': f'/settings/api/photo/{filename}/download'
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get metadata for {filename}: {e}")
                    continue
        
        # Sort by creation time (newest first)
        photos.sort(key=lambda x: x['created_at'], reverse=True)
        
        return photos
        
    except Exception as e:
        logger.error(f"Failed to get photos from {directory}: {e}")
        return []

def delete_photo(filename: str) -> bool:
    """Delete photo from storage"""
    try:
        # Delete from all directories
        for directory in ['all', 'printed']:
            photo_path = get_photo_path(filename, directory)
            if os.path.exists(photo_path):
                os.remove(photo_path)
                logger.info(f"Deleted photo: {photo_path}")
        
        # Delete thumbnail
        thumbnail_path = get_thumbnail_path(filename)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            logger.info(f"Deleted thumbnail: {thumbnail_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete photo {filename}: {e}")
        return False

def get_thumbnail_path(filename: str) -> str:
    """Get thumbnail path"""
    photos_dir = current_app.config['PHOTOS_ALL_DIR']
    thumbnail_dir = os.path.join(os.path.dirname(photos_dir), 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    # Change extension to jpg for thumbnails
    base_name = os.path.splitext(filename)[0]
    thumbnail_filename = f"{base_name}_thumb.jpg"
    
    return os.path.join(thumbnail_dir, thumbnail_filename)

def create_thumbnail(photo_path: str, size: int = None) -> str:
    """Create thumbnail from photo"""
    try:
        if size is None:
            size = current_app.config.get('THUMBNAIL_SIZE', 300)
        
        filename = os.path.basename(photo_path)
        thumbnail_path = get_thumbnail_path(filename)
        
        # Create thumbnail
        with Image.open(photo_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculate thumbnail size maintaining aspect ratio
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
        
        logger.info(f"Created thumbnail: {thumbnail_path}")
        
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {photo_path}: {e}")
        raise

def get_storage_usage() -> Dict[str, Any]:
    """Get storage usage information"""
    try:
        photos_dir = current_app.config['PHOTOS_DIR']
        
        if not os.path.exists(photos_dir):
            return {
                'total_size': 0,
                'photo_count': 0,
                'all_photos_size': 0,
                'printed_photos_size': 0,
                'thumbnails_size': 0
            }
        
        all_photos_size = _get_directory_size(current_app.config['PHOTOS_ALL_DIR'])
        printed_photos_size = _get_directory_size(current_app.config['PHOTOS_PRINTED_DIR'])
        
        # Get thumbnails size
        thumbnail_dir = os.path.join(photos_dir, 'thumbnails')
        thumbnails_size = _get_directory_size(thumbnail_dir)
        
        total_size = all_photos_size + printed_photos_size + thumbnails_size
        
        # Count photos
        photo_count = len(get_photos('all'))
        
        return {
            'total_size': total_size,
            'photo_count': photo_count,
            'all_photos_size': all_photos_size,
            'printed_photos_size': printed_photos_size,
            'thumbnails_size': thumbnails_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'all_photos_size_mb': round(all_photos_size / (1024 * 1024), 2),
            'printed_photos_size_mb': round(printed_photos_size / (1024 * 1024), 2),
            'thumbnails_size_mb': round(thumbnails_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Failed to get storage usage: {e}")
        return {
            'total_size': 0,
            'photo_count': 0,
            'error': str(e)
        }

def _get_directory_size(directory: str) -> int:
    """Get total size of directory"""
    try:
        if not os.path.exists(directory):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    continue
        
        return total_size
        
    except Exception:
        return 0

def cleanup_old_photos(days: int = 30) -> int:
    """Clean up photos older than specified days"""
    try:
        photos_dir = current_app.config['PHOTOS_ALL_DIR']
        if not os.path.exists(photos_dir):
            return 0
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for filename in os.listdir(photos_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_path = os.path.join(photos_dir, filename)
                
                try:
                    if os.path.getctime(photo_path) < cutoff_time:
                        if delete_photo(filename):
                            deleted_count += 1
                            logger.info(f"Cleaned up old photo: {filename}")
                            
                except Exception as e:
                    logger.warning(f"Failed to clean up {filename}: {e}")
                    continue
        
        logger.info(f"Cleaned up {deleted_count} old photos")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup old photos: {e}")
        return 0

def backup_photos(backup_dir: str) -> bool:
    """Backup all photos to external directory"""
    try:
        photos_dir = current_app.config['PHOTOS_ALL_DIR']
        if not os.path.exists(photos_dir):
            logger.warning("No photos to backup")
            return True
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy all photos
        for filename in os.listdir(photos_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                src_path = os.path.join(photos_dir, filename)
                dst_path = os.path.join(backup_dir, filename)
                
                shutil.copy2(src_path, dst_path)
        
        logger.info(f"Photos backed up to: {backup_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to backup photos: {e}")
        return False