"""
Test configuration and fixtures
"""
import pytest
import tempfile
import os
import sqlite3
from PIL import Image
import io

# Add the parent directory to the path so we can import the app
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from photobooth import create_app
from photobooth.models import init_db

@pytest.fixture
def app():
    """Create and configure a test Flask app"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create temporary directories for photos
    temp_dir = tempfile.mkdtemp()
    photos_dir = os.path.join(temp_dir, 'photos')
    os.makedirs(os.path.join(photos_dir, 'all'))
    os.makedirs(os.path.join(photos_dir, 'printed'))
    os.makedirs(os.path.join(photos_dir, 'thumbnails'))
    
    # Create temporary frame directory
    frame_dir = os.path.join(temp_dir, 'frames')
    os.makedirs(frame_dir)
    frame_path = os.path.join(frame_dir, 'current.png')
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'PHOTOS_DIR': photos_dir,
        'PHOTOS_ALL_DIR': os.path.join(photos_dir, 'all'),
        'PHOTOS_PRINTED_DIR': os.path.join(photos_dir, 'printed'),
        'FRAME_PATH': frame_path,
        'SECRET_KEY': 'test-secret-key',
        'SETTINGS_PASSWORD': 'test123',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
    })
    
    with app.app_context():
        init_db(db_path)
        yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def auth_session(client):
    """Authenticated session for settings"""
    with client.session_transaction() as sess:
        sess['authenticated'] = True
    return client

@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    img = Image.new('RGB', (800, 600), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

@pytest.fixture
def sample_frame():
    """Create a sample PNG frame with transparency"""
    img = Image.new('RGBA', (1800, 1200), color=(255, 255, 255, 0))
    # Add a simple border
    for x in range(50):
        for y in range(1200):
            if y < 100 or y > 1100:  # Top and bottom borders
                img.putpixel((x, y), (255, 0, 0, 255))
        for y in range(100, 1100):
            if x < 10:  # Left border
                img.putpixel((x, y), (255, 0, 0, 255))
    
    for x in range(1750, 1800):
        for y in range(1200):
            if y < 100 or y > 1100:  # Top and bottom borders
                img.putpixel((x, y), (255, 0, 0, 255))
        for y in range(100, 1100):
            if x > 1790:  # Right border
                img.putpixel((x, y), (255, 0, 0, 255))
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer