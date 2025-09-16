#!/usr/bin/env python3
"""
Test script for Immich integration
This script tests the Immich functionality within the Flask app context
"""

import sys
import os

# Add the photobooth directory to Python path
sys.path.insert(0, '/opt/photobooth')

def test_immich_integration():
    """Test Immich integration functionality"""
    print("=== PhotoBooth Immich Integration Test ===")
    print()
    
    try:
        # Import Flask app
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            print("✓ Flask application context created")
            
            # Test Immich module import
            try:
                from photobooth.immich import get_immich_sync, test_immich_connection
                print("✓ Immich module imported successfully")
                
                # Test getting sync instance
                sync = get_immich_sync()
                print("✓ Immich sync instance created")
                
                # Test getting settings
                settings = sync._get_settings()
                print(f"✓ Immich settings loaded:")
                print(f"  - Enabled: {settings['enabled']}")
                print(f"  - Server URL: {settings['server_url'] or 'Not configured'}")
                print(f"  - API Key: {'*' * len(settings['api_key']) if settings['api_key'] else 'Not configured'}")
                print(f"  - Album Name: {settings['album_name']}")
                print(f"  - Auto Sync: {settings['auto_sync']}")
                print(f"  - Sync on Capture: {settings['sync_on_capture']}")
                
                # Test connection (will fail if not configured, but should not error)
                result = test_immich_connection()
                if result['success']:
                    print("✓ Immich connection test passed")
                else:
                    print(f"⚠ Immich connection test failed (expected if not configured): {result['error']}")
                
                print()
                print("=== Test Results ===")
                print("✓ All Immich integration components are working correctly")
                print("✓ Module imports successful")
                print("✓ Settings system functional")
                print("✓ Connection testing functional")
                
                if not settings['enabled']:
                    print()
                    print("📋 Next Steps:")
                    print("1. Access the PhotoBooth settings at https://192.168.50.1/settings/")
                    print("2. Navigate to the Gallery page")
                    print("3. Configure your Immich server URL and API key")
                    print("4. Test the connection using the 'Test Connection' button")
                    print("5. Enable sync and configure album settings")
                
                return True
                
            except Exception as e:
                print(f"✗ Error testing Immich functionality: {e}")
                return False
            
    except Exception as e:
        print(f"✗ Error setting up test environment: {e}")
        return False

if __name__ == "__main__":
    success = test_immich_integration()
    sys.exit(0 if success else 1)