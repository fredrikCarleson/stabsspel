#!/usr/bin/env python3
"""
Test script for download and upload functionality
"""

import requests
import json
import os
import time
from models import skapa_nytt_spel, load_game_data

def test_download_upload():
    """Test the download and upload functionality"""
    print("🧪 Testing Download/Upload Functionality")
    print("=" * 50)
    
    # Create a test game
    print("📝 Creating test game...")
    spel_id = skapa_nytt_spel(
        datum="2024-01-01",
        plats="Test Location",
        antal_spelare=15,
        orderfas_min=10,
        diplomatifas_min=5
    )
    print(f"   ✅ Test game created: {spel_id}")
    
    # Test download endpoint
    print("💾 Testing download endpoint...")
    try:
        response = requests.get(f"http://localhost:5000/admin/download_game/{spel_id}", timeout=10)
        if response.status_code == 200:
            print("   ✅ Download request successful")
            
            # Save the downloaded file
            filename = f"test_download_{spel_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"   ✅ Downloaded file saved as: {filename}")
            
            # Verify the downloaded content
            downloaded_data = json.loads(response.text)
            if downloaded_data.get('id') == spel_id:
                print("   ✅ Downloaded data is valid")
            else:
                print("   ❌ Downloaded data is invalid")
                return False
                
        else:
            print(f"   ❌ Download failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Download request failed: {e}")
        return False
    
    # Test upload endpoint
    print("📤 Testing upload endpoint...")
    try:
        # Read the downloaded file
        with open(filename, 'rb') as f:
            files = {'gameFile': (filename, f, 'application/json')}
            response = requests.post("http://localhost:5000/admin/upload_game", files=files, timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Upload request successful")
            print("   ✅ Upload functionality working")
        else:
            print(f"   ❌ Upload failed with status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Upload request failed: {e}")
        return False
    
    # Clean up
    try:
        os.remove(filename)
        print(f"   🧹 Cleaned up test file: {filename}")
    except:
        print(f"   ⚠️ Could not clean up test file: {filename}")
    
    print("\n🎉 Download/Upload test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_download_upload()
        if success:
            print("\n✅ Download/Upload functionality test passed!")
        else:
            print("\n❌ Download/Upload functionality test failed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")


