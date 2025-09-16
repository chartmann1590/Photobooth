"""
Gotify notification system for PhotoBooth
Handles real-time notifications for printer errors and other critical events
"""
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GotifyNotifier:
    """Gotify notification client for PhotoBooth"""
    
    def __init__(self):
        self._last_notification_time = {}
        self._cooldown_period = timedelta(minutes=5)  # Prevent spam
    
    def _get_settings(self) -> Dict[str, Any]:
        """Get Gotify settings from database"""
        try:
            from .models import get_setting
            
            def get_bool_setting(key, default=False):
                """Helper to convert setting to boolean"""
                value = get_setting(key, str(default).lower())
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'on')
            
            return {
                'enabled': get_bool_setting('gotify_enabled', False),
                'server_url': get_setting('gotify_server_url', ''),
                'app_token': get_setting('gotify_app_token', ''),
                'printer_errors_enabled': get_bool_setting('gotify_printer_errors_enabled', True)
            }
        except Exception as e:
            logger.error(f"Failed to get Gotify settings: {e}")
            return {
                'enabled': False,
                'server_url': '',
                'app_token': '',
                'printer_errors_enabled': False
            }
    
    def _is_cooldown_active(self, notification_key: str) -> bool:
        """Check if notification is in cooldown period"""
        if notification_key not in self._last_notification_time:
            return False
        
        last_time = self._last_notification_time[notification_key]
        return datetime.now() - last_time < self._cooldown_period
    
    def _update_cooldown(self, notification_key: str):
        """Update last notification time for cooldown tracking"""
        self._last_notification_time[notification_key] = datetime.now()
    
    def _get_formatted_time(self) -> str:
        """Get current time formatted for notifications"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _send_notification(self, title: str, message: str, priority: int = 5) -> bool:
        """Send notification to Gotify server"""
        settings = self._get_settings()
        
        if not settings['enabled']:
            logger.debug("Gotify notifications disabled")
            return False
            
        if not settings['server_url'] or not settings['app_token']:
            logger.warning("Gotify not configured - missing server URL or app token")
            return False
        
        try:
            # Clean up server URL
            server_url = settings['server_url'].rstrip('/')
            if not server_url.startswith(('http://', 'https://')):
                server_url = f"http://{server_url}"
            
            # Prepare notification payload
            url = f"{server_url}/message"
            params = {'token': settings['app_token']}
            data = {
                'title': title,
                'message': message,
                'priority': priority
            }
            
            # Send notification
            response = requests.post(url, params=params, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Gotify notification sent: {title}")
                return True
            else:
                logger.error(f"Gotify notification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Gotify notification: {e}")
            return False
    
    def send_printer_error(self, printer_name: str, error_type: str, error_message: str) -> bool:
        """Send high-priority printer error notification"""
        settings = self._get_settings()
        
        if not settings['printer_errors_enabled']:
            logger.debug("Printer error notifications disabled")
            return False
        
        # Create unique key for this error type and printer
        notification_key = f"printer_error_{printer_name}_{error_type}"
        
        # Check cooldown to prevent spam
        if self._is_cooldown_active(notification_key):
            logger.debug(f"Printer error notification in cooldown: {notification_key}")
            return False
        
        # Determine error severity and appropriate prefix
        error_prefixes = {
            'paper_jam': 'PAPER JAM',
            'no_paper': 'NO PAPER',
            'low_ink': 'LOW INK',
            'no_ink': 'NO INK',
            'offline': 'OFFLINE',
            'error': 'ERROR',
            'connection': 'CONNECTION'
        }
        
        prefix = error_prefixes.get(error_type, 'PRINTER ERROR')
        
        title = f"PhotoBooth Alert: {prefix}"
        message = f"""**Printer**: {printer_name}
**Error**: {error_type.replace('_', ' ').title()}
**Details**: {error_message}
**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Action Required**: Please check the printer immediately to resolve this issue."""
        
        # Send high-priority notification
        success = self._send_notification(title, message, priority=8)
        
        if success:
            self._update_cooldown(notification_key)
        
        return success
    
    def send_printer_status(self, printer_name: str, status: str, details: str = "") -> bool:
        """Send printer status notification (lower priority)"""
        settings = self._get_settings()
        
        if not settings['printer_errors_enabled']:
            return False
        
        title = f"PhotoBooth Printer Update"
        message = f"""**Printer**: {printer_name}
**Status**: {status}
**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        if details:
            message += f"\n**Details**: {details}"
        
        # Send normal priority notification
        return self._send_notification(title, message, priority=4)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Gotify server connection"""
        settings = self._get_settings()
        
        if not settings['enabled']:
            return {
                'success': False,
                'error': 'Gotify notifications are disabled'
            }
        
        if not settings['server_url'] or not settings['app_token']:
            return {
                'success': False,
                'error': 'Gotify not configured - missing server URL or app token'
            }
        
        try:
            # Test with a simple notification
            success = self._send_notification(
                title="PhotoBooth Test",
                message="Gotify notification system is working correctly!",
                priority=2
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Test notification sent successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send test notification'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
_gotify_notifier = None

def get_gotify_notifier() -> GotifyNotifier:
    """Get global Gotify notifier instance"""
    global _gotify_notifier
    if _gotify_notifier is None:
        _gotify_notifier = GotifyNotifier()
    return _gotify_notifier

def send_printer_error_notification(printer_name: str, error_type: str, error_message: str) -> bool:
    """Convenience function to send printer error notification"""
    try:
        notifier = get_gotify_notifier()
        return notifier.send_printer_error(printer_name, error_type, error_message)
    except Exception as e:
        logger.error(f"Failed to send printer error notification: {e}")
        return False

def test_gotify_connection() -> Dict[str, Any]:
    """Convenience function to test Gotify connection"""
    try:
        notifier = get_gotify_notifier()
        return notifier.test_connection()
    except Exception as e:
        logger.error(f"Failed to test Gotify connection: {e}")
        return {
            'success': False,
            'error': str(e)
        }