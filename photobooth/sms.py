"""
SMS functionality using SMS-Gate and ImgBB for photo sharing
"""
import os
import logging
import requests
import base64
from typing import Dict, Any, Optional
from flask import current_app

from .models import get_setting, log_sms_message

logger = logging.getLogger(__name__)

def upload_image_to_imgbb(image_path: str) -> Dict[str, Any]:
    """
    Upload image to ImgBB and return the URL
    Using ImgBB free API (no registration required)
    """
    try:
        # ImgBB API endpoint (using free tier - no API key required)
        url = "https://api.imgbb.com/1/upload"
        
        # Read and encode image
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Prepare payload
        payload = {
            'image': image_data,
            'expiration': 86400  # 24 hours (free tier limit)
        }
        
        # Make request
        response = requests.post(url, data=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                image_url = result['data']['url']
                display_url = result['data']['display_url']
                
                logger.info(f"Image uploaded to ImgBB successfully: {display_url}")
                
                return {
                    'success': True,
                    'url': image_url,
                    'display_url': display_url,
                    'service': 'ImgBB',
                    'expiration': '24 hours'
                }
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.error(f"ImgBB upload failed: {error_msg}")
                return {
                    'success': False,
                    'error': f'ImgBB error: {error_msg}'
                }
        else:
            logger.error(f"ImgBB upload failed with status {response.status_code}")
            return {
                'success': False,
                'error': f'Upload failed with status {response.status_code}'
            }
            
    except Exception as e:
        logger.error(f"Failed to upload image to ImgBB: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def send_sms_via_gateway(phone_number: str, message: str) -> Dict[str, Any]:
    """
    Send SMS using SMS-Gate local server
    """
    try:
        # Get SMS gateway settings
        gateway_host = get_setting('sms_gateway_host', '')
        gateway_username = get_setting('sms_gateway_username', '')
        gateway_password = get_setting('sms_gateway_password', '')
        
        if not all([gateway_host, gateway_username, gateway_password]):
            return {
                'success': False,
                'error': 'SMS gateway not configured. Please configure in admin settings.'
            }
        
        # Prepare SMS-Gate API request
        api_url = f"{gateway_host}/message"
        
        payload = {
            'phone': phone_number,
            'message': message
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Make authenticated request
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            auth=(gateway_username, gateway_password),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"SMS sent successfully to {phone_number}")
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'gateway_response': result
            }
        else:
            error_msg = f"SMS gateway returned status {response.status_code}"
            if response.text:
                error_msg += f": {response.text}"
            
            logger.error(f"SMS sending failed: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg
            }
            
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def send_photo_sms(photo_path: str, phone_number: str, custom_message: str = None) -> Dict[str, Any]:
    """
    Complete workflow: Upload photo and send SMS with link
    """
    try:
        # Validate phone number (basic validation)
        if not phone_number or len(phone_number.strip()) < 10:
            return {
                'success': False,
                'error': 'Invalid phone number'
            }
        
        phone_number = phone_number.strip()
        
        # Upload image to ImgBB
        logger.info(f"Uploading photo for SMS to {phone_number}")
        upload_result = upload_image_to_imgbb(photo_path)
        
        if not upload_result['success']:
            log_sms_message(phone_number, '', 'failed', f"Image upload failed: {upload_result['error']}")
            return {
                'success': False,
                'error': f"Image upload failed: {upload_result['error']}"
            }
        
        image_url = upload_result['url']
        service_name = upload_result['service']
        expiration = upload_result['expiration']
        
        # Prepare SMS message
        if custom_message:
            sms_text = f"{custom_message}\n\nYour photo: {image_url}\n\n(Hosted on {service_name}, expires in {expiration})"
        else:
            sms_text = f"Here's your photo from the PhotoBooth! {image_url}\n\n(Hosted on {service_name}, expires in {expiration})"
        
        # Send SMS
        sms_result = send_sms_via_gateway(phone_number, sms_text)
        
        if sms_result['success']:
            # Log successful SMS
            log_sms_message(phone_number, image_url, 'sent')
            
            logger.info(f"Photo SMS sent successfully to {phone_number}")
            
            return {
                'success': True,
                'message': 'Photo sent successfully!',
                'image_url': image_url,
                'service': service_name
            }
        else:
            # Log failed SMS
            log_sms_message(phone_number, image_url, 'failed', sms_result['error'])
            
            return {
                'success': False,
                'error': f"SMS sending failed: {sms_result['error']}"
            }
            
    except Exception as e:
        logger.error(f"Failed to send photo SMS: {e}")
        log_sms_message(phone_number, '', 'failed', str(e))
        
        return {
            'success': False,
            'error': str(e)
        }

def test_sms_gateway() -> Dict[str, Any]:
    """
    Test SMS gateway connectivity
    """
    try:
        gateway_host = get_setting('sms_gateway_host', '')
        gateway_username = get_setting('sms_gateway_username', '')
        gateway_password = get_setting('sms_gateway_password', '')
        
        if not all([gateway_host, gateway_username, gateway_password]):
            return {
                'success': False,
                'error': 'SMS gateway not configured'
            }
        
        # Test connection to SMS-Gate API
        api_url = f"{gateway_host}/health"
        
        response = requests.get(
            api_url,
            auth=(gateway_username, gateway_password),
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'SMS gateway connection successful',
                'gateway_host': gateway_host
            }
        else:
            return {
                'success': False,
                'error': f'Gateway returned status {response.status_code}'
            }
            
    except Exception as e:
        logger.error(f"SMS gateway test failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_sms_gateway_status() -> Dict[str, Any]:
    """
    Get current SMS gateway configuration status
    """
    try:
        gateway_host = get_setting('sms_gateway_host', '')
        gateway_username = get_setting('sms_gateway_username', '')
        gateway_password = get_setting('sms_gateway_password', '')
        
        configured = bool(gateway_host and gateway_username and gateway_password)
        
        if configured:
            # Test connectivity
            test_result = test_sms_gateway()
            status = 'connected' if test_result['success'] else 'error'
            error = test_result.get('error') if not test_result['success'] else None
        else:
            status = 'not_configured'
            error = None
        
        return {
            'configured': configured,
            'status': status,
            'gateway_host': gateway_host if configured else None,
            'error': error
        }
        
    except Exception as e:
        logger.error(f"Failed to get SMS gateway status: {e}")
        return {
            'configured': False,
            'status': 'error',
            'error': str(e)
        }