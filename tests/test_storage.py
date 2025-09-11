"""
Tests for photo storage functionality
"""
import pytest
import os
import tempfile
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage

from photobooth.storage import (
    save_photo, get_photo_path, get_photos, delete_photo,
    create_thumbnail, get_storage_usage, cleanup_old_photos
)

def test_save_photo(app, sample_image):
    """Test saving a photo"""
    with app.app_context():
        # Create a FileStorage object from sample image
        sample_image.seek(0)
        file_storage = FileStorage(
            stream=sample_image,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        
        # Save the photo
        photo_path = save_photo(file_storage, 'test_photo.jpg')
        
        assert os.path.exists(photo_path)
        assert photo_path.endswith('test_photo.jpg')
        
        # Verify the image can be opened
        with Image.open(photo_path) as img:
            assert img.size == (800, 600)
            assert img.format == 'JPEG'

def test_get_photo_path(app):
    """Test getting photo paths"""
    with app.app_context():
        path_all = get_photo_path('test.jpg', 'all')
        assert 'all' in path_all
        assert path_all.endswith('test.jpg')
        
        path_printed = get_photo_path('test.jpg', 'printed')
        assert 'printed' in path_printed
        assert path_printed.endswith('test.jpg')

def test_get_photos(app, sample_image):
    """Test getting photo list"""
    with app.app_context():
        # Initially should be empty
        photos = get_photos()
        assert len(photos) == 0
        
        # Add a photo
        sample_image.seek(0)
        file_storage = FileStorage(
            stream=sample_image,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        save_photo(file_storage, 'test_photo.jpg')
        
        # Should now have one photo
        photos = get_photos()
        assert len(photos) == 1
        assert photos[0]['filename'] == 'test_photo.jpg'
        assert 'created_at' in photos[0]
        assert 'file_size' in photos[0]

def test_create_thumbnail(app, sample_image):
    """Test thumbnail creation"""
    with app.app_context():
        # Save a photo first
        sample_image.seek(0)
        file_storage = FileStorage(
            stream=sample_image,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        photo_path = save_photo(file_storage, 'test_photo.jpg')
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(photo_path)
        
        assert os.path.exists(thumbnail_path)
        
        # Verify thumbnail size
        with Image.open(thumbnail_path) as img:
            assert max(img.size) <= 300  # Default thumbnail size

def test_delete_photo(app, sample_image):
    """Test photo deletion"""
    with app.app_context():
        # Save a photo first
        sample_image.seek(0)
        file_storage = FileStorage(
            stream=sample_image,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        photo_path = save_photo(file_storage, 'test_photo.jpg')
        create_thumbnail(photo_path)
        
        assert os.path.exists(photo_path)
        
        # Delete the photo
        assert delete_photo('test_photo.jpg')
        assert not os.path.exists(photo_path)

def test_get_storage_usage(app, sample_image):
    """Test storage usage calculation"""
    with app.app_context():
        # Initially should be minimal
        usage = get_storage_usage()
        assert 'total_size' in usage
        assert 'photo_count' in usage
        initial_count = usage['photo_count']
        
        # Add a photo
        sample_image.seek(0)
        file_storage = FileStorage(
            stream=sample_image,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        save_photo(file_storage, 'test_photo.jpg')
        
        # Usage should increase
        usage = get_storage_usage()
        assert usage['photo_count'] == initial_count + 1
        assert usage['total_size'] > 0

def test_cleanup_old_photos(app, sample_image):
    """Test cleanup of old photos"""
    with app.app_context():
        # Save a photo
        sample_image.seek(0)
        file_storage = FileStorage(
            stream=sample_image,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        save_photo(file_storage, 'test_photo.jpg')
        
        # Cleanup should not delete recent photos
        deleted_count = cleanup_old_photos(days=1)
        assert deleted_count == 0
        
        photos = get_photos()
        assert len(photos) == 1