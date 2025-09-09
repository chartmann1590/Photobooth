"""
Tests for printing functionality (mocked since CUPS may not be available)
"""
import pytest
from unittest.mock import patch, MagicMock

from photobooth.printing import (
    get_printers, get_default_printer, get_printer_status,
    print_photo, test_print, validate_print_settings
)

@patch('photobooth.printing.CUPS_AVAILABLE', True)
@patch('photobooth.printing.cups')
def test_get_printers_success(mock_cups):
    """Test getting printer list successfully"""
    # Mock CUPS connection and printer data
    mock_conn = MagicMock()
    mock_conn.getPrinters.return_value = {
        'HP_Printer': {
            'printer-info': 'HP LaserJet',
            'printer-location': 'Office',
            'printer-state': 3,
            'printer-is-accepting-jobs': True,
            'device-uri': 'usb://HP/LaserJet'
        }
    }
    mock_cups.Connection.return_value = mock_conn
    
    printers = get_printers()
    
    assert len(printers) == 1
    assert printers[0]['name'] == 'HP_Printer'
    assert printers[0]['description'] == 'HP LaserJet'
    assert printers[0]['accepting_jobs'] is True

@patch('photobooth.printing.CUPS_AVAILABLE', False)
def test_get_printers_cups_unavailable():
    """Test getting printers when CUPS is unavailable"""
    printers = get_printers()
    assert printers == []

@patch('photobooth.printing.CUPS_AVAILABLE', True)
@patch('photobooth.printing.cups')
@patch('photobooth.printing.get_setting')
def test_get_default_printer_from_setting(mock_get_setting, mock_cups):
    """Test getting default printer from settings"""
    mock_get_setting.return_value = 'Test_Printer'
    
    printer = get_default_printer()
    assert printer == 'Test_Printer'

@patch('photobooth.printing.CUPS_AVAILABLE', True)
@patch('photobooth.printing.cups')
def test_get_printer_status_success(mock_cups):
    """Test getting printer status successfully"""
    mock_conn = MagicMock()
    mock_conn.getPrinters.return_value = {
        'Test_Printer': {
            'printer-info': 'Test Printer',
            'printer-state': 3,
            'printer-state-message': 'Ready',
            'printer-is-accepting-jobs': True
        }
    }
    mock_cups.Connection.return_value = mock_conn
    
    status = get_printer_status('Test_Printer')
    
    assert status['available'] is True
    assert status['name'] == 'Test_Printer'
    assert status['ready'] is True

@patch('photobooth.printing.CUPS_AVAILABLE', False)
def test_get_printer_status_cups_unavailable():
    """Test printer status when CUPS unavailable"""
    status = get_printer_status()
    
    assert status['available'] is False
    assert 'CUPS not available' in status['error']

@patch('photobooth.printing.CUPS_AVAILABLE', True)
@patch('photobooth.printing.cups')
@patch('photobooth.printing.get_default_printer')
@patch('photobooth.printing.optimize_image_for_print')
@patch('photobooth.printing.log_print_job')
@patch('os.path.exists')
def test_print_photo_success(mock_exists, mock_log_job, mock_optimize, 
                            mock_get_printer, mock_cups):
    """Test successful photo printing"""
    mock_exists.return_value = True
    mock_get_printer.return_value = 'Test_Printer'
    mock_optimize.return_value = '/path/to/optimized.jpg'
    
    mock_conn = MagicMock()
    mock_conn.printFile.return_value = 123
    mock_cups.Connection.return_value = mock_conn
    
    result = print_photo('/path/to/photo.jpg', 'photo.jpg')
    
    assert result['success'] is True
    assert result['job_id'] == 123
    mock_log_job.assert_called_once()

@patch('photobooth.printing.CUPS_AVAILABLE', True)
@patch('photobooth.printing.create_test_print_image')
@patch('photobooth.printing.print_photo')
def test_test_print_success(mock_print_photo, mock_create_image):
    """Test successful test print"""
    mock_create_image.return_value = '/path/to/test.jpg'
    mock_print_photo.return_value = {'success': True, 'job_id': 456}
    
    result = test_print('Test_Printer')
    
    assert result['success'] is True
    assert 'job_id' in result

def test_validate_print_settings_cups_unavailable():
    """Test print settings validation when CUPS unavailable"""
    with patch('photobooth.printing.CUPS_AVAILABLE', False):
        result = validate_print_settings()
        
        assert result['valid'] is False
        assert any('CUPS' in issue for issue in result['issues'])

@patch('photobooth.printing.CUPS_AVAILABLE', True)
@patch('photobooth.printing.get_default_printer')
def test_validate_print_settings_no_printer(mock_get_printer):
    """Test print settings validation with no printer"""
    mock_get_printer.return_value = None
    
    result = validate_print_settings()
    
    assert result['valid'] is False
    assert any('No default printer' in issue for issue in result['issues'])