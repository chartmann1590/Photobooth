# Troubleshooting Guide

This comprehensive guide covers common issues and their solutions for the PhotoBooth system.

## Quick Diagnostic Commands

### System Health Check
```bash
# Check all services status
sudo systemctl status photobooth nginx hostapd dnsmasq cups

# Check system resources
htop
df -h
free -h

# Check network interfaces
ip addr show
iwconfig

# Application health
curl -k https://localhost:5000/healthz
```

### Log Access
```bash
# PhotoBooth application logs
tail -f /opt/photobooth/photobooth.log

# System service logs
sudo journalctl -u photobooth -f
sudo journalctl -u nginx -f
sudo journalctl -u hostapd -f
sudo journalctl -u dnsmasq -f

# System logs
sudo dmesg | tail -20
```

## Installation Issues

### Installation Script Fails

**Symptoms:**
- `install.sh` exits with error
- Packages fail to install
- Service configuration errors

**Diagnostics:**
```bash
# Check internet connectivity
ping google.com

# Check available disk space (need 2GB+)
df -h

# Check system updates
sudo apt update
sudo apt list --upgradable
```

**Solutions:**
1. **Insufficient disk space:**
   ```bash
   # Clean package cache
   sudo apt clean
   sudo apt autoremove
   
   # Remove unnecessary files
   sudo rm -rf /var/log/*.log.1
   ```

2. **Network issues:**
   ```bash
   # Reset network configuration
   sudo systemctl restart networking
   
   # Try different DNS servers
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   ```

3. **Permission errors:**
   ```bash
   # Ensure running as sudo
   sudo bash install.sh
   
   # Check script permissions
   chmod +x install.sh
   ```

4. **Package installation failures:**
   ```bash
   # Update package list
   sudo apt update
   
   # Fix broken packages
   sudo apt --fix-broken install
   
   # Install packages individually
   sudo apt install nginx hostapd dnsmasq cups python3-venv
   ```

### Service Installation Issues

**Systemd service not starting:**
```bash
# Check service file syntax
sudo systemctl daemon-reload

# Check service configuration
sudo systemd-analyze verify /etc/systemd/system/photobooth.service

# Manual service start with debug
sudo -u pi /opt/photobooth/venv/bin/python /opt/photobooth/app.py
```

**Nginx configuration errors:**
```bash
# Test nginx configuration
sudo nginx -t

# Check site configuration
sudo nano /etc/nginx/sites-available/photobooth

# Remove default site if conflicting
sudo rm /etc/nginx/sites-enabled/default
```

## Network and WiFi Issues

### WiFi Hotspot Not Broadcasting

**Symptoms:**
- PhotoBooth network not visible
- Cannot connect to WiFi
- Connection immediately drops

**Diagnostics:**
```bash
# Check WiFi interface status
iwconfig wlan0

# Check hostapd service
sudo systemctl status hostapd
sudo journalctl -u hostapd -f

# Check if WiFi is blocked
sudo rfkill list
```

**Solutions:**
1. **WiFi interface issues:**
   ```bash
   # Unblock WiFi
   sudo rfkill unblock wlan
   
   # Restart WiFi interface
   sudo ip link set wlan0 down
   sudo ip link set wlan0 up
   
   # Check for interference
   sudo iwlist wlan0 scan | grep ESSID
   ```

2. **Hostapd configuration:**
   ```bash
   # Check configuration file
   sudo nano /etc/hostapd/hostapd.conf
   
   # Test configuration manually
   sudo hostapd -dd /etc/hostapd/hostapd.conf
   
   # Change WiFi channel if interference
   # Edit channel=7 to channel=1 or channel=11
   ```

3. **Service conflicts:**
   ```bash
   # Stop conflicting services
   sudo systemctl stop wpa_supplicant
   sudo systemctl disable wpa_supplicant
   
   # Restart hostapd
   sudo systemctl restart hostapd
   ```

### DHCP Issues

**Symptoms:**
- Devices connect but get no IP address
- Can't access PhotoBooth interface
- Limited connectivity warnings

**Diagnostics:**
```bash
# Check dnsmasq service
sudo systemctl status dnsmasq
sudo journalctl -u dnsmasq -f

# Check DHCP leases
cat /var/lib/dhcp/dhcpd.leases

# Check interface configuration
ip addr show wlan0
```

**Solutions:**
1. **DHCP configuration:**
   ```bash
   # Check dnsmasq configuration
   sudo nano /etc/dnsmasq.conf
   
   # Restart DHCP service
   sudo systemctl restart dnsmasq
   
   # Clear DHCP leases
   sudo rm /var/lib/dhcp/dhcpd.leases
   sudo systemctl restart dnsmasq
   ```

2. **IP address conflicts:**
   ```bash
   # Check for IP conflicts
   nmap -sn 192.168.50.0/24
   
   # Change DHCP range if needed
   sudo nano /etc/dnsmasq.conf
   # Modify: dhcp-range=192.168.50.100,192.168.50.200,255.255.255.0,24h
   ```

3. **Interface configuration:**
   ```bash
   # Check dhcpcd configuration
   sudo nano /etc/dhcpcd.conf
   
   # Ensure wlan0 static IP is set
   # interface wlan0
   # static ip_address=192.168.50.1/24
   # nohook wpa_supplicant
   ```

## Camera and Browser Issues

### Camera Access Denied

**Symptoms:**
- "Camera access denied" error
- Camera permission dialog doesn't appear
- Black screen instead of camera feed

**Diagnostics:**
```bash
# Check if HTTPS is working
curl -k https://192.168.50.1/

# Check certificate status
openssl s_client -connect 192.168.50.1:443 -servername 192.168.50.1
```

**Solutions:**
1. **HTTPS certificate issues (iOS):**
   - Go to Settings → General → VPN & Device Management
   - Find "mkcert" certificate profile
   - Tap "Install" and enter device passcode
   - Return to Safari and refresh page

2. **Browser-specific issues:**
   ```bash
   # Regenerate certificates if needed
   cd /opt/photobooth
   sudo bash services/mkcert.sh
   sudo systemctl restart nginx
   ```

3. **Camera permissions:**
   - Clear browser cache and cookies
   - Try incognito/private browsing mode
   - Ensure user gesture (button click) triggers camera

### Camera Not Working on Android

**Solutions:**
1. **Chrome permissions:**
   - Go to Chrome Settings → Privacy and Security → Site Settings
   - Find 192.168.50.1 and enable Camera
   - Try clearing site data and reconnecting

2. **Certificate acceptance:**
   - Navigate to https://192.168.50.1/
   - Tap "Advanced" → "Proceed to 192.168.50.1"
   - Camera should work after accepting certificate

## Printing Issues

### Printer Not Detected

**Symptoms:**
- No printers appear in settings dropdown
- "No printers found" message
- USB printer connected but not recognized

**Diagnostics:**
```bash
# Check USB devices
lsusb

# Check CUPS service
sudo systemctl status cups
lpstat -p
lpstat -a

# Check printer status
lpq
```

**Solutions:**
1. **USB connection:**
   ```bash
   # Check USB connection
   dmesg | grep -i usb
   
   # Try different USB port
   # Restart CUPS service
   sudo systemctl restart cups
   ```

2. **CUPS configuration:**
   ```bash
   # Access CUPS web interface
   # Navigate to http://192.168.50.1:631
   # Administration → Add Printer
   # Follow setup wizard
   ```

3. **Driver issues:**
   ```bash
   # Install additional printer drivers
   sudo apt install printer-driver-all
   sudo apt install cups-pdf
   
   # Restart CUPS
   sudo systemctl restart cups
   ```

### Print Jobs Fail

**Symptoms:**
- Photos sent to printer but nothing prints
- Print queue shows errors
- Printer reports errors

**Diagnostics:**
```bash
# Check print queue
lpq
lpstat -o

# Check printer status
lpstat -p -d

# View CUPS error logs
sudo journalctl -u cups -f
tail -f /var/log/cups/error_log
```

**Solutions:**
1. **Print queue issues:**
   ```bash
   # Clear print queue
   sudo cancel -a
   
   # Restart printer
   sudo cupsdisable printer-name
   sudo cupsenable printer-name
   ```

2. **Paper/ink issues:**
   - Check printer has paper loaded correctly
   - Verify ink/toner levels
   - Ensure correct paper size selected (4x6")

3. **Driver problems:**
   ```bash
   # Reinstall printer
   sudo lpadmin -x printer-name
   # Re-add through CUPS web interface
   ```

## Audio and TTS Issues

### Text-to-Speech Not Working

**Symptoms:**
- No audio during countdown
- TTS test button doesn't work
- Silent operation despite TTS enabled

**Diagnostics:**
```bash
# Test audio output
speaker-test -t wav -c 2

# Check audio devices
aplay -l

# Test eSpeak directly
espeak "Test message"

# Check TTS status in app
python -c "from photobooth.audio import get_tts_status; print(get_tts_status())"
```

**Solutions:**
1. **Audio output configuration:**
   ```bash
   # Force audio to 3.5mm jack
   sudo raspi-config
   # Advanced Options → Audio → Force 3.5mm jack
   
   # Or use amixer
   amixer cset numid=3 1
   ```

2. **eSpeak installation:**
   ```bash
   # Reinstall eSpeak
   sudo apt remove espeak-ng
   sudo apt install espeak-ng
   
   # Test installation
   espeak "Hello world"
   ```

3. **Volume settings:**
   ```bash
   # Adjust volume
   alsamixer
   
   # Or use amixer
   amixer set Master 80%
   ```

### Audio Device Issues

**Solutions:**
1. **USB audio devices:**
   ```bash
   # List audio devices
   cat /proc/asound/cards
   
   # Set default device
   sudo nano /etc/asound.conf
   # Add:
   # defaults.pcm.card 1
   # defaults.ctl.card 1
   ```

2. **Bluetooth audio:**
   ```bash
   # Disable Bluetooth if not needed
   sudo systemctl disable bluetooth
   sudo systemctl stop bluetooth
   ```

## SMS Sharing Issues

### SMS Gateway Connection Failed

**Symptoms:**
- "SMS gateway not reachable" error
- SMS test fails
- Photos can't be shared via SMS

**Diagnostics:**
```bash
# Check SMS-Gate device connectivity
ping 192.168.50.XXX  # SMS-Gate device IP

# Test SMS-Gate API
curl -X POST http://192.168.50.XXX:8080/api/send \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "message": "test"}'

# Check PhotoBooth SMS configuration
grep SMS /opt/photobooth/.env
```

**Solutions:**
1. **Network connectivity:**
   ```bash
   # Verify SMS-Gate device is on same network
   nmap -sn 192.168.50.0/24
   
   # Check SMS-Gate app settings on Android device
   # Ensure server is running and accessible
   ```

2. **Configuration issues:**
   ```bash
   # Update SMS settings in .env
   sudo nano /opt/photobooth/.env
   
   # Correct format:
   SMS_ENABLED=true
   SMS_GATE_HOST=192.168.50.101
   SMS_GATE_PORT=8080
   SMS_GATE_USERNAME=photobooth
   SMS_GATE_PASSWORD=your-password
   ```

3. **Firewall issues:**
   ```bash
   # Check if firewall is blocking
   sudo ufw status
   
   # Allow SMS-Gate port if needed
   sudo ufw allow 8080
   ```

### Image Upload Failures

**Symptoms:**
- "Failed to upload image" error
- SMS sharing starts but never completes
- ImgBB upload errors

**Solutions:**
1. **Internet connectivity:**
   ```bash
   # Check internet access (if available)
   ping imgbb.com
   
   # Test ImgBB API directly
   curl -X POST "https://api.imgbb.com/1/upload" \
     -F "image=@test_image.jpg" \
     -F "key=your-api-key"
   ```

2. **Image size issues:**
   ```bash
   # Check image file sizes
   ls -lh /opt/photobooth/data/photos/all/
   
   # Reduce photo quality if files too large
   sudo nano /opt/photobooth/.env
   # PHOTO_QUALITY=70
   ```

## Performance Issues

### Slow Photo Processing

**Symptoms:**
- Long delays after taking photos
- System becomes unresponsive
- Gallery loads slowly

**Diagnostics:**
```bash
# Check system resources
htop
iostat -x 1

# Check disk usage
df -h
du -sh /opt/photobooth/data/photos/

# Check memory usage
free -h
cat /proc/meminfo
```

**Solutions:**
1. **Memory optimization:**
   ```bash
   # Increase GPU memory split
   sudo raspi-config
   # Advanced Options → Memory Split → 128
   
   # Restart to apply
   sudo reboot
   ```

2. **Storage optimization:**
   ```bash
   # Clean old photos if storage full
   find /opt/photobooth/data/photos/all/ -mtime +30 -delete
   
   # Reduce photo quality
   sudo nano /opt/photobooth/.env
   # PHOTO_QUALITY=75
   ```

3. **System optimization:**
   ```bash
   # Disable unnecessary services
   sudo systemctl disable bluetooth
   sudo systemctl disable avahi-daemon
   
   # Update system
   sudo apt update && sudo apt upgrade
   ```

### High CPU Usage

**Solutions:**
1. **Process identification:**
   ```bash
   # Find CPU-intensive processes
   top -o %CPU
   
   # Check PhotoBooth processes
   ps aux | grep photobooth
   ```

2. **Application optimization:**
   ```bash
   # Reduce image processing quality
   sudo nano /opt/photobooth/.env
   # PHOTO_WIDTH=1200
   # PHOTO_HEIGHT=800
   
   # Restart application
   sudo systemctl restart photobooth
   ```

## Database Issues

### Database Corruption

**Symptoms:**
- "Database is locked" errors
- Gallery doesn't load
- Photos not saving

**Diagnostics:**
```bash
# Check database integrity
sqlite3 /opt/photobooth/data/photobooth.db "PRAGMA integrity_check;"

# Check database locks
lsof /opt/photobooth/data/photobooth.db

# Check database permissions
ls -la /opt/photobooth/data/photobooth.db
```

**Solutions:**
1. **Database repair:**
   ```bash
   # Stop application
   sudo systemctl stop photobooth
   
   # Backup database
   cp /opt/photobooth/data/photobooth.db /opt/photobooth/data/photobooth.db.backup
   
   # Repair database
   sqlite3 /opt/photobooth/data/photobooth.db "VACUUM;"
   
   # Restart application
   sudo systemctl start photobooth
   ```

2. **Restore from backup:**
   ```bash
   # Stop application
   sudo systemctl stop photobooth
   
   # Restore from latest backup
   cp /opt/photobooth/data/backups/photobooth.db.* /opt/photobooth/data/photobooth.db
   
   # Restart application
   sudo systemctl start photobooth
   ```

## System Recovery

### Complete System Reset

If multiple issues persist, perform complete reset:

1. **Backup important data:**
   ```bash
   # Backup photos
   sudo cp -r /opt/photobooth/data/photos /home/pi/photobooth-backup/
   
   # Backup configuration
   sudo cp /opt/photobooth/.env /home/pi/photobooth-backup/
   ```

2. **Reinstall application:**
   ```bash
   # Remove current installation
   sudo systemctl stop photobooth nginx hostapd dnsmasq
   sudo rm -rf /opt/photobooth
   
   # Run installer again
   cd /home/pi
   git clone https://github.com/chartmann1590/Photobooth.git photobooth
   cd photobooth
   sudo bash install.sh
   ```

3. **Restore data:**
   ```bash
   # Restore photos
   sudo cp -r /home/pi/photobooth-backup/photos/* /opt/photobooth/data/photos/
   
   # Restore configuration
   sudo cp /home/pi/photobooth-backup/.env /opt/photobooth/.env
   
   # Restart services
   sudo systemctl restart photobooth
   ```

### Emergency Recovery Mode

For critical system issues:

1. **Boot to recovery mode:**
   - Add `init=/bin/bash` to boot parameters
   - Mount filesystem: `mount -o remount,rw /`

2. **Reset network configuration:**
   ```bash
   # Remove network configuration
   rm /etc/hostapd/hostapd.conf
   rm /etc/dnsmasq.conf
   
   # Reset to defaults
   cp /opt/photobooth/services/hostapd.conf /etc/hostapd/
   cp /opt/photobooth/services/dnsmasq.conf /etc/
   ```

3. **Safe mode boot:**
   ```bash
   # Disable all PhotoBooth services
   systemctl disable photobooth nginx hostapd dnsmasq
   
   # Enable SSH for remote troubleshooting
   systemctl enable ssh
   ```

## Getting Additional Help

### Collecting Debug Information

Before seeking help, collect system information:
```bash
#!/bin/bash
# debug-info.sh
echo "=== PhotoBooth Debug Information ===" > debug-info.txt
echo "Date: $(date)" >> debug-info.txt
echo "System: $(uname -a)" >> debug-info.txt
echo "" >> debug-info.txt

echo "=== Service Status ===" >> debug-info.txt
systemctl status photobooth nginx hostapd dnsmasq >> debug-info.txt
echo "" >> debug-info.txt

echo "=== Network Configuration ===" >> debug-info.txt
ip addr show >> debug-info.txt
iwconfig >> debug-info.txt
echo "" >> debug-info.txt

echo "=== Recent Logs ===" >> debug-info.txt
tail -50 /opt/photobooth/photobooth.log >> debug-info.txt
journalctl -u photobooth --since "1 hour ago" >> debug-info.txt
```

### Community Resources

- **GitHub Issues**: Report bugs and get community help
- **Documentation**: Comprehensive guides in `/docs` folder
- **CLAUDE.md**: Technical reference for developers

### Professional Support

For production events requiring guaranteed support:
- Plan testing sessions 1-2 weeks before event
- Have backup equipment ready
- Consider hiring technical support for day-of assistance
- Document your specific configuration for future reference