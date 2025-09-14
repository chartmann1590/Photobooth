# Canon SELPHY CP760 Printer Setup Guide

This guide provides detailed instructions for setting up the Canon SELPHY CP760 dye-sublimation printer with the PhotoBooth Flask application on Raspberry Pi.

## Overview

The Canon SELPHY CP760 is a compact dye-sublimation photo printer that produces high-quality 4x6 inch prints. Since Canon no longer provides official Linux drivers, we rely on the open-source **Gutenprint** driver project and the CUPS printing system.

### Known Issues

The Gutenprint package bundled with Raspberry Pi OS may be outdated, which can cause **"Incorrect paper loaded (01 vs 11)"** errors even when the correct paper is loaded. This guide provides solutions for both basic setup and fixing these paper-mismatch errors.

## Prerequisites

- Raspberry Pi running Raspberry Pi OS
- Canon SELPHY CP760 printer
- Compatible dye-sublimation paper cartridges (KC-36IP or KC-18IP)
- USB cable to connect printer to Raspberry Pi
- Network access for downloading packages

## Quick Setup (Basic Installation)

For most users, the basic CUPS and Gutenprint installation will work:

### 1. Run the Setup Script

We've provided an automated setup script in the `scripts` directory:

```bash
cd /home/chartmann/photobooth
sudo chmod +x scripts/setup_cp760.sh
./scripts/setup_cp760.sh
```

### 2. Manual Installation Steps

If you prefer to run the commands manually:

```bash
# Update package lists
sudo apt update

# Install CUPS and Gutenprint driver
sudo apt install cups printer-driver-gutenprint

# Add current user to lpadmin group
sudo usermod -a -G lpadmin $USER

# Enable remote access to CUPS web interface
sudo cupsctl --remote-any

# Enable and restart CUPS service
sudo systemctl enable cups
sudo systemctl restart cups
```

### 3. Configure the Printer

1. Ensure the Canon SELPHY CP760 is connected via USB and powered on
2. Find your Raspberry Pi's IP address: `hostname -I`
3. From any computer on the same network, open `https://<pi-ip>:631` in a web browser
4. Navigate to **Administration > Add Printer**
5. Select the Canon SELPHY CP760 from the detected printers list
6. When prompted for the driver, choose **"Canon SELPHY CP760 – CUPS+Gutenprint"**
7. Complete the setup and print a test page

## Advanced Setup (Fix Paper Mismatch Errors)

If you encounter "Incorrect paper loaded" errors, you'll need to compile and install a newer version of Gutenprint along with the `selphy_print` backend.

### 1. Run the Update Script

We've provided an automated script for this process:

```bash
cd /home/chartmann/photobooth
sudo chmod +x scripts/update_gutenprint.sh
sudo su -
./scripts/update_gutenprint.sh
exit
```

### 2. Manual Advanced Installation

If you prefer to run the commands manually:

#### Install Development Dependencies

```bash
sudo apt update
sudo apt remove -y '*gutenprint*' ipp-usb || true
sudo apt install -y libusb-1.0-0-dev libcups2-dev pkg-config cups-daemon git-lfs curl build-essential
```

#### Download and Compile Latest Gutenprint

```bash
# Download the latest snapshot (update version as needed)
GUTENPRINT_VER="5.3.5-pre1-2025-02-13T14-28-b60f1e83"
SNAPSHOT_URL="https://master.dl.sourceforge.net/project/gimp-print/snapshots/gutenprint-${GUTENPRINT_VER}.tar.xz?viasf=1"

curl -L -o gutenprint-${GUTENPRINT_VER}.tar.xz "$SNAPSHOT_URL"
tar -xJf gutenprint-${GUTENPRINT_VER}.tar.xz
cd gutenprint-${GUTENPRINT_VER}

# Configure, compile and install
./configure --without-doc --enable-debug
make -j$(nproc)
sudo make install
cd ..
```

#### Install selphy_print Backend

```bash
# Clone and build selphy_print backend
git clone https://git.shaftnet.org/gitea/slp/selphy_print.git
cd selphy_print
make -j$(nproc)
sudo make install
cd ..
```

#### Update System Configuration

```bash
# Refresh PPD files and restart CUPS
sudo cups-genppdupdate
sudo service cups restart

# Ensure /usr/local/lib is in the dynamic linker path
echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/usr-local.conf
sudo ldconfig
```

### 3. Re-configure the Printer

After updating Gutenprint:

1. Access the CUPS web interface at `https://<pi-ip>:631`
2. Remove the existing SELPHY CP760 printer if already configured
3. Add the printer again, selecting the updated Gutenprint driver
4. Print a test page to verify the paper mismatch error is resolved

## Integration with PhotoBooth Application

Once the Canon SELPHY CP760 is properly configured in CUPS, it will automatically appear in the PhotoBooth application's printer settings:

1. Access the PhotoBooth admin interface at `https://<pi-ip>/settings`
2. Navigate to **Printer Settings**
3. Select the Canon SELPHY CP760 from the available printers list
4. Configure print queue settings as needed
5. Test printing from the PhotoBooth interface

## Troubleshooting

### Common Issues

**"Incorrect paper loaded (01 vs 11)" Error**
- This indicates an outdated Gutenprint driver
- Follow the Advanced Setup instructions to install the latest Gutenprint snapshot

**Printer Not Detected**
- Ensure the printer is powered on and connected via USB
- Check USB connection with: `lsusb | grep Canon`
- Restart CUPS: `sudo systemctl restart cups`

**Print Jobs Stuck in Queue**
- Check printer status: `lpstat -p`
- Clear print queue: `sudo cancel -a`
- Ensure correct paper/ink cartridge is installed

**Permission Issues**
- Ensure your user is in the lpadmin group: `groups $USER`
- If not, add with: `sudo usermod -a -G lpadmin $USER`
- Log out and back in for group changes to take effect

### Useful Commands

```bash
# Check printer status
lpstat -p -d

# List available printers
lpinfo -v

# Test print
echo "Test page" | lp -d CanonSELPHYCP760

# View CUPS error log
sudo tail -f /var/log/cups/error_log

# Check Gutenprint version
dpkg -l | grep gutenprint
```

## Paper and Ink Information

The Canon SELPHY CP760 uses specific paper and ink cartridge combinations:

- **KC-36IP**: 36 sheets of 4x6" paper with ink cartridge
- **KC-18IP**: 18 sheets of 4x6" paper with ink cartridge

Ensure you're using genuine Canon cartridges for best results and to avoid paper detection errors.

## Additional Resources

- [CUPS Documentation](https://www.cups.org/documentation.html)
- [Gutenprint Project](http://gimp-print.sourceforge.net/)
- [selphy_print Backend](https://git.shaftnet.org/gitea/slp/selphy_print)

## Scripts Reference

This repository includes two helper scripts in the `scripts/` directory:

- **setup_cp760.sh**: Basic installation of CUPS and Gutenprint
- **update_gutenprint.sh**: Advanced installation with latest Gutenprint snapshot

Both scripts include detailed logging and error handling for reliable setup.