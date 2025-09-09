"""
Tests for booth routes and functionality
"""
import pytest
import json
import os
from io import BytesIO
from werkzeug.datastructures import FileStorage

def test_booth_page(client):
    """Test main booth page loads"""
    response = client.get('/booth/')
    assert response.status_code == 200
    assert b'PhotoBooth' in response.data
    assert b'Start Photo Session' in response.data

def test_root_redirect(client):
    """Test root URL redirects to booth"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/booth/' in response.location

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/healthz')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['app'] == 'photobooth'

def test_capture_photo_no_file(client):
    """Test photo capture without file"""
    response = client.post('/booth/api/capture')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data

def test_capture_photo_success(client, sample_image, app):
    """Test successful photo capture"""
    with app.app_context():
        sample_image.seek(0)
        data = {
            'photo': (sample_image, 'test.jpg')
        }
        
        response = client.post('/booth/api/capture', 
                             data=data, 
                             content_type='multipart/form-data')
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'filename' in result
        assert 'preview_url' in result

def test_preview_photo_not_found(client):
    """Test preview for non-existent photo"""
    response = client.get('/booth/api/preview/nonexistent.jpg')
    assert response.status_code == 404

def test_preview_photo_success(client, sample_image, app):
    """Test successful photo preview"""
    with app.app_context():
        # First capture a photo
        sample_image.seek(0)
        data = {'photo': (sample_image, 'test.jpg')}
        
        capture_response = client.post('/booth/api/capture', 
                                     data=data, 
                                     content_type='multipart/form-data')
        
        capture_data = json.loads(capture_response.data)
        filename = capture_data['filename']
        
        # Then preview it
        response = client.get(f'/booth/api/preview/{filename}')
        assert response.status_code == 200
        assert response.content_type.startswith('image/')

def test_print_photo_no_filename(client):
    """Test print without filename"""
    response = client.post('/booth/api/print',
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 400

def test_print_photo_not_found(client):
    """Test print non-existent photo"""
    data = {'filename': 'nonexistent.jpg'}
    response = client.post('/booth/api/print',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 404

def test_retake_photo_no_filename(client):
    """Test retake without filename"""
    response = client.post('/booth/api/retake',
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 400

def test_countdown_tts(client):
    """Test countdown TTS endpoint"""
    data = {'text': '3, 2, 1, smile!'}
    response = client.post('/booth/api/countdown',
                          data=json.dumps(data),
                          content_type='application/json')
    
    # Should always succeed even if TTS fails
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result['success'] is True

def test_booth_status(client, app):
    """Test booth status endpoint"""
    with app.app_context():
        response = client.get('/booth/api/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'photos_count' in data
        assert 'timestamp' in data