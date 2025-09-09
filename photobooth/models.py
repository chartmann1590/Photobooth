"""
Database models and operations for SQLite
"""
import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

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
        'app_version': '1.0.0'
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