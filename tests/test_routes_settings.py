"""
Tests for settings routes and admin functionality
"""
import pytest
import json
import os
from io import BytesIO

def test_login_page(client):
    """Test login page loads"""
    response = client.get('/settings/login')
    assert response.status_code == 200
    assert b'Settings Access' in response.data

def test_login_invalid_password(client):
    """Test login with invalid password"""
    response = client.post('/settings/login', 
                          data={'password': 'wrong'})
    assert response.status_code == 200
    assert b'Invalid password' in response.data

def test_login_valid_password(client):
    """Test login with valid password"""
    response = client.post('/settings/login', 
                          data={'password': 'test123'})
    assert response.status_code == 302
    assert '/settings/' in response.location

def test_login_json_valid(client):
    """Test JSON login with valid password"""
    response = client.post('/settings/login',
                          data=json.dumps({'password': 'test123'}),
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True

def test_login_json_invalid(client):
    """Test JSON login with invalid password"""
    response = client.post('/settings/login',
                          data=json.dumps({'password': 'wrong'}),
                          content_type='application/json')
    assert response.status_code == 401

def test_dashboard_requires_auth(client):
    """Test dashboard requires authentication"""
    response = client.get('/settings/')
    assert response.status_code == 302
    assert '/settings/login' in response.location

def test_dashboard_authenticated(auth_session):
    """Test dashboard with authentication"""
    response = auth_session.get('/settings/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_logout(client):
    """Test logout functionality"""
    # Login first
    client.post('/settings/login', data={'password': 'test123'})
    
    # Then logout
    response = client.get('/settings/logout')
    assert response.status_code == 302
    assert '/settings/login' in response.location
    
    # Should no longer be able to access dashboard
    response = client.get('/settings/')
    assert response.status_code == 302

def test_printer_settings_page(auth_session):
    """Test printer settings page"""
    response = auth_session.get('/settings/printer')
    assert response.status_code == 200
    assert b'Printer Configuration' in response.data

def test_set_printer_no_data(auth_session):
    """Test set printer without data"""
    response = auth_session.post('/settings/api/printer/set',
                                data=json.dumps({}),
                                content_type='application/json')
    assert response.status_code == 400

def test_test_printer(auth_session):
    """Test printer test functionality"""
    response = auth_session.post('/settings/api/printer/test',
                                content_type='application/json')
    # May succeed or fail depending on printer availability
    assert response.status_code in [200, 500]

def test_frame_settings_page(auth_session):
    """Test frame settings page"""
    response = auth_session.get('/settings/frame')
    assert response.status_code == 200
    assert b'Frame' in response.data

def test_upload_frame_no_file(auth_session):
    """Test frame upload without file"""
    response = auth_session.post('/settings/api/frame/upload')
    assert response.status_code == 400

def test_upload_frame_success(auth_session, sample_frame):
    """Test successful frame upload"""
    sample_frame.seek(0)
    data = {
        'frame': (sample_frame, 'frame.png')
    }
    
    response = auth_session.post('/settings/api/frame/upload',
                                data=data,
                                content_type='multipart/form-data')
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result['success'] is True

def test_remove_frame(auth_session):
    """Test frame removal"""
    response = auth_session.post('/settings/api/frame/remove',
                                content_type='application/json')
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result['success'] is True

def test_gallery_page(auth_session):
    """Test gallery page"""
    response = auth_session.get('/settings/gallery')
    assert response.status_code == 200
    assert b'Gallery' in response.data

def test_download_photo_not_found(auth_session):
    """Test download non-existent photo"""
    response = auth_session.get('/settings/api/photo/nonexistent.jpg/download')
    assert response.status_code == 404

def test_delete_photo_not_found(auth_session):
    """Test delete non-existent photo"""
    response = auth_session.post('/settings/api/photo/nonexistent.jpg/delete')
    assert response.status_code == 500  # delete_photo returns False

def test_audio_settings_page(auth_session):
    """Test audio settings page"""
    response = auth_session.get('/settings/audio')
    assert response.status_code == 200
    assert b'Audio' in response.data

def test_update_audio_settings(auth_session):
    """Test updating audio settings"""
    data = {
        'tts_enabled': True,
        'tts_voice': 'en+f3',
        'tts_rate': 150
    }
    
    response = auth_session.post('/settings/api/audio/update',
                                data=json.dumps(data),
                                content_type='application/json')
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result['success'] is True

def test_system_settings_page(auth_session):
    """Test system settings page"""
    response = auth_session.get('/settings/system')
    assert response.status_code == 200
    assert b'System' in response.data

def test_restart_system(auth_session):
    """Test system restart endpoint"""
    response = auth_session.post('/settings/api/system/restart',
                                content_type='application/json')
    assert response.status_code == 200
    
    result = json.loads(response.data)
    assert result['success'] is True