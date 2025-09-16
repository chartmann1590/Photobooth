"""
Immich sync integration for PhotoBooth
Handles uploading photos to Immich server and album management
"""
import logging
import requests
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import mimetypes
from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)

class ImmichSync:
    """Immich sync client for PhotoBooth"""
    
    def __init__(self):
        self._cached_albums = None
        self._cache_time = None
        self._cache_duration = 300  # 5 minutes
    
    def _get_settings(self) -> Dict[str, Any]:
        """Get Immich settings from database"""
        try:
            from .models import get_setting
            
            def get_bool_setting(key, default=False):
                """Helper to convert setting to boolean"""
                value = get_setting(key, str(default).lower())
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'on')
            
            return {
                'enabled': get_bool_setting('immich_enabled', False),
                'server_url': get_setting('immich_server_url', ''),
                'api_key': get_setting('immich_api_key', ''),
                'album_name': get_setting('immich_album_name', 'PhotoBooth'),
                'auto_sync': get_bool_setting('immich_auto_sync', True),
                'sync_on_capture': get_bool_setting('immich_sync_on_capture', True)
            }
        except Exception as e:
            logger.error(f"Failed to get Immich settings: {e}")
            return {
                'enabled': False,
                'server_url': '',
                'api_key': '',
                'album_name': 'PhotoBooth',
                'auto_sync': False,
                'sync_on_capture': False
            }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication"""
        settings = self._get_settings()
        return {
            'x-api-key': settings['api_key'],
            'Content-Type': 'application/json'
        }
    
    def _get_upload_headers(self) -> Dict[str, str]:
        """Get headers for file upload (without Content-Type)"""
        settings = self._get_settings()
        return {
            'x-api-key': settings['api_key']
        }
    
    def _get_base_url(self) -> str:
        """Get formatted base URL"""
        settings = self._get_settings()
        base_url = settings['server_url'].rstrip('/')
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"
        return base_url
    
    def _generate_device_id(self) -> str:
        """Generate consistent device ID for PhotoBooth"""
        # Use a hash of the hostname/MAC address for consistency
        import socket
        hostname = socket.gethostname()
        return hashlib.md5(f"photobooth-{hostname}".encode()).hexdigest()
    
    def _get_photo_metadata(self, photo_path: str) -> Dict[str, Any]:
        """Extract metadata from photo file"""
        try:
            # Get file stats
            stat = os.stat(photo_path)
            file_size = stat.st_size
            created_time = datetime.fromtimestamp(stat.st_ctime)
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to get image dimensions and EXIF data
            try:
                with Image.open(photo_path) as img:
                    width, height = img.size
                    exif = {}
                    
                    # Extract EXIF data if available
                    if hasattr(img, '_getexif') and img._getexif():
                        for tag_id, value in img._getexif().items():
                            tag = TAGS.get(tag_id, tag_id)
                            exif[tag] = value
                    
                    # Get creation time from EXIF if available
                    if 'DateTime' in exif:
                        try:
                            created_time = datetime.strptime(exif['DateTime'], '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            pass
            except Exception as e:
                logger.warning(f"Could not extract image metadata: {e}")
                width = height = None
            
            return {
                'file_size': file_size,
                'width': width,
                'height': height,
                'created_at': created_time,
                'modified_at': modified_time,
                'mime_type': mimetypes.guess_type(photo_path)[0] or 'image/jpeg'
            }
        except Exception as e:
            logger.error(f"Failed to get photo metadata: {e}")
            return {}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Immich server"""
        settings = self._get_settings()
        
        if not settings['enabled']:
            return {
                'success': False,
                'error': 'Immich sync is disabled'
            }
        
        if not settings['server_url'] or not settings['api_key']:
            return {
                'success': False,
                'error': 'Immich not configured - missing server URL or API key'
            }
        
        try:
            base_url = self._get_base_url()
            headers = self._get_headers()
            
            # Test with server ping endpoint (updated for Immich v1.90+)
            # Try the newer endpoint first, fallback to older one
            test_endpoints = [
                ('/api/server/ping', 'pong'),  # Newer Immich versions
                ('/api/server-info/ping', 'res'),  # Older Immich versions  
                ('/api/server-info', 'version')  # Alternative endpoint
            ]
            
            last_error = None
            
            for endpoint, response_key in test_endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        response_data = response.json() if response.content else {}
                        server_info = response_data.get(response_key, 'Connection successful')
                        
                        return {
                            'success': True,
                            'message': f'Connection to Immich server successful (endpoint: {endpoint})',
                            'server_version': str(server_info),
                            'endpoint_used': endpoint
                        }
                except requests.exceptions.RequestException as e:
                    last_error = f"Endpoint {endpoint}: {str(e)}"
                    continue
                
                # If we get a non-200 response, save the error but continue trying
                if response.status_code != 200:
                    last_error = f"Endpoint {endpoint}: HTTP {response.status_code} - {response.text[:200]}"
            
            # If all endpoints failed, return the last error
            return {
                'success': False,
                'error': f'All connection attempts failed. Last error: {last_error}'
            }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Connection failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def get_albums(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get list of albums from Immich server"""
        settings = self._get_settings()
        
        if not settings['enabled'] or not settings['server_url'] or not settings['api_key']:
            return []
        
        # Check cache
        current_time = datetime.now()
        if (not force_refresh and self._cached_albums and self._cache_time and 
            (current_time - self._cache_time).seconds < self._cache_duration):
            return self._cached_albums
        
        try:
            base_url = self._get_base_url()
            headers = self._get_headers()
            
            # Try different album endpoints for API compatibility
            album_endpoints = [
                "/api/albums",      # Newer Immich API v1.90+
                "/api/album"        # Older API versions  
            ]
            
            response = None
            for endpoint in album_endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
                    if response.status_code == 200:
                        break
                except Exception:
                    continue
            
            if response and response.status_code == 200:
                albums = response.json()
                self._cached_albums = albums
                self._cache_time = current_time
                return albums
            else:
                if response:
                    logger.error(f"Failed to get albums: {response.status_code} - {response.text}")
                else:
                    logger.error("Failed to get albums: all API endpoints returned errors")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get albums: {e}")
            return []
    
    def create_album(self, album_name: str, description: str = "") -> Optional[str]:
        """Create a new album and return album ID"""
        settings = self._get_settings()
        
        if not settings['enabled'] or not settings['server_url'] or not settings['api_key']:
            logger.warning("Cannot create album: Immich not properly configured")
            return None
            
        if not album_name or not album_name.strip():
            logger.error("Cannot create album: album name is empty")
            return None
        
        album_name = album_name.strip()
        
        try:
            base_url = self._get_base_url()
            headers = self._get_headers()
            
            data = {
                'albumName': album_name,
                'description': description or f"PhotoBooth album created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            logger.info(f"Creating Immich album '{album_name}'...")
            
            # Try different album creation endpoints
            create_endpoints = [
                "/api/albums",      # Newer Immich API v1.90+
                "/api/album"        # Older API versions  
            ]
            
            response = None
            for endpoint in create_endpoints:
                try:
                    response = requests.post(f"{base_url}{endpoint}", headers=headers, json=data, timeout=10)
                    if response.status_code in [200, 201]:
                        break
                except Exception:
                    continue
            
            if response and response.status_code == 201:
                album_data = response.json()
                album_id = album_data.get('id')
                logger.info(f"Successfully created Immich album '{album_name}' with ID: {album_id}")
                
                # Clear cache to force refresh
                self._cached_albums = None
                self._cache_time = None
                
                return album_id
            elif response and response.status_code == 400:
                # Check if it's a duplicate album name error
                error_text = response.text.lower()
                if 'already exists' in error_text or 'duplicate' in error_text:
                    logger.warning(f"Album '{album_name}' already exists, attempting to find existing album...")
                    # Force refresh albums and try to find it
                    albums = self.get_albums(force_refresh=True)
                    for album in albums:
                        if album.get('albumName') == album_name:
                            album_id = album.get('id')
                            logger.info(f"Found existing album '{album_name}' with ID: {album_id}")
                            return album_id
                    logger.error(f"Album '{album_name}' should exist but could not find it")
                    return None
                else:
                    logger.error(f"Failed to create album '{album_name}': {response.status_code} - {response.text}")
                    return None
            else:
                if response:
                    logger.error(f"Failed to create album '{album_name}': {response.status_code} - {response.text}")
                else:
                    logger.error(f"Failed to create album '{album_name}': all API endpoints returned errors")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create album '{album_name}': {e}")
            return None
    
    def get_or_create_album(self, album_name: str) -> Optional[str]:
        """Get existing album ID or create new album if it doesn't exist"""
        if not album_name or not album_name.strip():
            logger.warning("Empty album name provided, skipping album creation")
            return None
            
        album_name = album_name.strip()
        
        try:
            # Check if album already exists
            albums = self.get_albums()
            
            for album in albums:
                if album.get('albumName') == album_name:
                    album_id = album.get('id')
                    logger.debug(f"Found existing album '{album_name}' with ID: {album_id}")
                    return album_id
            
            # Album doesn't exist, create it
            logger.info(f"Album '{album_name}' not found, creating new album...")
            album_id = self.create_album(album_name)
            
            if album_id:
                logger.info(f"Successfully created album '{album_name}' with ID: {album_id}")
            else:
                logger.error(f"Failed to create album '{album_name}'")
            
            return album_id
            
        except Exception as e:
            logger.error(f"Error in get_or_create_album for '{album_name}': {e}")
            return None
    
    def upload_photo(self, photo_path: str, album_name: Optional[str] = None) -> Dict[str, Any]:
        """Upload a photo to Immich server"""
        settings = self._get_settings()
        
        if not settings['enabled']:
            return {
                'success': False,
                'error': 'Immich sync is disabled'
            }
        
        if not settings['server_url'] or not settings['api_key']:
            return {
                'success': False,
                'error': 'Immich not configured'
            }
        
        if not os.path.exists(photo_path):
            return {
                'success': False,
                'error': f'Photo file not found: {photo_path}'
            }
        
        try:
            base_url = self._get_base_url()
            upload_headers = self._get_upload_headers()
            
            # Get photo metadata
            metadata = self._get_photo_metadata(photo_path)
            filename = os.path.basename(photo_path)
            
            # Generate SHA1 checksum for duplicate detection
            with open(photo_path, 'rb') as f:
                checksum = hashlib.sha1(f.read()).hexdigest()
            
            # Prepare form data for upload
            with open(photo_path, 'rb') as f:
                files = {
                    'assetData': (filename, f, metadata.get('mime_type', 'image/jpeg'))
                }
                
                form_data = {
                    'deviceAssetId': f"photobooth-{filename}-{checksum[:8]}",
                    'deviceId': self._generate_device_id(),
                    'fileCreatedAt': metadata.get('created_at', datetime.now()).isoformat(),
                    'fileModifiedAt': metadata.get('modified_at', datetime.now()).isoformat(),
                    'isFavorite': 'false'
                }
                
                # Add checksum header for duplicate detection
                upload_headers['x-immich-checksum'] = checksum
                
                # Try different upload endpoints for API compatibility
                upload_endpoints = [
                    "/api/assets",           # Newer Immich API v1.90+
                    "/api/asset/upload"      # Older API versions  
                ]
                
                response = None
                for endpoint in upload_endpoints:
                    try:
                        response = requests.post(
                            f"{base_url}{endpoint}",
                            headers=upload_headers,
                            files=files,
                            data=form_data,
                            timeout=30
                        )
                        if response.status_code in [200, 201]:
                            break
                    except Exception as e:
                        logger.debug(f"Upload endpoint {endpoint} failed: {e}")
                        continue
            
            # Handle both successful upload (201) and duplicate (200) responses
            if response and response.status_code in [200, 201]:
                result = response.json()
                asset_id = result.get('id')
                status = result.get('status', 'created')
                
                # Log appropriately based on status
                if status == 'duplicate':
                    logger.info(f"Photo '{filename}' already exists in Immich (duplicate, ID: {asset_id})")
                else:
                    logger.info(f"Uploaded photo '{filename}' to Immich (status: {status}, ID: {asset_id})")
                
                # Add to album if specified and we have an asset_id
                if asset_id and album_name:
                    logger.info(f"Adding photo to album '{album_name}'...")
                    album_id = self.get_or_create_album(album_name)
                    if album_id:
                        success = self.add_to_album(album_id, [asset_id])
                        if success:
                            logger.info(f"Successfully added photo to album '{album_name}'")
                        else:
                            logger.warning(f"Failed to add photo to album '{album_name}', but photo was processed successfully")
                    else:
                        logger.error(f"Could not get or create album '{album_name}', photo processed but not added to album")
                
                return {
                    'success': True,
                    'asset_id': asset_id,
                    'status': status,
                    'message': f'Photo processed successfully (status: {status})'
                }
            else:
                if response:
                    error_msg = f"Upload failed: {response.status_code} - {response.text}"
                else:
                    error_msg = f"Upload failed: all API endpoints returned errors"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Failed to upload photo: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def add_to_album(self, album_id: str, asset_ids: List[str]) -> bool:
        """Add assets to an album"""
        settings = self._get_settings()
        
        if not settings['enabled'] or not settings['server_url'] or not settings['api_key']:
            return False
        
        try:
            base_url = self._get_base_url()
            headers = self._get_headers()
            
            data = {
                'ids': asset_ids
            }
            
            # Try different album assets endpoints
            album_assets_endpoints = [
                f"/api/albums/{album_id}/assets",    # Newer Immich API v1.90+
                f"/api/album/{album_id}/assets"      # Older API versions  
            ]
            
            response = None
            for endpoint in album_assets_endpoints:
                try:
                    response = requests.put(f"{base_url}{endpoint}", headers=headers, json=data, timeout=10)
                    if response.status_code == 200:
                        break
                except Exception:
                    continue
            
            if response and response.status_code == 200:
                logger.info(f"Added {len(asset_ids)} assets to album {album_id}")
                return True
            else:
                if response:
                    logger.error(f"Failed to add assets to album: {response.status_code} - {response.text}")
                else:
                    logger.error("Failed to add assets to album: all API endpoints returned errors")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add assets to album: {e}")
            return False
    
    def sync_photo(self, photo_path: str) -> Dict[str, Any]:
        """Sync a single photo to Immich with album management"""
        settings = self._get_settings()
        
        if not settings['enabled'] or not settings['auto_sync']:
            return {
                'success': False,
                'error': 'Immich sync is disabled or auto-sync is off'
            }
        
        album_name = settings['album_name'] or 'PhotoBooth'
        return self.upload_photo(photo_path, album_name)
    
    def sync_all_photos(self, photos_dir: str) -> Dict[str, Any]:
        """Sync all photos in directory to Immich"""
        settings = self._get_settings()
        
        if not settings['enabled']:
            return {
                'success': False,
                'error': 'Immich sync is disabled'
            }
        
        if not os.path.exists(photos_dir):
            return {
                'success': False,
                'error': f'Photos directory not found: {photos_dir}'
            }
        
        results = {
            'success': True,
            'uploaded': 0,
            'duplicates': 0,
            'errors': 0,
            'details': []
        }
        
        album_name = settings['album_name'] or 'PhotoBooth'
        
        # Get list of photo files
        photo_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        photo_files = []
        
        for filename in os.listdir(photos_dir):
            if any(filename.lower().endswith(ext) for ext in photo_extensions):
                photo_files.append(os.path.join(photos_dir, filename))
        
        if not photo_files:
            return {
                'success': True,
                'message': 'No photos found to sync',
                'uploaded': 0,
                'duplicates': 0,
                'errors': 0
            }
        
        # Upload each photo
        for photo_path in photo_files:
            try:
                result = self.upload_photo(photo_path, album_name)
                
                if result['success']:
                    status = result.get('status', 'created')
                    if status == 'duplicate':
                        results['duplicates'] += 1
                    else:
                        results['uploaded'] += 1
                    
                    results['details'].append({
                        'file': os.path.basename(photo_path),
                        'status': status,
                        'success': True
                    })
                else:
                    results['errors'] += 1
                    results['details'].append({
                        'file': os.path.basename(photo_path),
                        'error': result.get('error', 'Unknown error'),
                        'success': False
                    })
                    
            except Exception as e:
                results['errors'] += 1
                results['details'].append({
                    'file': os.path.basename(photo_path),
                    'error': str(e),
                    'success': False
                })
        
        # Set overall success based on results
        if results['errors'] > 0 and results['uploaded'] == 0:
            results['success'] = False
        
        logger.info(f"Immich sync complete: {results['uploaded']} uploaded, {results['duplicates']} duplicates, {results['errors']} errors")
        
        return results

# Global instance
_immich_sync = None

def get_immich_sync() -> ImmichSync:
    """Get global Immich sync instance"""
    global _immich_sync
    if _immich_sync is None:
        _immich_sync = ImmichSync()
    return _immich_sync

def sync_photo_to_immich(photo_path: str) -> Dict[str, Any]:
    """Convenience function to sync a photo"""
    try:
        sync = get_immich_sync()
        return sync.sync_photo(photo_path)
    except Exception as e:
        logger.error(f"Failed to sync photo to Immich: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def test_immich_connection() -> Dict[str, Any]:
    """Convenience function to test Immich connection"""
    try:
        sync = get_immich_sync()
        return sync.test_connection()
    except Exception as e:
        logger.error(f"Failed to test Immich connection: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_immich_albums() -> List[Dict[str, Any]]:
    """Convenience function to get albums"""
    try:
        sync = get_immich_sync()
        return sync.get_albums()
    except Exception as e:
        logger.error(f"Failed to get Immich albums: {e}")
        return []