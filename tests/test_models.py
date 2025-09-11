"""
Tests for database models and operations
"""
import pytest
import tempfile
import os
from photobooth.models import (
    init_db, get_settings, update_setting, get_setting,
    log_photo, mark_photo_printed, log_print_job,
    update_print_job_status, log_event, get_photo_stats
)

def test_init_db():
    """Test database initialization"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    
    try:
        init_db(db_path)
        assert os.path.exists(db_path)
        
        # Verify tables were created
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_tables = {'settings', 'photos', 'print_jobs', 'events'}
        assert expected_tables.issubset(set(tables))
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_settings_operations(app):
    """Test settings CRUD operations"""
    with app.app_context():
        # Test getting default settings
        settings = get_settings()
        assert 'default_printer' in settings
        assert 'tts_enabled' in settings
        
        # Test updating a setting
        assert update_setting('test_key', 'test_value')
        assert get_setting('test_key') == 'test_value'
        
        # Test boolean conversion
        assert update_setting('bool_key', True)
        assert get_setting('bool_key') is True
        
        assert update_setting('bool_key', False)
        assert get_setting('bool_key') is False
        
        # Test integer conversion
        assert update_setting('int_key', '123')
        assert get_setting('int_key') == 123
        
        # Test default value
        assert get_setting('nonexistent_key', 'default') == 'default'

def test_photo_logging(app):
    """Test photo metadata logging"""
    with app.app_context():
        # Test logging a photo
        assert log_photo('test.jpg', 'original.jpg', 1920, 1080, 1024000)
        
        # Test marking as printed
        assert mark_photo_printed('test.jpg')
        
        # Test photo stats
        stats = get_photo_stats()
        assert stats['total_photos'] == 1
        assert stats['printed_photos'] == 1

def test_print_job_logging(app):
    """Test print job logging"""
    with app.app_context():
        # Test logging print job
        assert log_print_job('test.jpg', 'test_printer', 123, 'submitted')
        
        # Test updating job status
        assert update_print_job_status(123, 'completed')
        assert update_print_job_status(123, 'failed', 'Printer error')

def test_event_logging(app):
    """Test event logging"""
    with app.app_context():
        # Test logging simple event
        assert log_event('photo_taken')
        
        # Test logging event with data
        event_data = {'filename': 'test.jpg', 'user': 'test'}
        assert log_event('photo_printed', event_data)