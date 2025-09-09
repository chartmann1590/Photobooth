#!/bin/bash
# Production run script for Photobooth on Raspberry Pi

set -e

# Configuration
INSTALL_DIR="/opt/photobooth"
VENV_DIR="$INSTALL_DIR/venv"
LOG_FILE="$INSTALL_DIR/photobooth.log"

# Check if running as the correct user
if [ "$USER" != "pi" ] && [ "$USER" != "photobooth" ]; then
    echo "Warning: This script is intended to run as user 'pi' or 'photobooth'"
fi

# Change to installation directory
cd "$INSTALL_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found at $VENV_DIR"
    echo "Please run the installation script first: sudo bash install.sh"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file to customize your installation"
fi

# Set production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=false

# Ensure proper permissions on log file
touch "$LOG_FILE"
chmod 664 "$LOG_FILE"

# Ensure data directories exist with proper permissions
mkdir -p "/opt/photobooth/data/photos/all"
mkdir -p "/opt/photobooth/data/photos/printed"
mkdir -p "/opt/photobooth/data/photos/thumbnails"
chmod -R 755 "/opt/photobooth/data"

echo "Starting Photobooth application..."
echo "Log output: tail -f $LOG_FILE"
echo "Access at: https://192.168.50.1/"
echo "Settings at: https://192.168.50.1/settings"
echo ""

# Start the application
exec python app.py