#!/bin/bash
# PhotoBooth Complete Installation Script for Raspberry Pi 3B
# This script installs and configures the entire PhotoBooth system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PHOTOBOOTH_USER="pi"
PHOTOBOOTH_DIR="/opt/photobooth"
SERVICE_USER="${PHOTOBOOTH_USER}"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Logging
LOG_FILE="${PHOTOBOOTH_DIR}/install.log"
exec > >(tee -a "${LOG_FILE}")
exec 2>&1

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
echo_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo_error "This script should not be run as root. Run as pi user with sudo access."
        exit 1
    fi
    
    # Check sudo access
    if ! sudo -n true 2>/dev/null; then
        echo_error "This script requires sudo access. Please ensure the pi user has sudo privileges."
        exit 1
    fi
}

# Check OS compatibility
check_os() {
    echo_info "Checking OS compatibility..."
    
    if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        echo_warning "This script is designed for Raspberry Pi. Continuing anyway..."
    fi
    
    if ! grep -q "Debian\|Raspbian" /etc/os-release; then
        echo_warning "This script is designed for Debian/Raspbian. Continuing anyway..."
    fi
    
    echo_success "OS check completed"
}

# Update system packages
update_system() {
    echo_info "Updating system packages..."
    
    sudo apt update -y
    sudo apt upgrade -y
    
    echo_success "System updated successfully"
}

# Install system dependencies
install_dependencies() {
    echo_info "Installing system dependencies..."
    
    # Core packages
    sudo apt install -y \
        python3 \
        python3-venv \
        python3-pip \
        python3-dev \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        tk-dev \
        tcl-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libxcb1-dev \
        espeak-ng \
        libespeak-ng1 \
        alsa-utils \
        libasound2-dev \
        git \
        curl \
        wget \
        unzip \
        sqlite3 \
        nginx \
        hostapd \
        dnsmasq \
        iptables-persistent \
        cups \
        cups-client \
        cups-bsd \
        printer-driver-all \
        openssl
    
    echo_success "System dependencies installed"
}

# Copy application files to installation directory
copy_application_files() {
    echo_info "Copying application files to ${PHOTOBOOTH_DIR}..."
    
    # Create installation directory
    sudo mkdir -p "${PHOTOBOOTH_DIR}"
    
    # Copy all application files
    sudo cp -r "${CURRENT_DIR}"/* "${PHOTOBOOTH_DIR}/"
    
    # Set proper ownership
    sudo chown -R "${PHOTOBOOTH_USER}:${PHOTOBOOTH_USER}" "${PHOTOBOOTH_DIR}"
    
    # Set proper permissions
    sudo chmod -R 755 "${PHOTOBOOTH_DIR}"
    sudo chmod +x "${PHOTOBOOTH_DIR}/run.sh"
    sudo chmod +x "${PHOTOBOOTH_DIR}/install.sh"
    
    # Create data directories
    sudo mkdir -p "${PHOTOBOOTH_DIR}/data/photos/all"
    sudo mkdir -p "${PHOTOBOOTH_DIR}/data/photos/printed" 
    sudo mkdir -p "${PHOTOBOOTH_DIR}/data/photos/thumbnails"
    sudo mkdir -p "${PHOTOBOOTH_DIR}/photobooth/static/frames"
    
    # Set proper permissions for data directories
    sudo chown -R "${PHOTOBOOTH_USER}:${PHOTOBOOTH_USER}" "${PHOTOBOOTH_DIR}/data"
    sudo chmod -R 755 "${PHOTOBOOTH_DIR}/data"
    
    echo_success "Application files copied successfully"
}

# Create Python virtual environment
setup_python_env() {
    echo_info "Setting up Python virtual environment..."
    
    cd "${PHOTOBOOTH_DIR}"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip wheel setuptools
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    echo_success "Python environment configured"
}

# Configure system services
configure_services() {
    echo_info "Configuring system services..."
    
    # Stop services if running
    sudo systemctl stop hostapd dnsmasq nginx || true
    
    # Install PhotoBooth service
    sudo cp services/photobooth.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable photobooth
    
    # Configure nginx
    sudo cp services/nginx.site /etc/nginx/sites-available/photobooth
    sudo ln -sf /etc/nginx/sites-available/photobooth /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    
    # Configure hostapd
    sudo cp services/hostapd.conf /etc/hostapd/hostapd.conf
    sudo systemctl unmask hostapd
    sudo systemctl enable hostapd
    
    # Configure dnsmasq
    sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
    sudo cp services/dnsmasq.conf /etc/dnsmasq.conf
    sudo systemctl enable dnsmasq
    
    echo_success "System services configured"
}

# Set up WiFi Access Point
setup_wifi_ap() {
    echo_info "Configuring WiFi Access Point..."
    
    # Configure static IP for wlan0
    if ! grep -q "interface wlan0" /etc/dhcpcd.conf; then
        echo "
# PhotoBooth WiFi AP Configuration
interface wlan0
static ip_address=192.168.50.1/24
nohook wpa_supplicant" | sudo tee -a /etc/dhcpcd.conf
    fi
    
    # Enable WiFi if disabled
    sudo rfkill unblock wlan
    
    echo_success "WiFi Access Point configured"
}

# Set up certificates
setup_certificates() {
    echo_info "Setting up TLS certificates..."
    
    # Run certificate generation script
    bash services/mkcert.sh
    
    echo_success "TLS certificates configured"
}

# Configure IP forwarding and NAT
setup_networking() {
    echo_info "Configuring networking and NAT..."
    
    # Run networking script
    sudo bash services/sysctl_iptables.sh
    
    # Enable IP forwarding at boot
    if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
        echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
    fi
    
    echo_success "Networking configured"
}

# Configure CUPS printing
setup_printing() {
    echo_info "Configuring CUPS printing system..."
    
    # Add pi user to lpadmin group
    sudo usermod -a -G lpadmin "${PHOTOBOOTH_USER}"
    
    # Enable CUPS service
    sudo systemctl enable cups
    sudo systemctl start cups
    
    # Configure CUPS for network access
    sudo cp /etc/cups/cupsd.conf /etc/cups/cupsd.conf.backup
    
    # Allow access from PhotoBooth network
    sudo sed -i 's/Listen localhost:631/Listen 0.0.0.0:631/' /etc/cups/cupsd.conf
    
    if ! grep -q "Allow 192.168.50.*" /etc/cups/cupsd.conf; then
        sudo sed -i '/<Location \/>/a\  Allow 192.168.50.*' /etc/cups/cupsd.conf
        sudo sed -i '/<Location \/admin>/a\  Allow 192.168.50.*' /etc/cups/cupsd.conf
    fi
    
    echo_success "CUPS printing configured"
}

# Create environment file
create_env_file() {
    echo_info "Creating environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        
        # Generate a random secret key
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i "s/your-super-secret-flask-key-change-this/${SECRET_KEY}/" .env
        
        echo_info "Environment file created. Please review .env for customization."
    else
        echo_info "Environment file already exists"
    fi
    
    echo_success "Environment configured"
}

# Initialize database
setup_database() {
    echo_info "Initializing database..."
    
    cd "${PHOTOBOOTH_DIR}"
    source venv/bin/activate
    
    # Initialize the database
    python3 -c "
from photobooth.models import init_db
init_db('/opt/photobooth/data/photobooth.db')
print('Database initialized successfully')
"
    
    echo_success "Database initialized"
}

# Create scripts directory
setup_scripts() {
    echo_info "Setting up utility scripts..."
    
    mkdir -p scripts
    
    # Create certificate trust instructions
    cat > scripts/trust_cert_instructions.md << 'EOF'
# Trust Certificate Instructions

## iOS Devices

1. Connect to the PhotoBooth WiFi network
2. Open Safari and go to https://192.168.50.1/
3. You'll see a certificate warning - tap "Advanced" then "Proceed"
4. Go to Settings > General > VPN & Device Management
5. Under "Configuration Profile" tap the PhotoBooth certificate
6. Tap "Install" and enter your passcode
7. Tap "Install" again, then "Done"
8. Go to Settings > General > About > Certificate Trust Settings
9. Enable full trust for the PhotoBooth certificate

## Android Devices

1. Connect to the PhotoBooth WiFi network
2. Open Chrome and go to https://192.168.50.1/
3. You'll see a certificate warning - tap "Advanced" then "Proceed to 192.168.50.1"
4. The certificate will be temporarily accepted

## Windows Devices

1. Connect to the PhotoBooth WiFi network
2. Open Edge/Chrome and go to https://192.168.50.1/
3. Click "Advanced" then "Continue to 192.168.50.1"
4. Click the lock icon in the address bar
5. Click "Certificate" then "Details" then "Copy to File"
6. Save as photobooth.crt
7. Double-click the file and click "Install Certificate"
8. Select "Local Machine" and "Place all certificates in the following store"
9. Browse and select "Trusted Root Certification Authorities"

## macOS Devices

1. Connect to the PhotoBooth WiFi network
2. Open Safari and go to https://192.168.50.1/
3. You'll see a certificate warning - click "Show Details" then "Visit this website"
4. In Keychain Access, find the PhotoBooth certificate under "login"
5. Double-click it and change "When using this certificate" to "Always Trust"
EOF

    # Create certificate regeneration script
    cat > scripts/regenerate_cert.sh << 'EOF'
#!/bin/bash
# Regenerate TLS certificates

echo "Regenerating PhotoBooth TLS certificates..."
cd "$(dirname "$0")/.."
sudo bash services/mkcert.sh
sudo systemctl reload nginx
echo "Certificates regenerated and nginx reloaded"
EOF
    
    chmod +x scripts/regenerate_cert.sh
    
    echo_success "Utility scripts created"
}

# Start services
start_services() {
    echo_info "Starting PhotoBooth services..."
    
    # Start system services
    sudo systemctl start hostapd
    sudo systemctl start dnsmasq
    sudo systemctl start nginx
    sudo systemctl start cups
    
    # Start PhotoBooth application
    sudo systemctl start photobooth
    
    echo_success "All services started"
}

# Verify installation
verify_installation() {
    echo_info "Verifying installation..."
    
    # Check service status
    services=("photobooth" "nginx" "hostapd" "dnsmasq" "cups")
    for service in "${services[@]}"; do
        if sudo systemctl is-active --quiet "$service"; then
            echo_success "$service is running"
        else
            echo_error "$service is not running"
        fi
    done
    
    # Check if WiFi AP is working
    if iwconfig wlan0 2>/dev/null | grep -q "Mode:Master"; then
        echo_success "WiFi Access Point is active"
    else
        echo_warning "WiFi Access Point may not be active"
    fi
    
    # Check if web interface is accessible
    if curl -k -s https://localhost/ > /dev/null; then
        echo_success "Web interface is accessible"
    else
        echo_warning "Web interface may not be accessible"
    fi
    
    echo_success "Installation verification completed"
}

# Main installation function
main() {
    echo_info "Starting PhotoBooth installation on $(hostname) at $(date)"
    
    check_root
    check_os
    update_system
    install_dependencies
    copy_application_files
    setup_python_env
    create_env_file
    setup_database
    configure_services
    setup_wifi_ap
    setup_certificates
    setup_networking
    setup_printing
    setup_scripts
    start_services
    verify_installation
    
    echo_success "
=================================================================
PhotoBooth Installation Complete!
=================================================================

Next Steps:
1. Connect your printer via USB and configure it in CUPS
2. Access the web interface at https://192.168.50.1/
3. Configure settings at https://192.168.50.1/settings/
4. Upload a frame overlay if desired
5. Test the photo booth functionality

WiFi Network: PhotoBooth
WiFi Password: photobooth123
Web Interface: https://192.168.50.1/
Settings Password: admin123

For certificate trust instructions, see:
${PHOTOBOOTH_DIR}/scripts/trust_cert_instructions.md

Log file: ${LOG_FILE}

Reboot recommended to ensure all services start correctly.
================================================================="
}

# Run installation
main "$@"