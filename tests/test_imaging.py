"""
Tests for image processing functionality
"""
import pytest
import os
import tempfile
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage

from photobooth.imaging import (
    apply_frame_overlay, resize_and_crop, create_thumbnail,
    validate_frame, create_test_print_image, optimize_image_for_print
)

def test_resize_and_crop():
    """Test image resizing and cropping"""
    # Create a test image
    img = Image.new('RGB', (1600, 900), color='blue')
    
    # Test resize to 4:3 aspect ratio
    result = resize_and_crop(img, (800, 600))
    assert result.size == (800, 600)
    
    # Test resize to 16:9 aspect ratio  
    result = resize_and_crop(img, (1920, 1080))
    assert result.size == (1920, 1080)

def test_validate_frame_valid(sample_frame):
    """Test frame validation with valid frame"""
    sample_frame.seek(0)
    file_storage = FileStorage(
        stream=sample_frame,
        filename='frame.png',
        content_type='image/png'
    )
    
    result = validate_frame(file_storage)
    assert result['valid'] is True
    assert 'width' in result
    assert 'height' in result

def test_validate_frame_invalid_format():
    """Test frame validation with invalid format"""
    # Create a JPEG instead of PNG
    img = Image.new('RGB', (1000, 1000), color='red')
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    
    file_storage = FileStorage(
        stream=img_buffer,
        filename='frame.jpg',
        content_type='image/jpeg'
    )
    
    result = validate_frame(file_storage)
    assert result['valid'] is False
    assert 'PNG' in result['error']

def test_validate_frame_too_small():
    """Test frame validation with image too small"""
    # Create a small image
    img = Image.new('RGBA', (500, 500), color=(255, 0, 0, 255))
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    file_storage = FileStorage(
        stream=img_buffer,
        filename='frame.png',
        content_type='image/png'
    )
    
    result = validate_frame(file_storage)
    assert result['valid'] is False
    assert 'at least' in result['error']

def test_apply_frame_overlay(app, sample_image, sample_frame):
    """Test applying frame overlay to photo"""
    with app.app_context():
        # Save the sample image to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            sample_image.seek(0)
            f.write(sample_image.read())
            photo_path = f.name
        
        # Save the sample frame to a temporary file  
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            sample_frame.seek(0)
            f.write(sample_frame.read())
            frame_path = f.name
        
        try:
            # Apply frame overlay
            result_path = apply_frame_overlay(photo_path, frame_path)
            assert result_path == photo_path
            assert os.path.exists(result_path)
            
            # Verify the image is still valid
            with Image.open(result_path) as img:
                assert img.format == 'JPEG'
                # Should be resized to configured dimensions
                assert img.size == (1800, 1200)
        finally:
            if os.path.exists(photo_path):
                os.unlink(photo_path)
            if os.path.exists(frame_path):
                os.unlink(frame_path)

def test_create_test_print_image(app):
    """Test creating test print image"""
    with app.app_context():
        test_image_path = create_test_print_image()
        
        assert os.path.exists(test_image_path)
        
        # Verify the image
        with Image.open(test_image_path) as img:
            assert img.format == 'JPEG'
            assert img.size == (1800, 1200)  # Default photo dimensions
        
        # Clean up
        os.unlink(test_image_path)

def test_optimize_image_for_print(app, sample_image):
    """Test image optimization for printing"""
    with app.app_context():
        # Save sample image to temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            sample_image.seek(0)
            f.write(sample_image.read())
            image_path = f.name
        
        try:
            optimized_path = optimize_image_for_print(image_path)
            assert os.path.exists(optimized_path)
            
            # Should create a new file with _print suffix
            assert '_print.jpg' in optimized_path
            
            # Verify the optimized image
            with Image.open(optimized_path) as img:
                assert img.format == 'JPEG'
            
            # Clean up optimized file
            os.unlink(optimized_path)
        finally:
            if os.path.exists(image_path):
                os.unlink(image_path)