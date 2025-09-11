#!/usr/bin/env python3
"""
Test script to check frame overlay functionality
"""
import os
import sys
import requests
from pathlib import Path

def test_frame_functionality():
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Frame Overlay Functionality")
    print("=" * 50)
    
    # Test 1: Check if frame file exists
    frame_path = "/opt/photobooth/photobooth/static/frames/current.png"
    print(f"📁 Frame file exists: {os.path.exists(frame_path)}")
    if os.path.exists(frame_path):
        stat = os.stat(frame_path)
        print(f"📊 Frame file size: {stat.st_size} bytes")
        print(f"📅 Frame file modified: {stat.st_mtime}")
    
    # Test 2: Test frame API endpoint
    try:
        response = requests.get(f"{base_url}/settings/api/frame/current", timeout=10)
        print(f"🌐 Frame API status: {response.status_code}")
        print(f"📋 Frame API headers: {dict(response.headers)}")
        if response.status_code == 200:
            print(f"📊 Frame API response size: {len(response.content)} bytes")
        else:
            print(f"❌ Frame API error: {response.text}")
    except Exception as e:
        print(f"❌ Frame API request failed: {e}")
    
    # Test 3: Check booth page loads
    try:
        response = requests.get(f"{base_url}/booth/", timeout=10)
        print(f"🏠 Booth page status: {response.status_code}")
        
        # Check for frame overlay element
        if 'frameOverlay' in response.text:
            print("✅ Frame overlay element found in HTML")
        else:
            print("❌ Frame overlay element NOT found in HTML")
            
        # Check for updated JavaScript
        js_response = requests.get(f"{base_url}/static/js/booth.js", timeout=10)
        if 'loadFrameOverlay' in js_response.text:
            print("✅ Updated JavaScript with loadFrameOverlay found")
        else:
            print("❌ Updated JavaScript NOT found")
            
    except Exception as e:
        print(f"❌ Booth page request failed: {e}")
    
    # Test 4: Check CSS for frame overlay styles
    try:
        css_response = requests.get(f"{base_url}/static/css/fixes.css", timeout=10)
        if '#frameOverlay' in css_response.text:
            print("✅ Frame overlay CSS styles found")
        else:
            print("❌ Frame overlay CSS styles NOT found")
    except Exception as e:
        print(f"❌ CSS request failed: {e}")

if __name__ == "__main__":
    test_frame_functionality()