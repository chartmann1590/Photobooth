#!/bin/bash
# setup_cp760.sh – Install CUPS and Gutenprint driver for Canon SELPHY CP760
# This script must be run on Raspberry Pi OS.  It uses sudo for privileged operations.

set -e

# Update package lists
sudo apt update

# Install CUPS and Gutenprint driver (and optional Samba for Windows sharing)
sudo apt install -y cups printer-driver-gutenprint

# Optional: install Samba if you plan to share the printer with Windows clients
# sudo apt install -y samba

# Add the current user to the lpadmin group so they can administer CUPS
sudo usermod -a -G lpadmin "$USER"

# Enable remote access to the CUPS web interface
sudo cupsctl --remote-any

# Enable and restart the CUPS service
sudo systemctl enable cups
sudo systemctl restart cups

# Display instructions
echo "\nCUPS and the Gutenprint driver have been installed."
echo "Your user has been added to the lpadmin group."

echo "\nTo finish configuring your Canon SELPHY CP760:"
echo "1. Ensure the printer is connected to the Raspberry Pi and powered on."
echo "2. Find the Pi's IP address by running: hostname -I"
echo "3. On a computer on the same network, open https://<pi-ip>:631 in a web browser."
echo "4. In the CUPS interface, go to Administration > Add Printer."
echo "5. Select the Canon SELPHY CP760 and choose the Gutenprint driver when prompted."
echo "6. Complete the setup and print a test page."

# Optionally, list the detected printers (useful for debugging)
echo "\nDetected printers (if any):"
sudo lpinfo -v || true