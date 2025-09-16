"""
Database models and operations for SQLite
"""
import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str):
    """Initialize database with required tables"""
    try:
        with get_db_connection(db_path) as conn:
            # Settings table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Photos table (optional - for metadata tracking)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    original_filename TEXT,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    is_printed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    printed_at TIMESTAMP NULL
                )
            ''')
            
            # Print jobs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS print_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    photo_filename TEXT NOT NULL,
                    printer_name TEXT,
                    job_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    error_message TEXT NULL
                )
            ''')
            
            # Events log table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Print cartridge tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS print_cartridges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cartridge_name TEXT NOT NULL,
                    printer_name TEXT NOT NULL,
                    max_prints INTEGER NOT NULL,
                    current_prints INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    replaced_at TIMESTAMP NULL
                )
            ''')
            
            # Printer error tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS printer_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    printer_name TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    error_state TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_announced TIMESTAMP NULL,
                    resolved_at TIMESTAMP NULL
                )
            ''')
            
            # SMS messages tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sms_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
            # Insert default settings if they don't exist
            _insert_default_settings(conn)
            
            logger.info(f"Database initialized: {db_path}")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def _insert_default_settings(conn: sqlite3.Connection):
    """Insert default settings"""
    default_settings = {
        'default_printer': '',
        'tts_enabled': 'true',
        'tts_voice': 'en+f3',
        'tts_rate': '150',
        'photo_quality': '95',
        'print_paper_size': '4x6',
        'countdown_enabled': 'true',
        'countdown_duration': '3',
        'app_version': '1.0.0',
        'print_count_enabled': 'false',
        'print_count_max': '0',
        'print_count_low_warning': '10',
        'total_prints_ever': '0',
        'low_ink_audio_enabled': 'true',
        'empty_cartridge_audio_enabled': 'true',
        'printer_error_audio_enabled': 'true',
        'ink_warning_frequency_minutes': '5',
        'error_announcement_cooldown_minutes': '2',
        'printer_status_polling_enabled': 'true',
        'printer_status_polling_interval_seconds': '30',
        'low_ink_message': 'Low ink warning! Please consider replacing the cartridge soon.',
        'empty_cartridge_message': 'Ink cartridge is empty! Printing is disabled until cartridge is replaced.',
        'gotify_enabled': 'false',
        'gotify_server_url': '',
        'gotify_app_token': '',
        'gotify_printer_errors_enabled': 'true',
        'immich_enabled': 'false',
        'immich_server_url': '',
        'immich_api_key': '',
        'immich_album_name': 'PhotoBooth',
        'immich_auto_sync': 'true',
        'immich_sync_on_capture': 'true'
    }
    
    for key, value in default_settings.items():
        try:
            conn.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
        except Exception as e:
            logger.warning(f"Failed to insert default setting {key}: {e}")

def get_settings() -> Dict[str, Any]:
    """Get all settings as a dictionary"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute('SELECT key, value FROM settings')
            settings = {}
            
            for row in cursor.fetchall():
                key = row['key']
                value = row['value']
                
                # Try to convert boolean strings
                if value.lower() in ('true', 'false'):
                    settings[key] = value.lower() == 'true'
                # Try to convert numeric strings
                elif value.isdigit():
                    settings[key] = int(value)
                else:
                    settings[key] = value
            
            return settings
            
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return {}

def get_setting(key: str, default: Any = None) -> Any:
    """Get a specific setting"""
    settings = get_settings()
    return settings.get(key, default)

def update_setting(key: str, value: Any) -> bool:
    """Update a setting"""
    from flask import current_app
    
    try:
        # Convert value to string for storage
        str_value = str(value).lower() if isinstance(value, bool) else str(value)
        
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, str_value))
            conn.commit()
            
            logger.info(f"Setting updated: {key} = {value}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to update setting {key}: {e}")
        return False

def log_photo(filename: str, original_filename: str = None, width: int = None, 
              height: int = None, file_size: int = None) -> bool:
    """Log photo metadata"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO photos 
                (filename, original_filename, width, height, file_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, original_filename, width, height, file_size))
            conn.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to log photo {filename}: {e}")
        return False

def mark_photo_printed(filename: str) -> bool:
    """Mark photo as printed"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                UPDATE photos 
                SET is_printed = 1, printed_at = CURRENT_TIMESTAMP
                WHERE filename = ?
            ''', (filename,))
            conn.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to mark photo as printed {filename}: {e}")
        return False

def log_print_job(photo_filename: str, printer_name: str = None, 
                  job_id: int = None, status: str = 'pending') -> bool:
    """Log print job"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                INSERT INTO print_jobs 
                (photo_filename, printer_name, job_id, status)
                VALUES (?, ?, ?, ?)
            ''', (photo_filename, printer_name, job_id, status))
            conn.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to log print job: {e}")
        return False

def update_print_job_status(job_id: int, status: str, error_message: str = None) -> bool:
    """Update print job status"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            if status == 'completed':
                conn.execute('''
                    UPDATE print_jobs 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE job_id = ?
                ''', (status, error_message, job_id))
            else:
                conn.execute('''
                    UPDATE print_jobs 
                    SET status = ?, error_message = ?
                    WHERE job_id = ?
                ''', (status, error_message, job_id))
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to update print job status: {e}")
        return False

def get_print_job_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent print job logs from database"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute('''
                SELECT photo_filename, printer_name, job_id, status, error_message, 
                       created_at, completed_at
                FROM print_jobs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            jobs = []
            for row in cursor.fetchall():
                jobs.append({
                    'filename': row['photo_filename'],
                    'printer': row['printer_name'],
                    'job_id': row['job_id'],
                    'status': row['status'],
                    'error_message': row['error_message'],
                    'created_at': row['created_at'],
                    'completed_at': row['completed_at']
                })
            
            return jobs
            
    except Exception as e:
        logger.error(f"Failed to get print job logs: {e}")
        return []

def log_event(event_type: str, event_data: Dict[str, Any] = None) -> bool:
    """Log an event"""
    from flask import current_app
    
    try:
        event_data_json = json.dumps(event_data) if event_data else None
        
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                INSERT INTO events (event_type, event_data)
                VALUES (?, ?)
            ''', (event_type, event_data_json))
            conn.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to log event {event_type}: {e}")
        return False

def get_photo_stats() -> Dict[str, Any]:
    """Get photo statistics"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            # Total photos
            cursor = conn.execute('SELECT COUNT(*) as count FROM photos')
            total_photos = cursor.fetchone()['count']
            
            # Printed photos
            cursor = conn.execute('SELECT COUNT(*) as count FROM photos WHERE is_printed = 1')
            printed_photos = cursor.fetchone()['count']
            
            # Recent photos (last 24 hours)
            cursor = conn.execute('''
                SELECT COUNT(*) as count FROM photos 
                WHERE created_at > datetime('now', '-1 day')
            ''')
            recent_photos = cursor.fetchone()['count']
            
            return {
                'total_photos': total_photos,
                'printed_photos': printed_photos,
                'recent_photos': recent_photos
            }
            
    except Exception as e:
        logger.error(f"Failed to get photo stats: {e}")
        return {
            'total_photos': 0,
            'printed_photos': 0,
            'recent_photos': 0
        }

def get_print_count_status() -> Dict[str, Any]:
    """Get current print count status"""
    try:
        enabled = get_setting('print_count_enabled', False)
        if not enabled:
            return {
                'enabled': False,
                'remaining': 0,
                'total': 0,
                'used': 0,
                'low_warning': 0,
                'is_low': False,
                'is_empty': False,
                'total_prints_ever': get_setting('total_prints_ever', 0)
            }
        
        max_prints = get_setting('print_count_max', 0)
        total_ever = get_setting('total_prints_ever', 0)
        low_warning = get_setting('print_count_low_warning', 10)
        
        # Get current cartridge usage from active cartridge
        current_prints = get_current_cartridge_prints()
        remaining = max(0, max_prints - current_prints)
        
        return {
            'enabled': True,
            'remaining': remaining,
            'total': max_prints,
            'used': current_prints,
            'low_warning': low_warning,
            'is_low': remaining <= low_warning and remaining > 0,
            'is_empty': remaining <= 0,
            'total_prints_ever': total_ever
        }
        
    except Exception as e:
        logger.error(f"Failed to get print count status: {e}")
        return {
            'enabled': False,
            'remaining': 0,
            'total': 0,
            'used': 0,
            'low_warning': 0,
            'is_low': False,
            'is_empty': False,
            'total_prints_ever': 0
        }

def get_current_cartridge_prints() -> int:
    """Get current prints used from active cartridge"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute('''
                SELECT current_prints FROM print_cartridges 
                WHERE is_active = 1 
                ORDER BY installed_at DESC 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            return result['current_prints'] if result else 0
            
    except Exception as e:
        logger.error(f"Failed to get current cartridge prints: {e}")
        return 0

def increment_print_count() -> bool:
    """Increment print count after successful print"""
    from flask import current_app
    
    try:
        # Increment total prints ever
        total_ever = get_setting('total_prints_ever', 0)
        update_setting('total_prints_ever', total_ever + 1)
        
        # If print counting is enabled, update cartridge usage
        if get_setting('print_count_enabled', False):
            with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
                # Get or create active cartridge
                cursor = conn.execute('''
                    SELECT id, current_prints FROM print_cartridges 
                    WHERE is_active = 1 
                    ORDER BY installed_at DESC 
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                
                if result:
                    # Update existing cartridge
                    conn.execute('''
                        UPDATE print_cartridges 
                        SET current_prints = current_prints + 1 
                        WHERE id = ?
                    ''', (result['id'],))
                else:
                    # Create new cartridge with current settings
                    max_prints = get_setting('print_count_max', 0)
                    default_printer = get_setting('default_printer', 'Unknown')
                    conn.execute('''
                        INSERT INTO print_cartridges 
                        (cartridge_name, printer_name, max_prints, current_prints) 
                        VALUES (?, ?, ?, ?)
                    ''', ('Auto-created cartridge', default_printer, max_prints, 1))
                
                conn.commit()
        
        logger.info("Print count incremented successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to increment print count: {e}")
        return False

def install_new_cartridge(cartridge_name: str, max_prints: int, printer_name: str = None) -> bool:
    """Install a new cartridge and deactivate old ones"""
    from flask import current_app
    
    try:
        if printer_name is None:
            printer_name = get_setting('default_printer', 'Unknown')
        
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            # Deactivate all existing cartridges
            conn.execute('''
                UPDATE print_cartridges 
                SET is_active = 0, replaced_at = CURRENT_TIMESTAMP 
                WHERE is_active = 1
            ''')
            
            # Insert new cartridge
            conn.execute('''
                INSERT INTO print_cartridges 
                (cartridge_name, printer_name, max_prints, current_prints, is_active) 
                VALUES (?, ?, ?, 0, 1)
            ''', (cartridge_name, printer_name, max_prints))
            
            conn.commit()
        
        # Update settings
        update_setting('print_count_enabled', True)
        update_setting('print_count_max', max_prints)
        
        logger.info(f"New cartridge installed: {cartridge_name} ({max_prints} prints)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to install new cartridge: {e}")
        return False

def reset_print_count() -> bool:
    """Reset current cartridge print count to 0"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                UPDATE print_cartridges 
                SET current_prints = 0 
                WHERE is_active = 1
            ''')
            conn.commit()
        
        logger.info("Print count reset to 0")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset print count: {e}")
        return False

def get_cartridge_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get cartridge installation history"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute('''
                SELECT cartridge_name, printer_name, max_prints, current_prints, 
                       is_active, installed_at, replaced_at
                FROM print_cartridges 
                ORDER BY installed_at DESC 
                LIMIT ?
            ''', (limit,))
            
            cartridges = []
            for row in cursor.fetchall():
                cartridges.append({
                    'name': row['cartridge_name'],
                    'printer': row['printer_name'],
                    'max_prints': row['max_prints'],
                    'current_prints': row['current_prints'],
                    'is_active': bool(row['is_active']),
                    'installed_at': row['installed_at'],
                    'replaced_at': row['replaced_at']
                })
            
            return cartridges
            
    except Exception as e:
        logger.error(f"Failed to get cartridge history: {e}")
        return []

def log_printer_error(printer_name: str, error_message: str, error_state: str) -> bool:
    """Log or update a printer error"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            # Check if this error already exists and is active
            cursor = conn.execute('''
                SELECT id, last_announced FROM printer_errors 
                WHERE printer_name = ? AND error_message = ? AND is_active = 1
            ''', (printer_name, error_message))
            existing_error = cursor.fetchone()
            
            if existing_error:
                # Update existing error
                conn.execute('''
                    UPDATE printer_errors 
                    SET last_seen = CURRENT_TIMESTAMP, error_state = ?
                    WHERE id = ?
                ''', (error_state, existing_error['id']))
            else:
                # Insert new error
                conn.execute('''
                    INSERT INTO printer_errors 
                    (printer_name, error_message, error_state) 
                    VALUES (?, ?, ?)
                ''', (printer_name, error_message, error_state))
            
            conn.commit()
            
            # Send Gotify notification for new printer errors
            if not existing_error:
                try:
                    from .gotify import send_printer_error_notification
                    
                    # Determine error type based on error message and state
                    error_type = _classify_printer_error(error_message, error_state)
                    send_printer_error_notification(printer_name, error_type, error_message)
                except Exception as gotify_error:
                    logger.warning(f"Failed to send Gotify notification for printer error: {gotify_error}")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to log printer error: {e}")
        return False

def _classify_printer_error(error_message: str, error_state: str) -> str:
    """Classify printer error type based on message and state"""
    error_msg_lower = error_message.lower()
    error_state_lower = error_state.lower()
    
    # Check for specific error types
    if 'jam' in error_msg_lower or 'jammed' in error_msg_lower:
        return 'paper_jam'
    elif 'no paper' in error_msg_lower or 'out of paper' in error_msg_lower or 'paper empty' in error_msg_lower:
        return 'no_paper'
    elif 'low ink' in error_msg_lower or 'ink low' in error_msg_lower:
        return 'low_ink'
    elif 'no ink' in error_msg_lower or 'ink empty' in error_msg_lower or 'out of ink' in error_msg_lower:
        return 'no_ink'
    elif 'offline' in error_msg_lower or 'not connected' in error_msg_lower:
        return 'offline'
    elif 'connection' in error_msg_lower or 'connect' in error_msg_lower:
        return 'connection'
    elif error_state_lower in ['stopped', 'error', 'halted']:
        return 'error'
    else:
        return 'error'

def mark_error_announced(printer_name: str, error_message: str) -> bool:
    """Mark an error as announced"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                UPDATE printer_errors 
                SET last_announced = CURRENT_TIMESTAMP
                WHERE printer_name = ? AND error_message = ? AND is_active = 1
            ''', (printer_name, error_message))
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to mark error as announced: {e}")
        return False

def resolve_printer_errors(printer_name: str) -> bool:
    """Mark all active errors for a printer as resolved"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                UPDATE printer_errors 
                SET is_active = 0, resolved_at = CURRENT_TIMESTAMP
                WHERE printer_name = ? AND is_active = 1
            ''', (printer_name,))
            conn.commit()
            
            logger.info(f"Resolved all printer errors for {printer_name}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to resolve printer errors: {e}")
        return False

def get_active_printer_errors(printer_name: str = None) -> List[Dict[str, Any]]:
    """Get active printer errors"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            if printer_name:
                cursor = conn.execute('''
                    SELECT printer_name, error_message, error_state, first_seen, last_seen, last_announced
                    FROM printer_errors 
                    WHERE printer_name = ? AND is_active = 1
                    ORDER BY first_seen DESC
                ''', (printer_name,))
            else:
                cursor = conn.execute('''
                    SELECT printer_name, error_message, error_state, first_seen, last_seen, last_announced
                    FROM printer_errors 
                    WHERE is_active = 1
                    ORDER BY first_seen DESC
                ''')
            
            errors = []
            for row in cursor.fetchall():
                errors.append({
                    'printer_name': row['printer_name'],
                    'error_message': row['error_message'],
                    'error_state': row['error_state'],
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen'],
                    'last_announced': row['last_announced']
                })
            
            return errors
            
    except Exception as e:
        logger.error(f"Failed to get active printer errors: {e}")
        return []

def get_printer_error_status(printer_name: str) -> Dict[str, Any]:
    """Get current error status for a printer"""
    try:
        errors = get_active_printer_errors(printer_name)
        
        if not errors:
            return {
                'has_errors': False,
                'error_count': 0,
                'errors': [],
                'printing_disabled': False
            }
        
        # Check if any errors should disable printing
        printing_disabled = any(
            error['error_state'].lower() in ['stopped', 'error', 'offline'] 
            for error in errors
        )
        
        return {
            'has_errors': True,
            'error_count': len(errors),
            'errors': errors,
            'printing_disabled': printing_disabled,
            'latest_error': errors[0] if errors else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get printer error status: {e}")
        return {
            'has_errors': False,
            'error_count': 0,
            'errors': [],
            'printing_disabled': False
        }

# SMS-related functions
def log_sms_message(phone_number: str, image_url: str, status: str, error_message: str = None) -> bool:
    """Log an SMS message attempt"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                INSERT INTO sms_messages 
                (phone_number, image_url, status, error_message, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (phone_number, image_url, status, error_message))
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to log SMS message: {e}")
        return False

def get_sms_messages(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent SMS messages"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute('''
                SELECT id, phone_number, image_url, status, error_message, created_at
                FROM sms_messages 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row['id'],
                    'phone_number': row['phone_number'],
                    'image_url': row['image_url'],
                    'status': row['status'],
                    'error_message': row['error_message'],
                    'created_at': row['created_at']
                })
            
            return messages
            
    except Exception as e:
        logger.error(f"Failed to get SMS messages: {e}")
        return []

def get_sms_stats() -> Dict[str, Any]:
    """Get SMS usage statistics"""
    from flask import current_app
    
    try:
        with get_db_connection(current_app.config['DATABASE_PATH']) as conn:
            # Total messages
            cursor = conn.execute('SELECT COUNT(*) as total FROM sms_messages')
            total = cursor.fetchone()['total']
            
            # Successful messages
            cursor = conn.execute("SELECT COUNT(*) as successful FROM sms_messages WHERE status = 'sent'")
            successful = cursor.fetchone()['successful']
            
            # Failed messages
            cursor = conn.execute("SELECT COUNT(*) as failed FROM sms_messages WHERE status = 'failed'")
            failed = cursor.fetchone()['failed']
            
            # Today's messages
            cursor = conn.execute('''
                SELECT COUNT(*) as today 
                FROM sms_messages 
                WHERE DATE(created_at) = DATE('now')
            ''')
            today = cursor.fetchone()['today']
            
            return {
                'total': total,
                'successful': successful,
                'failed': failed,
                'today': today,
                'success_rate': round((successful / total * 100) if total > 0 else 0, 1)
            }
            
    except Exception as e:
        logger.error(f"Failed to get SMS stats: {e}")
        return {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'today': 0,
            'success_rate': 0
        }