"""
Configuration settings for the Photobooth application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'wedding-photobooth-secret-change-this-in-production')
    SETTINGS_PASSWORD = os.getenv('SETTINGS_PASSWORD', 'admin123')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', '/opt/photobooth/data/photobooth.db')
    
    # Photo storage
    PHOTOS_DIR = os.getenv('PHOTOS_DIR', '/opt/photobooth/data/photos')
    PHOTOS_ALL_DIR = os.path.join(PHOTOS_DIR, 'all')
    PHOTOS_PRINTED_DIR = os.path.join(PHOTOS_DIR, 'printed')
    THUMBNAILS_DIR = os.path.join(PHOTOS_DIR, 'thumbnails')
    
    # Image settings
    PHOTO_WIDTH = int(os.getenv('PHOTO_WIDTH', 1800))
    PHOTO_HEIGHT = int(os.getenv('PHOTO_HEIGHT', 1200))
    PHOTO_QUALITY = int(os.getenv('PHOTO_QUALITY', 85))
    THUMBNAIL_SIZE = int(os.getenv('THUMBNAIL_SIZE', 300))
    
    # Frame overlay settings  
    FRAMES_DIR = os.getenv('FRAMES_DIR', '/opt/photobooth/photobooth/static/frames')
    FRAME_PATH = os.path.join(FRAMES_DIR, 'current.png')
    
    # Printer settings
    DEFAULT_PRINTER = os.getenv('DEFAULT_PRINTER', '')
    PRINT_PAPER_SIZE = os.getenv('PRINT_PAPER_SIZE', '4x6')
    PRINT_DPI = int(os.getenv('PRINT_DPI', 300))
    
    # Audio settings
    TTS_ENABLED = os.getenv('TTS_ENABLED', 'true').lower() == 'true'
    TTS_VOICE = os.getenv('TTS_VOICE', 'en+f3')
    TTS_RATE = int(os.getenv('TTS_RATE', 150))
    
    # Network settings
    AP_SSID = os.getenv('AP_SSID', 'PhotoBooth')
    AP_PASSWORD = os.getenv('AP_PASSWORD', 'photobooth123')
    AP_IP = os.getenv('AP_IP', '192.168.50.1')
    AP_SUBNET = os.getenv('AP_SUBNET', '192.168.50.0/24')
    
    # Frame overlay
    FRAME_UPLOAD_PATH = '/opt/photobooth/photobooth/static/frames/'
    
    # Upload limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    @staticmethod
    def init_app(app):
        """Initialize app with config"""
        # Create directories
        os.makedirs(Config.PHOTOS_ALL_DIR, exist_ok=True)
        os.makedirs(Config.PHOTOS_PRINTED_DIR, exist_ok=True)
        os.makedirs(Config.THUMBNAILS_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(Config.FRAME_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}