#!/usr/bin/env python3
"""
Test script to diagnose callback connection issues
"""
import json
import requests
import time
from core import ConfigManager

def test_callback_connection():
    """Test if server can connect to client callback"""
    print("=== Callback Connection Test ===")
    
    # Load configurations
    config_manager = ConfigManager()
    callback_config = config_manager.get_callback_config()
    
    print(f"Client callback URL: {callback_config.get('callback_url', 'Not set')}")
    print(f"Client callback key: {callback_config.get('callback_key', 'Not set')[:16]}...")
    
    # Test if callback URL is reachable
    callback_url = callback_config.get('callback_url')
    callback_key = callback_config.get('callback_key')
    
    if not callback_url or not callback_key:
        print("❌ Callback URL or key not configured!")
        return False
    
    # Test heartbeat endpoint
    try:
        print(f"\n🔄 Testing heartbeat to {callback_url}/heartbeat...")
        response = requests.post(
            f"{callback_url}/heartbeat",
            json={"server_id": "test", "timestamp": time.time()},
            headers={'X-Callback-Key': callback_key},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Heartbeat successful!")
            return True
        else:
            print(f"❌ Heartbeat failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - Client callback listener not running or wrong URL")
        return False
    except requests.exceptions.Timeout:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_registration():
    """Test server registration with client"""
    print("\n=== Registration Test ===")
    
    config_manager = ConfigManager()
    callback_config = config_manager.get_callback_config()
    
    callback_url = callback_config.get('callback_url')
    callback_key = callback_config.get('callback_key')
    
    try:
        print(f"🔄 Testing registration to {callback_url}/register...")
        response = requests.post(
            f"{callback_url}/register",
            json={
                "server_id": "test_server",
                "server_name": "Test Server",
                "api_key": "test_api_key",
                "timestamp": time.time()
            },
            headers={'X-Callback-Key': callback_key},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

if __name__ == "__main__":
    # Run tests
    heartbeat_ok = test_callback_connection()
    registration_ok = test_registration()
    
    print(f"\n=== Summary ===")
    print(f"Heartbeat: {'✅' if heartbeat_ok else '❌'}")
    print(f"Registration: {'✅' if registration_ok else '❌'}")
    
    if not heartbeat_ok:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure the client is running with callback listener enabled")
        print("2. Check if the callback URL is correct (IP/hostname and port)")
        print("3. Verify the callback key matches between server and client")
        print("4. Check firewall settings")