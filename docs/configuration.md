# Configuration Guide

This guide covers all configuration options for the PhotoBooth system, from basic settings to advanced customization.

## Configuration Files Overview

### Environment Variables (.env)
Primary configuration file located at `/opt/photobooth/.env`:
```bash
# WiFi Access Point Settings
AP_SSID=PhotoBooth
AP_PASSWORD=photobooth123

# Admin Interface Security
SETTINGS_PASSWORD=admin123

# Photo Processing
PHOTO_WIDTH=1800
PHOTO_HEIGHT=1200
PHOTO_QUALITY=85

# Text-to-Speech
TTS_ENABLED=true
TTS_VOICE=en+f3
TTS_RATE=150

# SMS Configuration
SMS_ENABLED=false
SMS_GATE_HOST=
SMS_GATE_PORT=8080
SMS_GATE_USERNAME=
SMS_GATE_PASSWORD=

# Database
DATABASE_PATH=data/photobooth.db

# Application Settings
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### Configuration Classes (config.py)
Flask configuration with environment-specific settings:
- **DevelopmentConfig**: Debug mode, verbose logging
- **ProductionConfig**: Optimized for Raspberry Pi deployment
- **TestingConfig**: For automated testing

## WiFi Hotspot Configuration

### Basic Settings
Change WiFi network name and password:
```bash
sudo nano /opt/photobooth/.env
```

Update these values:
```bash
AP_SSID=YourWeddingName2024
AP_PASSWORD=your-secure-password
```

Restart hotspot services:
```bash
sudo systemctl restart hostapd dnsmasq
```

### Advanced Network Configuration

#### Hostapd Configuration (/etc/hostapd/hostapd.conf)
```bash
interface=wlan0
driver=nl80211
ssid=PhotoBooth
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=photobooth123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

**Key parameters:**
- **channel**: WiFi channel (1-11 for 2.4GHz)
- **hw_mode**: g=2.4GHz, a=5GHz (Pi 3B supports g only)
- **wpa**: 2 for WPA2 security
- **ignore_broadcast_ssid**: 0=visible, 1=hidden network

#### DHCP Configuration (/etc/dnsmasq.conf)
```bash
interface=wlan0
dhcp-range=192.168.50.50,192.168.50.150,255.255.255.0,24h
domain=local
address=/photobooth.local/192.168.50.1
dhcp-option=3,192.168.50.1
dhcp-option=6,192.168.50.1
```

**Key parameters:**
- **dhcp-range**: IP pool for connected devices
- **domain**: Local domain name
- **dhcp-option=3**: Default gateway
- **dhcp-option=6**: DNS server

### Internet Sharing
To share internet via ethernet connection:

1. **Enable IP forwarding:**
   ```bash
   echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
   ```

2. **Configure iptables:**
   ```bash
   sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
   sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
   sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
   ```

3. **Save iptables rules:**
   ```bash
   sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
   ```

## Photo Settings Configuration

### Image Quality Settings
Balance quality vs. Pi 3B performance:

```bash
# High Quality (slower processing)
PHOTO_WIDTH=2400
PHOTO_HEIGHT=1600
PHOTO_QUALITY=95

# Balanced (recommended)
PHOTO_WIDTH=1800
PHOTO_HEIGHT=1200
PHOTO_QUALITY=85

# Performance (faster processing)
PHOTO_WIDTH=1200
PHOTO_HEIGHT=800
PHOTO_QUALITY=75
```

### Storage Configuration
Configure photo storage paths:
```bash
# In .env file
PHOTO_STORAGE_PATH=data/photos
THUMBNAIL_PATH=data/photos/thumbnails
BACKUP_PATH=data/photos/printed
```

### Frame Overlay Settings
Frame system configuration:
```bash
# Maximum frame file size (bytes)
MAX_FRAME_SIZE=10485760  # 10MB

# Frame overlay opacity (0.0-1.0)
FRAME_OPACITY=1.0

# Frame caching
FRAME_CACHE_ENABLED=true
```

## Printer Configuration

### CUPS Integration
Basic printer setup via CUPS:

1. **Access CUPS web interface:**
   ```
   http://192.168.50.1:631
   ```

2. **Add printer:**
   - Administration → Add Printer
   - Select USB printer
   - Configure paper size and quality

3. **Set default printer in PhotoBooth:**
   - Settings → Printer section
   - Select from dropdown
   - Test print

### Print Job Settings
Configure print behavior:
```bash
# In .env file
PRINT_PAPER_SIZE=4x6
PRINT_DPI=300
PRINT_ORIENTATION=portrait
PRINT_QUALITY=high
PRINT_COPIES=1

# Print queue settings
MAX_PRINT_QUEUE=50
PRINT_TIMEOUT=300  # seconds
RETRY_FAILED_PRINTS=true
```

### Printer-Specific Configuration

#### Canon SELPHY CP Series
```bash
# Optimal settings for Canon SELPHY
PRINT_PAPER_SIZE=Postcard
PRINT_QUALITY=normal
PRINT_BORDERLESS=true
```

#### HP DeskJet Series
```bash
# Optimal settings for HP DeskJet
PRINT_PAPER_SIZE=4x6
PRINT_QUALITY=best
PRINT_MEDIA_TYPE=photo
```

## Audio & Text-to-Speech Configuration

### TTS Settings
Configure speech synthesis:
```bash
# Basic TTS settings
TTS_ENABLED=true
TTS_VOICE=en+f3
TTS_RATE=150
TTS_VOLUME=0.8

# Advanced TTS settings
TTS_PITCH=50
TTS_WORD_GAP=10
TTS_SENTENCE_GAP=100
```

### Available Voices
eSpeak NG voice options:
- **en**: English (default)
- **en+f3**: English female voice 3
- **en+m4**: English male voice 4
- **en-us**: American English
- **en-gb**: British English

### Custom Messages
Configure countdown and status messages:
```python
# In photobooth/audio.py
MESSAGES = {
    'welcome': "Welcome to our PhotoBooth!",
    'countdown': "Get ready... {count}",
    'capture': "Perfect! Your photo is ready!",
    'printing': "Your photo is printing!",
    'sms_sent': "Photo sent successfully!"
}
```

### Audio Hardware
Configure audio output:
```bash
# Set default audio device
sudo raspi-config
# Advanced Options → Audio → Force 3.5mm jack

# Test audio output
speaker-test -t wav -c 2

# Adjust volume
alsamixer
```

## SMS Configuration

### SMS-Gate Setup
Configure SMS photo sharing:

1. **Install SMS-Gate on Android device**
2. **Configure SMS-Gate app:**
   - Set server port (default: 8080)
   - Create username/password
   - Note device IP address

3. **Update PhotoBooth settings:**
   ```bash
   SMS_ENABLED=true
   SMS_GATE_HOST=192.168.50.101
   SMS_GATE_PORT=8080
   SMS_GATE_USERNAME=photobooth
   SMS_GATE_PASSWORD=your-sms-password
   ```

### ImgBB Configuration
Image hosting for SMS sharing:
```bash
# ImgBB API settings
IMGBB_API_KEY=your-imgbb-api-key
IMGBB_EXPIRATION=86400  # 24 hours in seconds
IMGBB_UPLOAD_URL=https://api.imgbb.com/1/upload
```

### Country Code Support
Configure supported countries for SMS:
```python
# In photobooth/sms.py
SUPPORTED_COUNTRIES = [
    {'code': 'US', 'name': 'United States', 'prefix': '+1'},
    {'code': 'CA', 'name': 'Canada', 'prefix': '+1'},
    {'code': 'GB', 'name': 'United Kingdom', 'prefix': '+44'},
    {'code': 'AU', 'name': 'Australia', 'prefix': '+61'},
    # Add more as needed
]
```

## Security Configuration

### Admin Access
Configure admin interface security:
```bash
# Strong password requirements
SETTINGS_PASSWORD=YourSecureAdminPassword123!

# Session configuration
SESSION_TIMEOUT=3600  # 1 hour
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
```

### TLS/SSL Configuration
HTTPS certificate settings:
```bash
# Certificate paths
SSL_CERT_PATH=/opt/photobooth/certs/photobooth.crt
SSL_KEY_PATH=/opt/photobooth/certs/photobooth.key

# SSL security settings
SSL_PROTOCOLS=TLSv1.2 TLSv1.3
SSL_CIPHERS=ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS
```

### Input Validation
Configure security filters:
```bash
# File upload restrictions
MAX_CONTENT_LENGTH=16777216  # 16MB
ALLOWED_EXTENSIONS=png,jpg,jpeg

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

## Database Configuration

### SQLite Settings
Database configuration:
```bash
# Database file location
DATABASE_PATH=data/photobooth.db

# Connection settings
DB_TIMEOUT=30
DB_WAL_MODE=true
DB_JOURNAL_MODE=WAL
```

### Backup Configuration
Automatic database backups:
```bash
# Backup settings
BACKUP_ENABLED=true
BACKUP_INTERVAL=3600  # 1 hour
BACKUP_RETENTION=168  # 1 week in hours
BACKUP_PATH=data/backups
```

## Performance Configuration

### Memory Management
Optimize for Raspberry Pi 3B:
```bash
# Memory settings
MAX_MEMORY_USAGE=512MB
THUMBNAIL_CACHE_SIZE=100
IMAGE_CACHE_SIZE=50

# Garbage collection
GC_THRESHOLD_0=700
GC_THRESHOLD_1=10
GC_THRESHOLD_2=10
```

### Processing Optimization
CPU and I/O optimization:
```bash
# Image processing
JPEG_OPTIMIZE=true
PNG_COMPRESS_LEVEL=6
THUMBNAIL_QUALITY=80

# Async processing
ENABLE_ASYNC_PROCESSING=true
WORKER_THREADS=2
QUEUE_SIZE=100
```

## Logging Configuration

### Log Levels
Configure application logging:
```bash
# Log configuration
LOG_LEVEL=INFO
LOG_FILE=photobooth.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# Component-specific logging
FLASK_LOG_LEVEL=WARNING
CUPS_LOG_LEVEL=ERROR
TTS_LOG_LEVEL=INFO
```

### Log Rotation
Automatic log management:
```bash
# Logrotate configuration
ROTATE_LOGS=true
ROTATE_SIZE=10MB
ROTATE_DAILY=true
KEEP_LOGS=7  # days
```

## Development Configuration

### Debug Settings
For development and troubleshooting:
```bash
# Development mode
FLASK_ENV=development
DEBUG=true
TESTING=false

# Debug features
SHOW_DEBUG_INFO=true
ENABLE_PROFILING=true
VERBOSE_LOGGING=true
```

### Testing Configuration
Test environment settings:
```bash
# Test database
TEST_DATABASE_PATH=test_photobooth.db

# Mock services
MOCK_PRINTER=true
MOCK_TTS=true
MOCK_SMS=true

# Test data
TEST_DATA_PATH=tests/data
```

## Backup and Restore

### Configuration Backup
Backup all configuration:
```bash
# Create backup
sudo tar -czf photobooth-config-backup.tar.gz \
  /opt/photobooth/.env \
  /opt/photobooth/data/photobooth.db \
  /etc/hostapd/hostapd.conf \
  /etc/dnsmasq.conf \
  /etc/nginx/sites-available/photobooth
```

### Configuration Restore
Restore from backup:
```bash
# Extract backup
sudo tar -xzf photobooth-config-backup.tar.gz -C /

# Restart services
sudo systemctl restart photobooth nginx hostapd dnsmasq
```

## Configuration Validation

### Syntax Checking
Validate configuration files:
```bash
# Check nginx configuration
sudo nginx -t

# Check systemd service
sudo systemd-analyze verify photobooth.service

# Check hostapd configuration
sudo hostapd -dd /etc/hostapd/hostapd.conf
```

### Configuration Testing
Test configuration changes:
```bash
# Test WiFi hotspot
sudo hostapd -dd /etc/hostapd/hostapd.conf

# Test application config
cd /opt/photobooth
source venv/bin/activate
python -c "from config import config; print(config['production'].__dict__)"
```

## Troubleshooting Configuration

### Common Issues

**Environment variables not loading:**
```bash
# Check .env file syntax
cat /opt/photobooth/.env

# Verify permissions
ls -la /opt/photobooth/.env

# Test loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AP_SSID'))"
```

**WiFi hotspot configuration errors:**
```bash
# Check hostapd logs
sudo journalctl -u hostapd -f

# Validate configuration
sudo hostapd -dd /etc/hostapd/hostapd.conf
```

**Database configuration issues:**
```bash
# Check database permissions
ls -la /opt/photobooth/data/

# Test database connection
sqlite3 /opt/photobooth/data/photobooth.db "SELECT COUNT(*) FROM photos;"
```

### Configuration Reset
Reset to default configuration:
```bash
# Backup current config
sudo cp /opt/photobooth/.env /opt/photobooth/.env.backup

# Restore defaults
sudo cp /opt/photobooth/.env.example /opt/photobooth/.env

# Restart services
sudo systemctl restart photobooth
```