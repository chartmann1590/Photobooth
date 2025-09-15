# Installation Guide

This guide covers the complete installation process for the PhotoBooth application on Raspberry Pi 3B.

## Prerequisites

### Hardware Requirements
- **Raspberry Pi 3B** (minimum) or newer model
- **16GB+ microSD card** (Class 10 U1 recommended for better performance)
- **2.5A power supply** (official Raspberry Pi PSU recommended)
- **USB printer** (optional but recommended for full functionality)
- **Ethernet cable** (optional, for internet sharing during events)

### Software Requirements
- **Fresh Raspberry Pi OS** (Debian 11+ based)
- **Internet connection** during installation only
- **SSH access** or direct terminal access to the Pi

### Tested Hardware
- **Raspberry Pi**: 3B, 3B+, 4B (all models supported)
- **Printers**: Canon SELPHY CP series, HP DeskJet, Epson photo printers
- **Storage**: SanDisk Ultra, Samsung EVO Select microSD cards
- **Network**: 2.4GHz WiFi support (Pi 3B limitation)

## Quick Installation

### One-Command Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chartmann1590/Photobooth.git photobooth
   cd photobooth
   ```

2. **Run the automated installer:**
   ```bash
   sudo bash install.sh
   ```

3. **Wait for completion** (15-30 minutes depending on internet speed)

4. **Reboot the system:**
   ```bash
   sudo reboot
   ```

That's it! The PhotoBooth is ready to use.

## What the Installer Does

The `install.sh` script automatically handles:

### System Packages
- **nginx** - HTTPS reverse proxy server
- **hostapd** - WiFi access point daemon
- **dnsmasq** - DNS and DHCP server for the hotspot
- **cups** - Common Unix Printing System
- **espeak-ng** - Text-to-speech engine
- **mkcert** - Local certificate authority for HTTPS

### Python Environment
- Creates isolated virtual environment at `/opt/photobooth/venv`
- Installs all Python dependencies from `requirements.txt`
- Sets up proper permissions for the photobooth user

### Network Configuration
- Configures WiFi access point with SSID "PhotoBooth"
- Sets up DHCP server on 192.168.50.0/24 network
- Enables packet forwarding for internet sharing (optional)
- Configures iptables rules for NAT

### TLS Certificates
- Generates local CA certificate using mkcert
- Creates HTTPS certificate for 192.168.50.1
- Installs certificates for nginx HTTPS support

### Service Installation
- Creates systemd service for PhotoBooth application
- Enables auto-start on boot for all required services
- Sets up proper service dependencies

### Directory Structure
- Creates `/opt/photobooth/` application directory
- Sets up `data/photos/` storage directories
- Initializes SQLite database with proper schema
- Configures log file rotation

## Post-Installation Setup

### Access Information
After installation, the system provides:
- **WiFi Network**: `PhotoBooth`
- **WiFi Password**: `photobooth123`
- **PhotoBooth URL**: `https://192.168.50.1/`
- **Settings URL**: `https://192.168.50.1/settings`
- **Settings Password**: `admin123`

### First-Time Configuration

#### 1. Trust TLS Certificate
Each device needs to trust the self-signed certificate:

**iOS Devices:**
1. Connect to PhotoBooth WiFi
2. Open Safari and go to `https://192.168.50.1/`
3. Tap "Continue" on certificate warning
4. Go to Settings → General → VPN & Device Management
5. Find "mkcert" profile and tap "Install"
6. Enter device passcode and confirm installation

**Android Devices:**
1. Connect to PhotoBooth WiFi
2. Open Chrome and go to `https://192.168.50.1/`
3. Tap "Advanced" then "Proceed to 192.168.50.1"
4. Certificate will be automatically accepted

#### 2. Printer Setup
If you have a USB printer:
1. Connect printer to Raspberry Pi via USB
2. Go to `https://192.168.50.1/settings`
3. Navigate to Printer section
4. Your printer should appear in the dropdown
5. Select it and click "Set as Default"
6. Run a test print to verify functionality

**Manual Printer Setup (if auto-detection fails):**
1. Access CUPS web interface: `http://192.168.50.1:631`
2. Click Administration → Add Printer
3. Log in with system credentials
4. Follow the printer setup wizard
5. Return to PhotoBooth settings to select the printer

#### 3. Frame Overlay (Optional)
To add custom wedding frames:
1. Prepare PNG image with transparency (1800×1200 pixels recommended)
2. Go to Settings → Frame section
3. Upload your frame image
4. Preview the result
5. Save the configuration

## Advanced Installation Options

### Custom Configuration During Install

Before running `install.sh`, you can customize settings by editing `.env.example`:

```bash
cp .env.example .env
nano .env
```

**Key settings to customize:**
```bash
# WiFi Access Point
AP_SSID=YourWeddingName
AP_PASSWORD=your-secure-password

# Admin Access
SETTINGS_PASSWORD=your-admin-password

# Photo Quality (balance quality vs Pi 3B performance)
PHOTO_WIDTH=1800
PHOTO_HEIGHT=1200
PHOTO_QUALITY=85

# Text-to-Speech
TTS_ENABLED=true
TTS_VOICE=en+f3
TTS_RATE=150
```

### Manual Installation Steps

If you prefer to install manually or need to troubleshoot:

#### 1. System Packages
```bash
sudo apt update
sudo apt install -y nginx hostapd dnsmasq cups espeak-ng python3-venv python3-pip git
```

#### 2. Application Setup
```bash
sudo mkdir -p /opt/photobooth
sudo chown pi:pi /opt/photobooth
cd /opt/photobooth
git clone https://github.com/chartmann1590/Photobooth.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configuration Files
```bash
# Copy service configurations
sudo cp services/photobooth.service /etc/systemd/system/
sudo cp services/nginx.site /etc/nginx/sites-available/photobooth
sudo cp services/hostapd.conf /etc/hostapd/hostapd.conf
sudo cp services/dnsmasq.conf /etc/dnsmasq.conf

# Enable services
sudo systemctl enable photobooth nginx hostapd dnsmasq cups
```

#### 4. Network Configuration
```bash
# Configure hostapd
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee -a /etc/default/hostapd

# Configure wlan0 interface
sudo tee -a /etc/dhcpcd.conf << EOF
interface wlan0
static ip_address=192.168.50.1/24
nohook wpa_supplicant
EOF
```

#### 5. Generate Certificates
```bash
cd /opt/photobooth
bash services/mkcert.sh
```

#### 6. Initialize Database
```bash
cd /opt/photobooth
source venv/bin/activate
python -c "from photobooth.models import init_db; init_db('data/photobooth.db')"
```

## Verification

### Service Status Check
```bash
sudo systemctl status photobooth nginx hostapd dnsmasq
```

All services should show "active (running)" status.

### Network Verification
```bash
# Check WiFi interface
iwconfig wlan0

# Check DHCP leases
cat /var/lib/dhcp/dhcpd.leases

# Test local access
curl -k https://192.168.50.1/healthz
```

### Application Test
1. Connect device to PhotoBooth WiFi
2. Navigate to `https://192.168.50.1/`
3. Allow camera access
4. Take a test photo
5. Verify photo appears in gallery

## Troubleshooting Installation

### Common Issues

**Installation script fails:**
```bash
# Check internet connection
ping google.com

# Check available disk space
df -h

# Re-run with verbose output
sudo bash -x install.sh
```

**Services won't start:**
```bash
# Check service logs
sudo journalctl -u photobooth -f
sudo journalctl -u hostapd -f

# Check configuration syntax
sudo nginx -t
```

**WiFi hotspot not broadcasting:**
```bash
# Check WiFi is unblocked
sudo rfkill unblock wlan

# Restart network services
sudo systemctl restart hostapd dnsmasq
```

**Cannot access web interface:**
```bash
# Check nginx is running
sudo systemctl status nginx

# Check firewall
sudo ufw status

# Test local connection
curl -k https://localhost:5000/healthz
```

### Getting Help

If you encounter issues during installation:

1. **Check the logs** first:
   ```bash
   tail -f /opt/photobooth/photobooth.log
   sudo journalctl -u photobooth -f
   ```

2. **Verify system requirements** are met
3. **Try the manual installation** steps if automated install fails
4. **Document the error** and check GitHub issues

## Next Steps

After successful installation:
1. **Review** the [Configuration Guide](configuration.md)
2. **Test** all features using the [Features Guide](features.md)
3. **Prepare** for your event with the [Production Checklist](production-checklist.md)
4. **Set up SMS sharing** with the [SMS Setup Guide](sms-setup.md)