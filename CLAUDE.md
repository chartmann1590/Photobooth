# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **PhotoBooth Flask application** designed for Raspberry Pi 3B, providing a wedding-themed photobooth system with offline WiFi access point, professional printing capabilities, and elegant user interface for dark venues.

## Technology Stack

- **Backend**: Flask 2.3.3 with Python 3.9+
- **Frontend**: Vanilla JavaScript with camera API integration
- **Database**: SQLite (via models.py)
- **Image Processing**: Pillow for photo manipulation and frame overlays
- **Printing**: CUPS integration via pycups
- **Text-to-Speech**: pyttsx3 for countdown announcements
- **Production Server**: Waitress WSGI server
- **Network**: hostapd + dnsmasq for WiFi access point

## Development Commands

### Environment Setup
```bash
# Install dependencies (production)
pip install -r requirements.txt

# Install test dependencies
pip install -r test_requirements.txt

# Create virtual environment (done by install.sh)
python -m venv venv
source venv/bin/activate
```

### Audio/TTS Testing
```bash
# Test TTS functionality
cd /opt/photobooth && source venv/bin/activate
python -c "from photobooth.audio import speak_text; speak_text('Test message')"

# Check TTS status
python -c "from photobooth.audio import get_tts_status; print(get_tts_status())"
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_models.py

# Run tests with verbose output
pytest -v

# Run coverage report
pytest --cov=photobooth --cov-report=html
```

### Running the Application
```bash
# Development mode
python app.py

# Production mode
./run.sh
# or
python -m waitress --host=127.0.0.1 --port=5000 app:create_app
```

### Service Management (Production)
```bash
# System service control
sudo systemctl start photobooth
sudo systemctl stop photobooth
sudo systemctl restart photobooth
sudo systemctl status photobooth

# View application logs
sudo journalctl -u photobooth -f
tail -f photobooth.log
```

## Architecture Overview

### Core Application Structure
- **app.py**: Main entry point using Flask application factory
- **config.py**: Configuration management with environment variable support
- **photobooth/__init__.py**: Application factory with blueprint registration
- **photobooth/routes_booth.py**: Main photobooth functionality (camera, photo capture)
- **photobooth/routes_settings.py**: Admin interface for configuration

### Key Modules
- **photobooth/models.py**: SQLite database models for photo metadata and settings
- **photobooth/storage.py**: Photo file management and organization
- **photobooth/imaging.py**: Image processing, resizing, and frame overlay application
- **photobooth/printing.py**: CUPS printer integration and queue management
- **photobooth/audio.py**: Text-to-speech functionality for countdown
- **photobooth/gotify.py**: Gotify notification system for printer errors and alerts

### Data Flow
1. **Photo Capture**: Browser camera API → Flask route → storage.py → database
2. **Image Processing**: Raw photo → imaging.py (resize, apply frame) → final photo
3. **Printing**: Print request → printing.py → CUPS → physical printer
4. **Gallery**: Database query → thumbnail generation → web interface

### Configuration Management
- Environment variables loaded via python-dotenv
- Main config in **config.py** with development/production classes
- Runtime settings stored in SQLite database (models.py)
- Photo storage paths, printer settings, TTS configuration all configurable

### Network Architecture (Production)
- Raspberry Pi creates WiFi access point (hostapd)
- DHCP/DNS services via dnsmasq
- Nginx reverse proxy with HTTPS certificates
- Flask app runs on localhost:5000 behind proxy
- Captive portal automatically opens photobooth interface

## Key File Locations

### Photos and Data
- `data/photos/all/` - All captured photos
- `data/photos/printed/` - Backup of printed photos
- `photobooth.db` - SQLite database with photo metadata
- `photobooth/static/frames/current.png` - Active frame overlay

### Configuration Files
- `.env` - Environment variables (created from .env.example)
- `services/` - System service configurations (nginx, hostapd, etc.)

### Static Assets
- `photobooth/static/css/` - Wedding-themed stylesheets
- `photobooth/static/js/booth.js` - Camera interface and photo capture
- `photobooth/templates/` - Jinja2 HTML templates

## Testing Guidelines

- Tests located in `tests/` directory
- Coverage requirement: 80% minimum (configured in pytest.ini)
- Test database and photo storage handled automatically by conftest.py
- Use pytest-flask for Flask application testing
- Mock external dependencies (printers, TTS) in tests

## Development Notes

### Camera Integration
- Uses browser MediaStream API for camera access
- Requires HTTPS for camera permissions (production uses mkcert certificates)
- Photo capture via HTML5 canvas element
- Supports both front/rear cameras on mobile devices

### Printing System
- CUPS integration allows any supported printer
- Print jobs queued and managed through database
- Supports 4x6 photo paper by default
- Admin interface for printer selection and testing

### Frame Overlay System
- PNG images with transparency applied over photos
- Configurable via admin interface
- Images processed server-side using Pillow
- Recommended size: 1800x1200 pixels (matches PHOTO_WIDTH/HEIGHT)

### Text-to-Speech System
- Built on eSpeak NG engine with pyttsx3 integration
- Customizable voice selection with enhanced voice options
- Configurable speech rate (80-300 words per minute)
- Custom messages for welcome, countdown, capture, and printing events
- Audio settings accessible via `/settings/audio` admin interface
- Fallback static voice options when dynamic loading fails
- Non-blocking async speech to prevent UI hangs

### Gotify Notification System
- Real-time push notifications for printer errors and critical events
- Configurable via `/settings/printer` admin interface in Gotify Notifications section
- Supports high-priority notifications (priority 8) for printer errors
- 5-minute cooldown period to prevent notification spam
- Monitors multiple error types: paper jams, no paper, low/no ink, offline printer, connection issues
- Automatic error classification with appropriate emojis and messaging
- Test functionality for connection verification and printer error simulation
- Built-in connection status monitoring and health checks

### Production Deployment
- Single installation script (install.sh) handles complete setup
- Systemd service for automatic startup
- Nginx handles HTTPS termination and static file serving
- WiFi access point configured for isolated network
- Supports up to 10 concurrent users