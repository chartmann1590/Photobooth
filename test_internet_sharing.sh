#!/bin/bash
# Test script to verify internet sharing through PhotoBooth WiFi AP

echo "=== PhotoBooth Internet Sharing Test ==="
echo

# Test 0: Detect active internet interface
echo "0. Detecting internet interface..."
INTERNET_INTERFACE=""
for iface in eth0 wlan1 usb0 enp*; do
    if ip link show $iface up > /dev/null 2>&1; then
        if ip addr show $iface | grep -q "inet "; then
            if ip route show dev $iface | grep -q "default\|0.0.0.0/0"; then
                INTERNET_INTERFACE=$iface
                echo "✓ Found internet interface: $INTERNET_INTERFACE"
                break
            fi
        fi
    fi
done

if [ -z "$INTERNET_INTERFACE" ]; then
    echo "✗ No active internet interface found"
    echo "   PhotoBooth will work in offline mode only"
else
    echo "   IP Address: $(ip addr show $INTERNET_INTERFACE | grep 'inet ' | awk '{print $2}')"
fi

# Test 1: Check IP forwarding
echo
echo "1. Checking IP forwarding..."
ip_forward=$(cat /proc/sys/net/ipv4/ip_forward)
if [ "$ip_forward" = "1" ]; then
    echo "✓ IP forwarding is enabled"
else
    echo "✗ IP forwarding is disabled"
fi

# Test 2: Check NAT rules
echo
echo "2. Checking NAT rules..."
nat_rules=$(sudo iptables -t nat -L POSTROUTING -n | grep "MASQUERADE")
if [ -n "$nat_rules" ]; then
    echo "✓ NAT masquerading is configured"
    echo "   Rule: $nat_rules"
else
    echo "✗ NAT masquerading not found"
fi

# Test 3: Check forwarding rules
echo
echo "3. Checking forwarding rules..."
forward_rules=$(sudo iptables -L FORWARD -n | grep "ACCEPT")
if [ -n "$forward_rules" ]; then
    echo "✓ Forwarding rules exist"
    echo "   Found $(echo "$forward_rules" | wc -l) ACCEPT rules in FORWARD chain"
else
    echo "✗ Forwarding rules not found"
fi

# Test 4: Check dnsmasq is running
echo
echo "4. Checking dnsmasq service..."
if pgrep dnsmasq > /dev/null; then
    echo "✓ dnsmasq is running"
    
    # Test DNS resolution
    echo
    echo "5. Testing DNS resolution through WiFi AP..."
    if nslookup google.com 192.168.50.1 > /dev/null 2>&1; then
        echo "✓ DNS resolution working through 192.168.50.1"
    else
        echo "✗ DNS resolution failed"
    fi
else
    echo "✗ dnsmasq is not running"
fi

# Test 6: Check network interfaces
echo
echo "6. Network interface status:"
echo "   Ethernet (eth0): $(ip addr show eth0 | grep 'inet ' | awk '{print $2}')"
echo "   WiFi AP (wlan0): $(ip addr show wlan0 | grep 'inet ' | awk '{print $2}')"

echo
echo "=== Test Complete ==="
echo "Users connecting to 'PhotoBooth' WiFi should now have internet access"
echo "while still being able to access the photobooth at https://192.168.50.1"