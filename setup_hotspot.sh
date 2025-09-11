#!/bin/bash
# PhotoBooth Hotspot Setup Script
# Ensures WiFi interface is properly configured for AP mode

set -e

echo "Setting up PhotoBooth hotspot..."

# Stop NetworkManager from managing wlan0
if systemctl is-active --quiet NetworkManager; then
    echo "Ensuring NetworkManager ignores wlan0..."
    if [ ! -f /etc/NetworkManager/conf.d/99-photobooth.conf ]; then
        echo '[keyfile]
unmanaged-devices=interface-name:wlan0' > /etc/NetworkManager/conf.d/99-photobooth.conf
        systemctl restart NetworkManager
        sleep 2
    fi
fi

# Stop any existing wpa_supplicant processes
killall wpa_supplicant 2>/dev/null || true

# Configure wlan0 interface
echo "Configuring wlan0 interface..."
ip link set wlan0 down
sleep 1
ip link set wlan0 up
sleep 1

# Set static IP for AP
ip addr flush dev wlan0
ip addr add 192.168.50.1/24 dev wlan0

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Set up NAT rules
iptables -t nat -F
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

# Start services in correct order
systemctl start hostapd
sleep 2
systemctl start dnsmasq

echo "PhotoBooth hotspot setup complete!"
echo "SSID: PhotoBooth"
echo "Password: photobooth123"
echo "Gateway: 192.168.50.1"