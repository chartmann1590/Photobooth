# PhotoBooth Documentation

This directory contains comprehensive documentation for the PhotoBooth system, covering everything from installation to advanced features and troubleshooting.

## 📚 Documentation Overview

### 🚀 Getting Started

- **[Installation Guide](installation.md)** - Complete setup instructions for Raspberry Pi deployment
- **[Configuration Guide](configuration.md)** - Detailed configuration options and settings management
- **[Production Checklist](production-checklist.md)** - Pre-event checklist and deployment verification

### ✨ Core Features

- **[Features Overview](features.md)** - Complete feature list and capabilities
- **[API Documentation](api.md)** - REST API endpoints and integration guide
- **[SMS Photo Sharing](sms_photo_sharing.md)** - Real-time photo sharing via SMS integration

### 🔧 Hardware & Printing

- **[Canon Selphy Printer Setup](selphy_printer_setup.md)** - Specific setup guide for Canon Selphy CP1300/CP1500 printers

### 📱 Advanced Integration

- **[SMS Gateway Setup](sms-setup.md)** - Complete SMS gateway configuration and troubleshooting
- **[Immich Gallery Sync](immich_sync.md)** - Automatic photo backup to personal Immich server

### 🛠️ Maintenance & Support

- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions

## 🏗️ Architecture Overview

The PhotoBooth system is designed as a complete wedding photography solution with:

- **Offline WiFi Access Point** - Creates isolated network with optional internet sharing
- **Professional Photo Capture** - Browser-based camera interface with frame overlays
- **Instant Printing** - CUPS integration for professional photo printing
- **Real-time Sharing** - SMS integration for immediate photo delivery
- **Gallery Management** - Web-based photo browsing and management
- **Cloud Backup** - Optional Immich sync for personal photo server backup

## 📖 Quick Navigation

| Component | Documentation | Description |
|-----------|---------------|-------------|
| **Installation** | [installation.md](installation.md) | Initial setup and deployment |
| **Basic Config** | [configuration.md](configuration.md) | Settings and customization |
| **SMS Features** | [sms_photo_sharing.md](sms_photo_sharing.md) | Photo sharing setup |
| **Printing** | [selphy_printer_setup.md](selphy_printer_setup.md) | Printer configuration |
| **Cloud Sync** | [immich_sync.md](immich_sync.md) | Photo backup integration |
| **API Access** | [api.md](api.md) | Developer integration |
| **Production** | [production-checklist.md](production-checklist.md) | Event deployment |
| **Problems** | [troubleshooting.md](troubleshooting.md) | Issue resolution |

## 🎯 Common Use Cases

### Wedding Photography Setup
1. Start with [Installation Guide](installation.md)
2. Configure printer using [Selphy Setup](selphy_printer_setup.md) 
3. Set up photo sharing with [SMS Guide](sms_photo_sharing.md)
4. Enable cloud backup with [Immich Sync](immich_sync.md)
5. Verify everything with [Production Checklist](production-checklist.md)

### Party/Event Setup
1. Basic [Installation](installation.md) and [Configuration](configuration.md)
2. Set up [Printing](selphy_printer_setup.md) for instant photos
3. Optional [SMS Sharing](sms_photo_sharing.md) for guests
4. Use [Troubleshooting Guide](troubleshooting.md) if issues arise

### Developer Integration
1. Review [API Documentation](api.md) for available endpoints
2. Check [Features Overview](features.md) for capabilities
3. Use [Configuration Guide](configuration.md) for customization options

## 🔍 Quick Reference

- **Default Access**: `https://192.168.50.1/` (when connected to PhotoBooth WiFi)
- **Settings Panel**: `https://192.168.50.1/settings/`
- **Photo Gallery**: `https://192.168.50.1/gallery/`
- **Default WiFi**: `PhotoBooth` (password in installation guide)

## 📞 Support

If you encounter issues not covered in the documentation:

1. Check the [Troubleshooting Guide](troubleshooting.md) first
2. Review relevant feature documentation above
3. Check system logs: `sudo journalctl -u photobooth -f`
4. Verify hardware connections and network settings

---

*This documentation is maintained alongside the PhotoBooth codebase. Last updated: September 2025*