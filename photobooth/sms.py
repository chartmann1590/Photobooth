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

def upload_image_to_0x0st(image_path: str) -> Dict[str, Any]:
    """
    Upload image to 0x0.st - a free, no-registration file hosting service
    """
    try:
        url = "https://0x0.st"
        
        # Read image file
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            data = {'expires': '24'}  # Expire after 24 hours
            headers = {'User-Agent': 'PhotoBooth/1.0 (Wedding Photo Sharing)'}
            
            # Make request
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            image_url = response.text.strip()
            
            logger.info(f"Image uploaded to 0x0.st successfully: {image_url}")
            
            return {
                'success': True,
                'url': image_url,
                'display_url': image_url,
                'service': '0x0.st',
                'expiration': '24 hours'
            }
        else:
            logger.error(f"0x0.st upload failed with status {response.status_code}: {response.text}")
            return {
                'success': False,
                'error': f'Upload failed with status {response.status_code}'
            }
            
    except Exception as e:
        logger.error(f"Failed to upload image to 0x0.st: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def upload_image_to_imgbb(image_path: str) -> Dict[str, Any]:
    """
    Upload image to ImgBB and return the URL
    Note: This requires a valid API key. Get one at https://api.imgbb.com/
    """
    try:
        # Try to get API key from settings
        from .models import get_setting
        api_key = get_setting('imgbb_api_key', '')
        
        if not api_key:
            logger.warning("ImgBB API key not configured, falling back to 0x0.st")
            return upload_image_to_0x0st(image_path)
        
        url = f"https://api.imgbb.com/1/upload?key={api_key}"
        
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
        
        # Prepare SMS-Gate API request (local server endpoint)
        if not gateway_host.startswith(('http://', 'https://')):
            gateway_host = f"http://{gateway_host}"
        api_url = f"{gateway_host}/message"
        
        payload = {
            'phoneNumbers': [phone_number],
            'textMessage': {
                'text': message
            },
            'withDeliveryReport': True
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
        
        if response.status_code in [200, 201, 202]:  # Accept success statuses
            result = response.json()
            
            # Check if the SMS is in a successful state (sent, pending, or delivered)
            state = result.get('state', '').lower()
            if state in ['pending', 'sent', 'delivered']:
                logger.info(f"SMS sent successfully to {phone_number} (state: {state})")
                
                return {
                    'success': True,
                    'message': 'SMS sent successfully',
                    'gateway_response': result
                }
            else:
                logger.warning(f"SMS to {phone_number} has unexpected state: {state}")
                return {
                    'success': True,  # Still consider it successful since gateway accepted it
                    'message': f'SMS sent (state: {state})',
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
        
        # Upload image to hosting service (ImgBB with 0x0.st fallback)
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
        
        # Prepare SMS message with automated introduction
        automated_intro = "💒 Greetings from the Wedding PhotoBooth! 📸"
        
        if custom_message:
            sms_text = f"{automated_intro}\n\n{custom_message}\n\nYour photo: {image_url}\n\n(Hosted on {service_name}, expires in {expiration})"
        else:
            sms_text = f"{automated_intro}\n\nHere's your beautiful photo from today's celebration! {image_url}\n\n(Hosted on {service_name}, expires in {expiration})"
        
        # Send SMS
        sms_result = send_sms_via_gateway(phone_number, sms_text)
        
        if sms_result['success']:
            # Log successful SMS
            log_sms_message(phone_number, image_url, 'sent')
            
            logger.info(f"Photo SMS sent successfully to {phone_number}")
            
            # Play success audio notification
            try:
                from .audio import speak_text
                speak_text("SMS sent successfully!", async_mode=True)
            except Exception as e:
                logger.warning(f"Failed to play SMS success audio: {e}")
            
            return {
                'success': True,
                'message': 'Photo sent successfully!',
                'image_url': image_url,
                'service': service_name
            }
        else:
            # Log failed SMS
            log_sms_message(phone_number, image_url, 'failed', sms_result['error'])
            
            # Play error audio notification
            try:
                from .audio import speak_text
                speak_text("SMS sending failed. Please try again.", async_mode=True)
            except Exception as e:
                logger.warning(f"Failed to play SMS error audio: {e}")
            
            return {
                'success': False,
                'error': f"SMS sending failed: {sms_result['error']}"
            }
            
    except Exception as e:
        logger.error(f"Failed to send photo SMS: {e}")
        log_sms_message(phone_number, '', 'failed', str(e))
        
        # Play error audio notification
        try:
            from .audio import speak_text
            speak_text("SMS sending failed. Please try again.", async_mode=True)
        except Exception as audio_error:
            logger.warning(f"Failed to play SMS error audio: {audio_error}")
        
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
        
        # Test connection to SMS-Gate API (health endpoint at root)
        if not gateway_host.startswith(('http://', 'https://')):
            gateway_host = f"http://{gateway_host}"
        api_url = f"{gateway_host}/health"
        
        # Health endpoint - simple GET, no authentication required
        response = requests.get(api_url, timeout=10)
        
        # SMS-Gate returns 500 when status="fail" but still provides valid health data
        if response.status_code in [200, 500]:
            try:
                health_data = response.json()
                status = health_data.get('status', 'unknown')
                version = health_data.get('version', 'unknown')
                release_id = health_data.get('releaseId', 'unknown')
                checks = health_data.get('checks', {})
                
                # Extract specific health metrics
                battery_level = None
                connection_status = None
                
                if 'battery:level' in checks:
                    battery_level = checks['battery:level'].get('observedValue')
                    
                if 'connection:status' in checks:
                    connection_status = checks['connection:status'].get('observedValue') == 1
                
                if status == 'pass':
                    return {
                        'success': True,
                        'message': 'SMS gateway connection successful',
                        'gateway_host': gateway_host,
                        'version': version,
                        'releaseId': release_id,
                        'status': status,
                        'battery_level': battery_level,
                        'connection_status': connection_status,
                        'checks': checks
                    }
                elif status == 'fail':
                    # Check which health checks failed
                    failed_checks = []
                    ignorable_checks = ['connection:status', 'messages:failed']
                    critical_failed_checks = []
                    
                    for check_name, check_data in checks.items():
                        if check_data.get('status') == 'fail':
                            failed_checks.append(check_name)
                            if check_name not in ignorable_checks:
                                critical_failed_checks.append(check_name)
                    
                    # Build warning message for ignorable failures
                    warning_parts = []
                    if 'connection:status' in failed_checks:
                        warning_parts.append('connection status offline')
                    if 'messages:failed' in failed_checks:
                        # Get failed message count if available
                        failed_count = checks.get('messages:failed', {}).get('observedValue', 'unknown')
                        warning_parts.append(f'failed messages: {failed_count}')
                    
                    warning_msg = f" ({', '.join(warning_parts)})" if warning_parts else ""
                    
                    # If only ignorable checks failed, treat as success with warning
                    if len(critical_failed_checks) == 0:
                        return {
                            'success': True,
                            'message': f'SMS gateway connection successful{warning_msg}',
                            'gateway_host': gateway_host,
                            'version': version,
                            'releaseId': release_id,
                            'status': status,
                            'battery_level': battery_level,
                            'connection_status': connection_status,
                            'checks': checks
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Gateway health check failed: status={status}, critical failures: {critical_failed_checks}'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Gateway health check failed: status={status}'
                    }
            except Exception as e:
                return {
                    'success': True,  # 200 response is still success even if we can't parse
                    'message': 'SMS gateway connection successful (could not parse health data)',
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
            
            # Include health data if available
            health_data = None
            if test_result['success'] and 'version' in test_result:
                # Parse health information for display
                health_data = {
                    'version': test_result.get('version'),
                    'releaseId': test_result.get('releaseId'),
                    'status': test_result.get('status'),
                    'battery_level': test_result.get('battery_level'),
                    'connection_status': test_result.get('connection_status'),
                    'checks': test_result.get('checks', {})
                }
                
        else:
            status = 'not_configured'
            error = None
            health_data = None
        
        return {
            'configured': configured,
            'status': status,
            'gateway_host': gateway_host if configured else None,
            'error': error,
            'health': health_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get SMS gateway status: {e}")
        return {
            'configured': False,
            'status': 'error',
            'error': str(e)
        }