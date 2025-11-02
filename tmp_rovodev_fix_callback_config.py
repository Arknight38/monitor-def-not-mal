#!/usr/bin/env python3
"""
Fix callback configuration to use local IP
"""
import socket
from core import ConfigManager

def get_local_ip():
    """Get local IP address"""
    try:
        # Connect to a remote server to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

def fix_callback_config():
    """Fix callback configuration to use local IP"""
    print("=== Fixing Callback Configuration ===")
    
    config_manager = ConfigManager()
    local_ip = get_local_ip()
    
    print(f"Local IP detected: {local_ip}")
    
    # Get current config
    current_config = config_manager.get_callback_config()
    print(f"Current callback URL: {current_config.get('callback_url')}")
    
    # Update to use local IP
    new_url = f"http://{local_ip}:8080"
    config_manager.set_duckdns_url(local_ip, 8080)  # Use local IP
    
    # Get updated config
    updated_config = config_manager.get_callback_config()
    print(f"New callback URL: {updated_config.get('callback_url')}")
    print(f"Callback key: {updated_config.get('callback_key')[:16]}...")
    
    print("\n✅ Configuration updated!")
    print(f"\n📋 Server configuration needed:")
    print(f'{{')
    print(f'  "callback": {{')
    print(f'    "callback_url": "{updated_config.get("callback_url")}",')
    print(f'    "callback_key": "{updated_config.get("callback_key")}"')
    print(f'  }}')
    print(f'}}')

if __name__ == "__main__":
    fix_callback_config()