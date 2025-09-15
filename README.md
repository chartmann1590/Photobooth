# Wedding PhotoBooth for Raspberry Pi 3B

**Repository**: https://github.com/chartmann1590/Photobooth.git

A complete, production-ready wedding photobooth system that runs on Raspberry Pi 3B with offline WiFi hotspot, professional printing, HTTPS certificate support, and beautiful touch-friendly interface designed for dark venues.

## ✨ Key Features

- **Complete offline WiFi system** - Creates captive portal hotspot for up to 10 guests
- **Professional photo capture** - WebRTC camera with frame overlays and instant preview
- **USB printing integration** - CUPS support for Canon SELPHY, HP, Epson printers
- **SMS photo sharing** - Instant sharing via SMS-Gate with ImgBB hosting
- **Wedding-optimized UI** - Mobile-first design perfect for dark venues
- **Text-to-speech audio** - Countdown announcements with eSpeak NG
- **Admin management** - Password-protected settings with system monitoring

## 🚀 Quick Start

### One-Command Installation

```bash
git clone https://github.com/chartmann1590/Photobooth.git photobooth
cd photobooth
sudo bash install.sh
sudo reboot
```

**That's it!** After reboot:
- Connect to **"PhotoBooth"** WiFi (password: `photobooth123`)
- Visit **https://192.168.50.1/** for the photobooth
- Visit **https://192.168.50.1/settings** for admin (password: `admin123`)

### What Gets Installed
- Complete WiFi hotspot with captive portal
- HTTPS certificates for camera access
- All system services (nginx, hostapd, dnsmasq, CUPS)
- Python environment with dependencies
- Database initialization and photo storage

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Installation Guide](docs/installation.md)** - Complete setup instructions and requirements
- **[Features Guide](docs/features.md)** - Detailed feature documentation and usage
- **[Configuration Guide](docs/configuration.md)** - All configuration options and customization
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions
- **[API Documentation](docs/api.md)** - REST API reference for developers
- **[Production Checklist](docs/production-checklist.md)** - Event day preparation and monitoring
- **[SMS Setup Guide](docs/sms-setup.md)** - Complete SMS photo sharing configuration

## ⚙️ System Requirements

### Hardware
- **Raspberry Pi 3B** (minimum) or newer
- **16GB+ microSD** card (Class 10 recommended)
- **USB printer** (optional but recommended)
- **2.5A power supply**

### Tested Printers
- **Canon SELPHY** CP760, CP800, CP900 series
- **HP DeskJet** 2600, 3700, 4100 series
- **Epson Expression** Home series

## 🎯 Perfect For

- **Weddings** and receptions
- **Engagement parties** 
- **Anniversary celebrations**
- **Bridal showers**
- **Any special event** deserving beautiful memories

## 🔧 Quick Configuration

### Change WiFi Settings
```bash
sudo nano /opt/photobooth/.env
# Update AP_SSID and AP_PASSWORD
sudo systemctl restart hostapd dnsmasq
```

### Upload Custom Frame
1. Go to **Settings → Frame** section
2. Upload PNG with transparency (1800×1200 recommended)
3. Preview and save

### Configure Printer
1. Connect USB printer
2. Go to **Settings → Printer** section  
3. Select printer and run test print

## 📊 Event Capacity

- **Photos**: 1000+ photos on 16GB card
- **Users**: Up to 10 concurrent connections
- **Print speed**: ~30-90 seconds (printer dependent)
- **Processing**: ~3-5 seconds per photo with frame

## 🛠️ Service Management

```bash
# Check system status
sudo systemctl status photobooth nginx hostapd dnsmasq

# View logs
tail -f /opt/photobooth/photobooth.log
sudo journalctl -u photobooth -f

# Restart services
sudo systemctl restart photobooth
```

## 🎨 Customization

The system is highly customizable:
- **Photo quality** settings for performance tuning
- **Custom frame overlays** with PNG transparency
- **SMS photo sharing** with international support
- **Audio announcements** with voice selection
- **Network configuration** for different environments

## 💡 Production Tips

1. **Test extensively** before your event
2. **Change default passwords** for security
3. **Upload custom frame** with wedding details
4. **Stock adequate supplies** (paper, ink cartridges)
5. **Position strategically** for good lighting and WiFi coverage

## 🤝 Contributing

This project is designed as a complete solution. For improvements:
1. Test thoroughly on Raspberry Pi 3B
2. Maintain compatibility with existing installation
3. Follow the wedding theme design principles

## 📄 License

MIT License - Feel free to use for your special day! 💕

## 💍 Credits

Created with love for couples celebrating their special moments. Built to capture joy, laughter, and unforgettable memories at life's most precious celebrations.

---

*May your PhotoBooth capture all the joy and love of your special day! 💖*