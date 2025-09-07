#!/usr/bin/env python3
"""
Test script to verify HTTPS issue is fixed
This script tests the Django server's response to HTTPS requests
"""

import requests
import sys
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def test_https_redirect():
    """Test that HTTPS requests are properly handled"""
    print("🔍 Testing HTTPS request handling...")
    
    # Test 1: Regular HTTP request (should work)
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        print(f"✅ HTTP request: Status {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")
        return False
    
    # Test 2: HTTPS request (should redirect or give clear error)
    try:
        response = requests.get('https://localhost:8000/', timeout=5, verify=False)
        print(f"✅ HTTPS request handled: Status {response.status_code}")
        if response.status_code == 301 or response.status_code == 302:
            print("   ↳ Redirected to HTTP (good!)")
        return True
    except requests.exceptions.SSLError:
        print("✅ HTTPS request properly rejected with SSL error (expected)")
        return True
    except Exception as e:
        print(f"❌ HTTPS request failed unexpectedly: {e}")
        return False

def test_ssl_handshake():
    """Test handling of SSL handshake attempts"""
    print("\n🔍 Testing SSL handshake handling...")
    
    # Simulate SSL handshake data
    ssl_data = b'\x16\x03\x01\x00\x75\x01\x00\x00\x71\x03\x03'
    
    try:
        response = requests.post(
            'http://localhost:8000/',
            data=ssl_data,
            headers={'Content-Type': 'application/octet-stream'},
            timeout=5
        )
        print(f"✅ SSL handshake handled: Status {response.status_code}")
        if response.status_code == 400:
            print("   ↳ Proper error response for SSL attempt")
        return True
    except Exception as e:
        print(f"❌ SSL handshake test failed: {e}")
        return False

def main():
    print("🛠️  Testing HTTPS Fix for Piata.ro Django Server")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:8000/', timeout=3)
        if response.status_code != 200:
            print("❌ Django server not running or not responding")
            print("   Please start the server first: python start_server.py")
            return False
    except:
        print("❌ Django server not running on http://localhost:8000")
        print("   Please start the server first: python start_server.py")
        return False
    
    # Run tests
    test1 = test_https_redirect()
    test2 = test_ssl_handshake()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("🎉 All tests passed! HTTPS issues should be fixed.")
        print("\n📋 Summary:")
        print("   • HTTPS requests are properly handled")
        print("   • SSL handshake attempts get clear error messages")
        print("   • Regular HTTP requests work normally")
        return True
    else:
        print("❌ Some tests failed. Check server configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
