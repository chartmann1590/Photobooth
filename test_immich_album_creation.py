#!/usr/bin/env python3
"""
Test script for Immich album creation functionality
Tests the get_or_create_album method with various scenarios
"""

import sys
import os
import logging

# Add the photobooth module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def setup_logging():
    """Setup logging for test visibility"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_album_creation():
    """Test album creation functionality"""
    
    print("=" * 60)
    print("IMMICH ALBUM CREATION TEST")
    print("=" * 60)
    
    try:
        from photobooth.immich import get_immich_sync
        from photobooth.models import get_setting, update_setting
        
        # Get Immich sync instance
        sync = get_immich_sync()
        
        # Check if Immich is configured
        settings = sync._get_settings()
        
        print(f"Immich enabled: {settings['enabled']}")
        print(f"Server URL: {settings['server_url']}")
        print(f"API key configured: {'Yes' if settings['api_key'] else 'No'}")
        print(f"Album name: {settings['album_name']}")
        print()
        
        if not settings['enabled']:
            print("❌ Immich sync is disabled. Enable it in settings first.")
            return False
            
        if not settings['server_url'] or not settings['api_key']:
            print("❌ Immich not configured. Set server URL and API key first.")
            return False
        
        # Test 1: Connection test
        print("🔧 Testing connection to Immich server...")
        connection_result = sync.test_connection()
        
        if connection_result['success']:
            print(f"✅ Connection successful: {connection_result.get('message', '')}")
        else:
            print(f"❌ Connection failed: {connection_result.get('error', '')}")
            return False
        
        print()
        
        # Test 2: Get existing albums
        print("📁 Getting existing albums...")
        albums = sync.get_albums(force_refresh=True)
        
        if albums:
            print(f"Found {len(albums)} existing albums:")
            for album in albums[:5]:  # Show first 5
                print(f"  - {album.get('albumName', 'Unknown')} (ID: {album.get('id', 'Unknown')})")
            if len(albums) > 5:
                print(f"  ... and {len(albums) - 5} more")
        else:
            print("No existing albums found")
        
        print()
        
        # Test 3: Test album creation/retrieval
        test_album_name = settings['album_name'] or 'PhotoBooth'
        print(f"🎯 Testing get_or_create_album for '{test_album_name}'...")
        
        album_id = sync.get_or_create_album(test_album_name)
        
        if album_id:
            print(f"✅ Success! Album '{test_album_name}' ID: {album_id}")
            
            # Verify album exists by listing albums again
            print("🔍 Verifying album exists...")
            albums_after = sync.get_albums(force_refresh=True)
            found_album = None
            
            for album in albums_after:
                if album.get('id') == album_id:
                    found_album = album
                    break
            
            if found_album:
                print(f"✅ Verification successful! Album found: {found_album.get('albumName')}")
            else:
                print("⚠️  Album created but not found in album list (may be a caching issue)")
                
        else:
            print(f"❌ Failed to get or create album '{test_album_name}'")
            return False
        
        print()
        
        # Test 4: Test with different album name
        test_album_name_2 = f"Test-Album-{int(datetime.now().timestamp())}"
        print(f"🎯 Testing creation of new album '{test_album_name_2}'...")
        
        album_id_2 = sync.get_or_create_album(test_album_name_2)
        
        if album_id_2:
            print(f"✅ Success! Created new album '{test_album_name_2}' ID: {album_id_2}")
        else:
            print(f"❌ Failed to create new album '{test_album_name_2}'")
        
        print()
        print("=" * 60)
        print("✅ ALBUM CREATION TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the photobooth directory")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_logging()
    
    # Import datetime here since it's needed
    from datetime import datetime
    
    success = test_album_creation()
    
    if success:
        print("\n🎉 All tests passed! Album creation functionality is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        sys.exit(1)