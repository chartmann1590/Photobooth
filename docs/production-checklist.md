# Production Event Checklist

This comprehensive checklist ensures your PhotoBooth system is ready for live events and helps prevent common issues.

## Pre-Event Planning (1-2 Weeks Before)

### System Configuration
- [ ] **Change default passwords**
  - WiFi password from `photobooth123` to unique secure password
  - Admin password from `admin123` to unique secure password
  - Document new passwords for event day reference

- [ ] **Customize WiFi settings**
  - Update SSID to wedding/event name (e.g., "JohnAndJane2024")
  - Verify password is easy for guests to type but secure
  - Test WiFi range in intended venue location

- [ ] **Upload custom frame overlay**
  - Create or design frame with couple names, date, venue
  - Test frame with sample photos to ensure proper positioning
  - Verify transparency areas show faces clearly
  - Save backup copy of frame file

### Hardware Testing
- [ ] **Printer setup and testing**
  - Connect USB printer and verify auto-detection
  - Load correct paper size (4x6" photo paper)
  - Print test photos to verify colors and quality
  - Stock adequate paper and ink cartridges (estimate 1 print per 3 photos)
  - Test print speed and queue handling

- [ ] **Camera functionality**
  - Test camera on multiple device types (iPhone, Android, iPad)
  - Verify HTTPS certificate trust on all device types
  - Test front/back camera switching
  - Verify frame overlay appears correctly in preview

- [ ] **Audio system testing**
  - Test TTS countdown functionality
  - Adjust volume levels for venue acoustics
  - Verify voice selection and speech rate
  - Test with external speakers if needed

### SMS Photo Sharing Setup (Optional)
- [ ] **SMS-Gate configuration**
  - Install SMS-Gate app on Android device
  - Configure server settings and note IP address
  - Test SMS gateway connectivity
  - Verify ImgBB account and API key

- [ ] **SMS functionality testing**
  - Send test SMS to multiple phone number formats
  - Test international numbers if needed
  - Verify image hosting and link generation
  - Test SMS delivery timing and reliability

### Network and Security
- [ ] **Network performance testing**
  - Test with maximum expected concurrent users (8-10 devices)
  - Verify internet sharing via ethernet (if needed)
  - Test network range throughout venue
  - Check for WiFi interference sources

- [ ] **Security verification**
  - Verify HTTPS certificate trust process
  - Test admin access protection
  - Confirm guest isolation on network
  - Review data privacy settings

### Storage and Performance
- [ ] **Storage capacity planning**
  - Ensure 8GB+ free space for event photos
  - Plan for 2-3MB per photo, estimate guest count
  - Set up automatic backup process if needed
  - Test microSD card performance under load

- [ ] **Performance optimization**
  - Increase GPU memory split to 128MB
  - Disable unnecessary system services
  - Test photo processing speed under load
  - Monitor system temperature during extended use

## Event Day Setup (30 Minutes Before)

### System Startup
- [ ] **Power on and boot verification**
  - Allow 2-3 minutes for complete system boot
  - Verify all LED indicators show normal status
  - Check system temperature and ventilation

- [ ] **Service status verification**
  ```bash
  sudo systemctl status photobooth nginx hostapd dnsmasq cups
  ```
  - All services should show "active (running)"
  - No error messages in status output

### Network Testing
- [ ] **WiFi hotspot verification**
  - Confirm PhotoBooth network is broadcasting
  - Test connection from guest device type
  - Verify automatic captive portal redirect
  - Test HTTPS certificate acceptance

- [ ] **IP address and connectivity**
  ```bash
  ip addr show wlan0
  ping -c 3 192.168.50.1
  ```
  - Confirm wlan0 has 192.168.50.1 IP address
  - Verify local connectivity

### Hardware Verification
- [ ] **Printer readiness**
  - Confirm printer is powered on and shows ready status
  - Verify paper is loaded correctly (4x6" orientation)
  - Check ink/toner levels
  - Print one test photo to verify quality

- [ ] **Camera system test**
  - Access PhotoBooth interface from test device
  - Take one complete test photo with frame
  - Verify photo quality and frame positioning
  - Test print workflow end-to-end

- [ ] **Audio system check**
  - Test TTS countdown announcement
  - Verify volume level appropriate for venue
  - Confirm speakers/audio output working

### Application Testing
- [ ] **Core functionality verification**
  - Access main PhotoBooth interface at `https://192.168.50.1/`
  - Take test photo and verify instant preview
  - Test all three options: Print, SMS, Retake
  - Verify gallery displays test photos correctly

- [ ] **Admin interface testing**
  - Access settings at `https://192.168.50.1/settings`
  - Login with admin credentials
  - Verify all status indicators show green/healthy
  - Test printer and SMS settings if configured

### Final Checks
- [ ] **Storage and logs**
  - Verify adequate free space: `df -h`
  - Check recent logs for errors: `tail -f /opt/photobooth/photobooth.log`
  - Confirm database is accessible and responsive

- [ ] **Backup verification**
  - Confirm backup storage location is accessible
  - Test manual photo backup process if planned
  - Document recovery procedures for team

- [ ] **Guest instruction materials**
  - Prepare WiFi network name and password signs
  - Create simple instruction cards if needed
  - Designate tech support contact person

## During Event Monitoring

### Regular System Checks (Every 2-3 Hours)
- [ ] **Service health monitoring**
  ```bash
  sudo systemctl status photobooth
  tail -20 /opt/photobooth/photobooth.log
  ```

- [ ] **Storage space monitoring**
  ```bash
  df -h
  du -sh /opt/photobooth/data/photos/
  ```

- [ ] **System performance**
  - Monitor CPU temperature: `vcgencmd measure_temp`
  - Check memory usage: `free -h`
  - Verify network device count

### Photo and Print Management
- [ ] **Gallery monitoring**
  - Periodically check photo count and quality
  - Monitor for any failed photo saves
  - Check print queue for stuck jobs

- [ ] **Printer maintenance**
  - Monitor paper levels throughout event
  - Clear any paper jams immediately
  - Check print queue and clear failed jobs if needed
  - Replace paper/ink cartridges as needed

- [ ] **Network performance**
  - Monitor connected device count
  - Watch for network connectivity issues
  - Check for WiFi interference problems

### Troubleshooting Response
- [ ] **Common issue responses**
  - Camera access issues: Guide certificate trust process
  - Print problems: Check printer status and restart if needed
  - Network issues: Restart hostapd/dnsmasq services
  - Performance issues: Monitor and restart PhotoBooth service if needed

## Post-Event Procedures

### Data Backup
- [ ] **Photo archive creation**
  ```bash
  # Create dated backup
  sudo cp -r /opt/photobooth/data/photos /home/pi/event-backup-$(date +%Y%m%d)
  
  # Create ZIP archive for delivery
  cd /opt/photobooth/data/photos/all
  zip -r ../photobooth-photos-$(date +%Y%m%d).zip *.jpg
  ```

- [ ] **Database backup**
  ```bash
  sudo cp /opt/photobooth/data/photobooth.db /home/pi/photobooth-db-$(date +%Y%m%d).db
  ```

- [ ] **Configuration backup**
  ```bash
  sudo cp /opt/photobooth/.env /home/pi/photobooth-config-$(date +%Y%m%d).env
  ```

### System Maintenance
- [ ] **Log review and cleanup**
  - Review event logs for any issues
  - Archive important logs
  - Clean up old log files to free space

- [ ] **Photo delivery preparation**
  - Organize photos by timestamp or event segment
  - Generate gallery webpage if requested
  - Prepare photos for client delivery (USB, cloud, etc.)

- [ ] **System cleanup**
  - Clear temporary files and caches
  - Reset system to defaults if needed for next event
  - Update documentation with any lessons learned

### Performance Analysis
- [ ] **Event statistics**
  - Total photos taken
  - Print job success rate
  - SMS delivery statistics
  - Peak concurrent user count

- [ ] **Issue documentation**
  - Document any problems encountered
  - Note solutions and response times
  - Update troubleshooting procedures

## Emergency Procedures

### Critical System Failure
If the PhotoBooth system completely fails:

1. **Immediate response:**
   - Have backup camera/phone ready for manual photo collection
   - Notify event coordinator of technical difficulties
   - Attempt system reboot: `sudo reboot`

2. **Quick recovery steps:**
   ```bash
   # Service restart sequence
   sudo systemctl restart photobooth nginx hostapd dnsmasq
   
   # Network reset if needed
   sudo rfkill unblock wlan
   sudo systemctl restart hostapd
   ```

3. **Fallback options:**
   - Use mobile hotspot if available
   - Manual photo collection with instant cameras
   - Guest photo sharing via existing social media

### Printer Failure
If printer stops working:

1. **Quick fixes:**
   - Check paper jam and clear
   - Restart printer and check USB connection
   - Restart CUPS service: `sudo systemctl restart cups`

2. **Alternative printing:**
   - Queue photos for later printing
   - Use alternative printer if available
   - Manual print job processing post-event

### Network Issues
If WiFi hotspot fails:

1. **Emergency network:**
   - Use mobile hotspot as backup
   - Connect PhotoBooth to existing venue WiFi
   - Manual network sharing setup

2. **Fallback connectivity:**
   ```bash
   # Manual hotspot restart
   sudo systemctl restart hostapd dnsmasq
   sudo rfkill unblock wlan
   ```

## Contact Information Template

**Event Day Emergency Contacts:**
- Technical Support: _________________
- Event Coordinator: ________________
- Venue IT Contact: _________________
- Equipment Backup: _________________

**PhotoBooth System Info:**
- WiFi Network: ____________________
- WiFi Password: ___________________
- Admin Password: __________________
- System Location: _________________

**Vendor Contacts:**
- Printer Support: _________________
- Internet/Network: ________________
- Equipment Rental: _______________

## Success Metrics

### Technical Performance
- [ ] System uptime > 99% during event
- [ ] Photo capture success rate > 95%
- [ ] Print success rate > 90%
- [ ] SMS delivery rate > 85% (if enabled)
- [ ] Average photo processing time < 5 seconds

### User Experience
- [ ] Camera access successful on all device types
- [ ] Minimal guest assistance required for operation
- [ ] Positive feedback on photo quality and frame design
- [ ] Smooth print and SMS workflow operation
- [ ] No significant technical delays or interruptions

### Event Impact
- [ ] High guest engagement with PhotoBooth
- [ ] Successful photo sharing and social media presence
- [ ] Complete photo archive delivered to client
- [ ] Professional appearance and operation
- [ ] Memorable experience creation for guests