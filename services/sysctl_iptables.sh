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

# Internet sharing configuration - detect active interface with internet
INTERNET_INTERFACE=""

# Check for active internet interface in order of preference
for iface in eth0 wlan1 usb0 enp*; do
    # Check if interface exists and is up
    if ip link show $iface up > /dev/null 2>&1; then
        # Check if interface has an IP address
        if ip addr show $iface | grep -q "inet "; then
            # Check if interface has a default route (internet access)
            if ip route show dev $iface | grep -q "default\|0.0.0.0/0"; then
                INTERNET_INTERFACE=$iface
                echo "Found internet interface: $INTERNET_INTERFACE"
                break
            fi
        fi
    fi
done

# Set up NAT for internet sharing if we found an active internet interface
if [ -n "$INTERNET_INTERFACE" ]; then
    echo "Setting up NAT for internet sharing via $INTERNET_INTERFACE"
    
    # Masquerade outgoing traffic from WiFi AP to internet interface
    iptables -t nat -A POSTROUTING -o $INTERNET_INTERFACE -j MASQUERADE
    
    # Allow forwarding from wlan0 (WiFi AP) to internet interface
    iptables -A FORWARD -i wlan0 -o $INTERNET_INTERFACE -j ACCEPT
    iptables -A FORWARD -i $INTERNET_INTERFACE -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
    
    # Log successful setup
    echo "Internet sharing configured: WiFi AP (192.168.50.x) -> $INTERNET_INTERFACE"
else
    echo "No active internet interface found - WiFi AP will work in offline mode"
    echo "Users will still be able to access PhotoBooth at https://192.168.50.1"
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