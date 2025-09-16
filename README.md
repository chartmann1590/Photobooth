# Wedding PhotoBooth for Raspberry Pi 3B

**Repository**: https://github.com/chartmann1590/Photobooth.git

A complete, production-ready wedding photobooth system that runs directly on Raspberry Pi 3B with offline WiFi hotspot, professional printing, HTTPS certificate support, and beautiful touch-friendly interface designed for dark venues.

## ✨ Key Features

### 🎯 Core PhotoBooth Functionality
- **Full-screen camera interface** with visual countdown (3-2-1) and audio prompts
- **Instant photo capture** via WebRTC (front/back camera toggle)
- **PNG frame overlay system** - upload transparent frames for branding
- **Professional printing** via CUPS integration (4×6" optimized)
- **Print/SMS/Retake workflow** with instant preview and three sharing options
- **Gallery management** with thumbnails and reprint functionality

### 🌐 Complete Offline WiFi System
- **Captive portal hotspot** - creates "PhotoBooth" network
- **Self-contained system** - no internet required to operate
- **HTTPS with local TLS certificates** for iOS Safari camera access
- **Multi-device support** - up to 10 concurrent users
- **NAT routing** with optional internet forwarding via ethernet

### 🎨 Wedding-Optimized UI
- **Mobile-first responsive design** optimized for iPad/phone in dark venues
- **Large, obvious touch controls** for guest-friendly operation
- **Elegant wedding theme** with tasteful animations
- **Accessibility support** with high contrast and keyboard navigation
- **Two interfaces only**: `/booth` (guest UI) and `/settings` (admin UI)

### 🖨️ Professional Printing
- **USB printer support** with CUPS integration
- **Auto-detection** of connected printers
- **4×6" photo optimization** (1800×1200 @ 300 DPI)
- **Print queue management** and reprint capability
- **Test printing** from admin interface

### 🔊 Audio & TTS Integration
- **eSpeak NG text-to-speech** for countdown announcements
- **Non-blocking audio** - "Get ready... 3... 2... 1... Smile!"
- **Customizable voice** and speech rate
- **Audio feedback** for user actions and SMS notifications

### 📱 SMS Photo Sharing with Audio Feedback
- **Instant photo sharing** via SMS directly from booth interface after capture
- **Three-option workflow**: Print, Send SMS, or Retake after each photo
- **Dual image hosting**: 0x0.st (primary, no API key) with ImgBB fallback (24-hour expiration)
- **Wedding-themed messaging**: Automated "💒 Greetings from the Wedding PhotoBooth! 📸" introduction
- **Audio alerts**: "SMS sent successfully!" or "SMS sending failed. Please try again."
- **Local SMS gateway** integration with [SMS-Gate](https://docs.sms-gate.app/)
- **Admin configuration** for SMS gateway settings with health monitoring
- **Message tracking** and delivery statistics

### 🔔 Gotify Real-Time Notifications
- **Instant printer error alerts** via [Gotify](https://gotify.net/) push notifications
- **High-priority notifications** (priority 8) for critical printer issues
- **Smart error classification**: paper jams, no paper, low/no ink, offline printer, connection issues
- **Spam prevention** with 5-minute cooldown per error type
- **Rich messaging** with contextual emojis and detailed error information
- **Connection monitoring** with admin interface status checks
- **Test functionality** for notification verification and printer error simulation
- **Zero-configuration**: works with any Gotify server on your network

### 📱 Mobile App Experience
- **Wedding-themed favicon** with camera, heart, and rings design
- **PWA support** - add to iPad homescreen for app-like experience  
- **Apple Touch Icon** optimized for mobile devices
- **Responsive design** for all screen sizes
- **Privacy-conscious** with automatic image expiration

### ⚙️ Admin Controls
- **Password-protected settings** page
- **Frame overlay upload** with PNG validation
- **Printer configuration** and testing
- **Photo gallery** with download/delete/reprint
- **SMS gateway configuration** and testing
- **Gotify notification setup** with connection testing and error simulation
- **System monitoring** and service status
- **Hotspot configuration** (SSID/password changes)

## 🚀 Complete Installation

### Prerequisites
- **Raspberry Pi 3B** running fresh Raspberry Pi OS (Raspbian)
- **16GB+ microSD** card (Class 10 recommended)
- **USB printer** (optional but recommended)
- **Internet connection** during installation only

### One-Command Installation

1. **Download and run the installer:**
   ```bash
   git clone https://github.com/chartmann1590/Photobooth.git photobooth
   cd photobooth
   sudo bash install.sh
   ```

2. **Wait for completion** (15-30 minutes depending on internet speed)

3. **Reboot the system:**
   ```bash
   sudo reboot
   ```

That's it! The installer automatically handles:
- All system packages (nginx, hostapd, dnsmasq, CUPS, eSpeak NG)
- Python virtual environment and dependencies
- TLS certificate generation
- WiFi access point configuration
- Service installation and startup
- Database initialization
- Directory structure and permissions

### Post-Installation Access

- **WiFi Network**: `PhotoBooth`
- **WiFi Password**: `photobooth123`
- **PhotoBooth URL**: `https://192.168.50.1/`
- **Settings URL**: `https://192.168.50.1/settings`
- **Settings Password**: `admin123`

### First Time Setup

1. **Trust the TLS certificate** on your devices:
   - iOS: Settings → General → VPN & Device Management → Install Profile
   - Android: Chrome will prompt to accept certificate
   - See `/opt/photobooth/scripts/trust_cert_instructions.md` for detailed steps

2. **Configure your printer** (if you have one):
   - Plug USB printer into Raspberry Pi
   - Go to `https://192.168.50.1/settings` → Printer section
   - Your printer should be auto-detected
   - Select it as default and run a test print

3. **Upload a custom frame overlay** (optional):
   - Go to Settings → Frame section
   - Upload PNG with transparency (1800×1200 recommended)
   - Preview and save

4. **Test the PhotoBooth:**
   - Go to `https://192.168.50.1/` (main booth interface)
   - Allow camera access when prompted
   - Take a test photo and try printing!

## ⚙️ Configuration & Customization

### Change WiFi Network Settings

Edit `/opt/photobooth/.env` file:
```bash
AP_SSID=PhotoBooth
AP_PASSWORD=your-secure-password
```

Then restart the hotspot:
```bash
sudo systemctl restart hostapd dnsmasq
```

### Customize PhotoBooth Settings

Edit `/opt/photobooth/.env`:
```bash
# Security
SETTINGS_PASSWORD=your-admin-password

# Photo Quality (balance quality vs RPi 3B performance)
PHOTO_WIDTH=1800
PHOTO_HEIGHT=1200
PHOTO_QUALITY=85

# Printing
PRINT_PAPER_SIZE=4x6
PRINT_DPI=300

# Audio/TTS
TTS_ENABLED=true
TTS_VOICE=en+f3
TTS_RATE=150
```

Then restart the application:
```bash
sudo systemctl restart photobooth
```

### USB Printer Setup

1. **Connect printer via USB** to Raspberry Pi
2. **Auto-detection**: Most printers are detected automatically
3. **Manual setup** (if needed):
   - Access CUPS at `http://192.168.50.1:631`
   - Administration → Add Printer
   - Follow the setup wizard
4. **Configure in PhotoBooth**:
   - Go to Settings → Printer
   - Select default printer
   - Run test print

**Tested printer types:**
- **Canon SELPHY** CP series (photo printers)
- **HP DeskJet** series with photo paper
- **Epson** photo and inkjet printers
- Most USB printers with Linux drivers

### Custom Frame Overlays

Create wedding-branded frames:

**Requirements:**
- **Format:** PNG with transparency
- **Size:** 1800×1200 pixels (matches photo dimensions)
- **Design areas:** Transparent center for photo, decorated borders

**Design tips:**
- Use wedding colors and theme
- Include couple names and date
- Add venue name or hashtag
- Keep center area clear for faces
- Test transparency on sample photos

**Upload via Settings → Frame section**

### SMS Photo Sharing Setup

Enable guests to share photos instantly via SMS:

**Prerequisites:**
- **Android device** (phone/tablet) with SMS capability
- **SMS-Gate app** installed from [SMS-Gate releases](https://github.com/capcom6/sms-gate/releases)
- **Same network** as PhotoBooth system

**Quick Setup:**
1. **Install SMS-Gate** on Android device
2. **Configure SMS-Gate server** and note IP address
3. **Access PhotoBooth Settings** → SMS section
4. **Enter gateway details**:
   - Host/IP: `192.168.50.XXX:8080` (SMS-Gate device IP)
   - Username/Password: As configured in SMS-Gate
5. **Test connection** using built-in test button

**How it works:**
- After taking a photo, guests see three options: Print, Send SMS, or Retake
- Guests click "Send SMS" to share the photo instantly
- Photo uploads to [ImgBB](https://imgbb.com/) (free, 24-hour hosting)
- SMS sent with photo URL via local SMS-Gate server
- No external SMS services or fees required
- Also available from admin gallery for any saved photo

**Documentation:** See `docs/sms_photo_sharing.md` for complete setup guide

## 🛠️ System Management

### Service Control

**Main PhotoBooth service:**
```bash
sudo systemctl start photobooth    # Start
sudo systemctl stop photobooth     # Stop
sudo systemctl restart photobooth  # Restart
sudo systemctl status photobooth   # Check status
```

**All related services:**
```bash
# Start all services
sudo systemctl start photobooth nginx hostapd dnsmasq cups

# Check status of all services
sudo systemctl status photobooth nginx hostapd dnsmasq
```

### Logs and Monitoring

```bash
# PhotoBooth application logs
tail -f /opt/photobooth/photobooth.log

# System service logs
sudo journalctl -u photobooth -f
sudo journalctl -u hostapd -f
sudo journalctl -u nginx -f

# Check disk space
df -h
```

### Performance Optimization

**For Raspberry Pi 3B:**

1. **Increase GPU memory:**
   ```bash
   sudo raspi-config
   # Advanced Options → Memory Split → 128
   ```

2. **Disable unnecessary services:**
   ```bash
   sudo systemctl disable bluetooth
   sudo systemctl disable avahi-daemon
   ```

### Backup Important Data

```bash
# Backup photos
sudo cp -r /opt/photobooth/data/photos /your-backup-location/

# Backup configuration
sudo cp /opt/photobooth/.env /your-backup-location/
sudo cp /opt/photobooth/data/photobooth.db /your-backup-location/
```

## 🐛 Troubleshooting

### Camera Access Issues

**iOS Safari (most important):**
1. Connect to WiFi network
2. Go to `https://192.168.50.1/`
3. Trust certificate when prompted (Settings → General → VPN & Device Management)
4. Return to Safari and allow camera access
5. Use full-screen mode for best experience

**Android Chrome:**
1. Accept certificate warning when prompted
2. Allow camera access in browser permissions
3. Ensure microphone isn't blocking camera

**General tips:**
- **HTTPS is required** for camera access (never use HTTP)
- Camera requires **user gesture** (button tap) to activate
- Try different browsers if issues persist

### Printer Issues

**Printer not detected:**
```bash
# Check USB connection
lsusb

# Check CUPS status
sudo systemctl status cups
lpstat -p

# Restart CUPS
sudo systemctl restart cups
```

**Manual printer setup:**
1. Access CUPS web interface: `http://192.168.50.1:631`
2. Administration → Add Printer
3. Follow setup wizard
4. Test print from PhotoBooth settings

### WiFi Hotspot Issues

**Hotspot not broadcasting:**
```bash
# Check service status
sudo systemctl status hostapd dnsmasq

# Check WiFi interface
iwconfig wlan0

# Restart hotspot services
sudo systemctl restart hostapd dnsmasq

# Unblock WiFi if needed
sudo rfkill unblock wlan
```

**Clients can't connect:**
```bash
# Check DHCP lease file
cat /var/lib/dhcp/dhcpd.leases

# Restart networking
sudo systemctl restart dhcpcd
```

### Performance Issues

**Photos loading slowly:**
- Reduce `PHOTO_QUALITY` in `.env` (try 75 instead of 85)
- Increase GPU memory split to 128MB
- Use faster microSD card (Class 10 or better)

**General slowness:**
```bash
# Check system resources
htop
df -h

# Disable unnecessary services
sudo systemctl disable bluetooth avahi-daemon
```

## 🎯 Production Event Checklist

### Pre-Event Testing (1-2 weeks before)

- [ ] **Change default passwords** (WiFi: `photobooth123`, Settings: `admin123`)
- [ ] **Upload custom frame** with couple names/date/venue
- [ ] **Test printer** with actual photo paper (not plain paper)
- [ ] **Configure SMS sharing** (optional but recommended for engagement)
- [ ] **Test SMS delivery** with real phone numbers
- [ ] **Test on guests' devices** (iOS/Android/tablets)
- [ ] **Verify certificate trust** on different device types
- [ ] **Test in low-light conditions** (dim venue lighting)
- [ ] **Check storage space** (8GB+ free recommended)
- [ ] **Backup system** (photos, config, database)
- [ ] **Prepare guest instructions** (WiFi name/password sign)

### Event Day Setup (30 minutes before)

1. **Power on Raspberry Pi** and wait for full boot
2. **Verify all services running:**
   ```bash
   sudo systemctl status photobooth nginx hostapd dnsmasq
   ```
3. **Test WiFi network** broadcasting and connection
4. **Test printer** with one photo print
5. **Test camera** on primary device type (iPad/phone)
6. **Test SMS functionality** if configured
7. **Verify frame overlay** appears correctly
8. **Check storage space** one final time
9. **Position system** away from interference sources

### Event Monitoring

- **Check system status** every 2-3 hours
- **Monitor photo count** and storage space
- **Clear paper jams** immediately if they occur
- **Have technical contact** available (phone number posted)
- **Backup photos periodically** during long events

## 📊 System Requirements & Performance

### Hardware Requirements
- **Raspberry Pi 3B** (minimum) or newer
- **16GB+ microSD** card (Class 10 U1 recommended)
- **USB printer** (Canon SELPHY, HP, Epson tested)
- **2.5A power supply** (official RPi PSU recommended)
- **Ethernet cable** (optional, for internet sharing)

### Performance Specifications
- **Photo processing**: ~3-5 seconds per photo (with frame overlay)
- **Concurrent users**: Up to 10 simultaneous connections
- **Print speed**: Depends on printer (typically 30-90 seconds)
- **Storage**: ~2MB per photo (1800×1200 @ 85% quality)
- **Network range**: ~30-50 feet (typical indoor WiFi)

### Expected Capacity
- **All-day wedding**: 200-500 photos typical
- **Storage for**: 1000+ photos on 16GB card
- **Print consumables**: Plan 1 print per 2-3 photos taken

## 📄 File Structure

```
/opt/photobooth/
├── app.py                    # Main Flask application
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables
├── run.sh                   # Production startup script
├── photobooth/              # Main application package
│   ├── routes_booth.py      # Guest booth interface
│   ├── routes_settings.py   # Admin settings interface
│   ├── models.py           # Database operations
│   ├── storage.py          # Photo file management
│   ├── printing.py         # CUPS integration
│   ├── imaging.py          # Image processing/frames
│   ├── audio.py            # Text-to-speech
│   ├── sms.py              # SMS photo sharing
│   ├── static/             # CSS, JavaScript, images
│   └── templates/          # HTML templates
├── services/               # System service configurations
│   ├── photobooth.service # Main app service
│   ├── nginx.site         # HTTPS reverse proxy
│   ├── hostapd.conf       # WiFi access point
│   ├── dnsmasq.conf       # DHCP/DNS
│   └── mkcert.sh          # Certificate generation
├── data/                  # Photo storage and database
│   ├── photos/all/        # All captured photos
│   ├── photos/printed/    # Backup of printed photos
│   └── photobooth.db      # SQLite database
├── docs/                  # Documentation
│   └── sms_photo_sharing.md # SMS feature documentation
└── scripts/               # Utility scripts
    └── trust_cert_instructions.md
```

## 💡 Tips for Success

1. **Test extensively** before the event - don't assume anything works
2. **Have a backup plan** - bring a regular camera just in case
3. **Post clear instructions** for guests (WiFi network info)
4. **Position strategically** - good lighting, away from interference
5. **Monitor actively** - check on system periodically during event
6. **Keep it simple** - the interface is designed to be intuitive
7. **Plan for prints** - bring extra photo paper and ink cartridges
8. **Have fun!** - This creates amazing memories for couples

---

*Built with ❤️ for unforgettable wedding moments*

## 📊 System Requirements

### Hardware
- **Raspberry Pi 3B** (minimum) or newer
- **16GB+ microSD** card (Class 10 recommended)
- **USB printer** (optional but recommended)
- **Power supply** 2.5A minimum
- **Ethernet cable** (optional, for internet sharing)

### Software
- **Raspberry Pi OS** (Debian 11+ based)
- **Python 3.9+**
- **Modern web browser** on client devices

### Network
- **2.4GHz WiFi** support (Pi 3B limitation)
- **Up to 10 concurrent** devices
- **Local network only** (unless ethernet connected)

## 📦 Project Structure

```
photobooth/
├── app.py                    # Main application entry point
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── install.sh               # One-click installation script
├── run.sh                   # Production run script
├── .env.example             # Environment variables template
├── photobooth/              # Main application package
│   ├── __init__.py
│   ├── routes_booth.py      # Main photobooth routes
│   ├── routes_settings.py   # Admin settings routes
│   ├── models.py           # Database models
│   ├── storage.py          # Photo storage management
│   ├── printing.py         # CUPS printing integration
│   ├── imaging.py          # Image processing & frames
│   ├── audio.py            # Text-to-speech functionality
│   ├── static/             # CSS, JS, images
│   └── templates/          # HTML templates
├── services/               # System service configurations
│   ├── photobooth.service # Systemd service
│   ├── nginx.site         # Nginx configuration
│   ├── hostapd.conf       # WiFi AP configuration
│   ├── dnsmasq.conf       # DNS/DHCP configuration
│   ├── sysctl_iptables.sh # Network routing
│   └── mkcert.sh          # Certificate generation
├── data/                   # Photo storage
│   ├── photos/all/        # All captured photos
│   └── photos/printed/    # Printed photos backup
└── scripts/               # Utility scripts
    ├── trust_cert_instructions.md
    └── regenerate_cert.sh
```

## 🤝 Contributing

This project is designed as a complete, self-contained solution. If you find issues or have improvements:

1. **Document the issue** with steps to reproduce
2. **Test thoroughly** on Raspberry Pi 3B
3. **Maintain compatibility** with the existing installation process
4. **Follow the wedding theme** design principles

## 📄 License

This project is released under the MIT License. Feel free to use it for your special day! 💕

## 💍 Credits

Created with love for couples celebrating their special moments. Perfect for:
- **Weddings** and receptions
- **Engagement parties**
- **Anniversary celebrations**
- **Bridal showers**
- **Any special event** deserving beautiful memories

---

*May your PhotoBooth capture all the joy and love of your special day! 💖*