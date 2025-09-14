#!/bin/bash
# update_gutenprint.sh – Build and install the latest Gutenprint and selphy_print on Raspberry Pi
# Run this script as root (sudo su -) to update Gutenprint and fix paper‑mismatch errors.

set -e

# Remove existing Gutenprint packages and ipp-usb to avoid conflicts
apt remove -y '*gutenprint*' ipp-usb || true

# Install development libraries and tools
apt update
apt install -y libusb-1.0-0-dev libcups2-dev pkg-config cups-daemon git-lfs curl build-essential

# Variables for the Gutenprint snapshot; update GUTENPRINT_VER to the latest snapshot when needed
GUTENPRINT_VER="5.3.5-pre1-2025-02-13T14-28-b60f1e83"

# Download the snapshot tarball from SourceForge
SNAPSHOT_URL="https://master.dl.sourceforge.net/project/gimp-print/snapshots/gutenprint-${GUTENPRINT_VER}.tar.xz?viasf=1"
echo "Downloading Gutenprint snapshot ${GUTENPRINT_VER}..."
curl -L -o gutenprint-${GUTENPRINT_VER}.tar.xz "$SNAPSHOT_URL"

# Extract and build Gutenprint
rm -rf gutenprint-${GUTENPRINT_VER} || true
tar -xJf gutenprint-${GUTENPRINT_VER}.tar.xz
cd gutenprint-${GUTENPRINT_VER}
./configure --without-doc --enable-debug
make -j$(nproc)
make install
cd ..

# Refresh PPDs and restart CUPS
cups-genppdupdate
service cups restart

# Compile and install the selphy_print backend (required for SELPHY series)
if [ ! -d selphy_print ]; then
  git clone https://git.shaftnet.org/gitea/slp/selphy_print.git
fi
cd selphy_print
make -j$(nproc)
make install
cd ..

# Ensure /usr/local/lib is in the dynamic linker path
if [ ! -f /etc/ld.so.conf.d/usr-local.conf ]; then
  echo "/usr/local/lib" > /etc/ld.so.conf.d/usr-local.conf
fi
ldconfig

# Finished
echo "\nModern Gutenprint and the selphy_print backend have been installed."
echo "Restart CUPS and re-add your Canon SELPHY CP760 through the CUPS web interface."