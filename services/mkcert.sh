#!/bin/bash
# Generate TLS certificates for PhotoBooth using mkcert or openssl

set -e

# Check if mkcert is available
if command -v mkcert &> /dev/null; then
    echo "Using mkcert to generate certificates..."
    
    # Install CA if not already installed
    mkcert -install
    
    # Generate certificates for common domains
    cd /tmp
    mkcert \
        192.168.50.1 \
        photobooth.local \
        localhost \
        127.0.0.1 \
        ::1
    
    # Move certificates to proper location
    sudo mkdir -p /etc/ssl/certs /etc/ssl/private
    sudo mv 192.168.50.1+4.pem /etc/ssl/certs/photobooth.crt
    sudo mv 192.168.50.1+4-key.pem /etc/ssl/private/photobooth.key
    
    # Set proper permissions
    sudo chmod 644 /etc/ssl/certs/photobooth.crt
    sudo chmod 600 /etc/ssl/private/photobooth.key
    sudo chown root:root /etc/ssl/certs/photobooth.crt /etc/ssl/private/photobooth.key
    
    echo "mkcert certificates installed successfully"
    echo "To trust certificates on client devices:"
    echo "1. Install mkcert CA certificate from ~/.local/share/mkcert/"
    echo "2. Or use the trust instructions in scripts/trust_cert_instructions.md"
    
else
    echo "mkcert not found. Using openssl to generate self-signed certificates..."
    
    # Create directories
    sudo mkdir -p /etc/ssl/certs /etc/ssl/private
    
    # Generate private key
    sudo openssl genrsa -out /etc/ssl/private/photobooth.key 2048
    
    # Create certificate signing request config
    cat > /tmp/photobooth.conf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=PhotoBooth
OU=IT
CN=photobooth.local

[v3_req]
basicConstraints = CA:FALSE
keyUsage = keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = photobooth.local
DNS.2 = localhost
IP.1 = 192.168.50.1
IP.2 = 127.0.0.1
EOF
    
    # Generate certificate
    sudo openssl req -new -x509 -key /etc/ssl/private/photobooth.key \
        -out /etc/ssl/certs/photobooth.crt -days 365 \
        -config /tmp/photobooth.conf -extensions v3_req
    
    # Set proper permissions
    sudo chmod 644 /etc/ssl/certs/photobooth.crt
    sudo chmod 600 /etc/ssl/private/photobooth.key
    sudo chown root:root /etc/ssl/certs/photobooth.crt /etc/ssl/private/photobooth.key
    
    # Clean up
    rm /tmp/photobooth.conf
    
    echo "Self-signed certificates generated successfully"
    echo "Note: Clients will need to manually trust the self-signed certificate"
    echo "See scripts/trust_cert_instructions.md for details"
fi

echo "Certificate files:"
echo "  Certificate: /etc/ssl/certs/photobooth.crt"
echo "  Private Key: /etc/ssl/private/photobooth.key"