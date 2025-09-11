"""
Tests for configuration functionality
"""
import pytest
import tempfile
import os

from config import Config, DevelopmentConfig, ProductionConfig

def test_config_defaults():
    """Test default configuration values"""
    config = Config()
    
    assert hasattr(config, 'SECRET_KEY')
    assert hasattr(config, 'DATABASE_PATH')
    assert hasattr(config, 'PHOTOS_DIR')
    assert hasattr(config, 'PHOTO_WIDTH')
    assert hasattr(config, 'PHOTO_HEIGHT')
    assert config.PHOTO_WIDTH == 1800
    assert config.PHOTO_HEIGHT == 1200

def test_development_config():
    """Test development configuration"""
    config = DevelopmentConfig()
    assert config.DEBUG is True

def test_production_config():
    """Test production configuration"""
    config = ProductionConfig()
    assert config.DEBUG is False

def test_config_init_app():
    """Test config initialization with app"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Update config paths to use temp directory
        original_photos_all = Config.PHOTOS_ALL_DIR
        original_photos_printed = Config.PHOTOS_PRINTED_DIR
        original_frame_path = Config.FRAME_PATH
        
        Config.PHOTOS_ALL_DIR = os.path.join(tmpdir, 'photos', 'all')
        Config.PHOTOS_PRINTED_DIR = os.path.join(tmpdir, 'photos', 'printed')  
        Config.FRAME_PATH = os.path.join(tmpdir, 'frames', 'current.png')
        
        try:
            # Initialize with mock app
            class MockApp:
                pass
            
            Config.init_app(MockApp())
            
            # Check that directories were created
            assert os.path.exists(Config.PHOTOS_ALL_DIR)
            assert os.path.exists(Config.PHOTOS_PRINTED_DIR)
            assert os.path.exists(os.path.dirname(Config.FRAME_PATH))
            
        finally:
            # Restore original paths
            Config.PHOTOS_ALL_DIR = original_photos_all
            Config.PHOTOS_PRINTED_DIR = original_photos_printed
            Config.FRAME_PATH = original_frame_path