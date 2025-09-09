#!/bin/bash
# IP forwarding and NAT configuration for PhotoBooth
# This script sets up routing so the Pi can act as a WiFi hotspot

set -e

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Make IP forwarding permanent
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi

# Clear existing iptables rules
iptables -F
iptables -t nat -F
iptables -t mangle -F
iptables -X

# Set default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# NAT rules for internet sharing (if eth0 has internet)
# Only add if eth0 exists and is up
if ip link show eth0 up > /dev/null 2>&1; then
    echo "Setting up NAT for internet sharing via eth0"
    
    # Masquerade outgoing traffic
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    
    # Allow forwarding from wlan0 to eth0
    iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
    iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
fi

# Allow traffic on the loopback interface
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow traffic from the AP network
iptables -A INPUT -s 192.168.50.0/24 -j ACCEPT

# Allow DHCP
iptables -A INPUT -p udp --dport 67 -j ACCEPT
iptables -A INPUT -p udp --dport 68 -j ACCEPT

# Allow DNS
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

# Allow HTTP and HTTPS for the web interface
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH (optional - comment out for security)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

echo "IP forwarding and NAT configured successfully"