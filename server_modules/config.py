"""
Configuration Management - Fixed version
Exports config, pc_id, and API_KEY properly
"""
import json
import os
import secrets
from pathlib import Path

CONFIG_FILE = "config.json"
DATA_DIR = Path("monitor_data")
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
OFFLINE_LOGS_DIR = DATA_DIR / "offline_logs"

def ensure_directories():
    """Create necessary directories"""
    DATA_DIR.mkdir(exist_ok=True)
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    OFFLINE_LOGS_DIR.mkdir(exist_ok=True)

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    
    # Generate default config
    config = {
        "api_key": secrets.token_urlsafe(32),
        "port": 5000,
        "host": "0.0.0.0",
        "auto_screenshot": False,
        "screenshot_interval": 300,
        "motion_detection": False,
        "data_retention_days": 30,
        "pc_id": secrets.token_hex(8),
        "pc_name": os.environ.get('COMPUTERNAME', 'Unknown-PC')
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"\n{'='*70}")
    print("FIRST TIME SETUP - Configuration Created")
    print(f"{'='*70}")
    print(f"API Key: {config['api_key']}")
    print(f"Port: {config['port']}")
    print(f"\nSave this API key - you'll need it in the client!")
    print(f"{'='*70}\n")
    
    return config

def load_callback_config():
    """Load callback configuration"""
    callback_file = Path("callback_config.json")
    
    if callback_file.exists():
        try:
            with open(callback_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    default_config = {
        "enabled": False,
        "callback_url": "http://YOUR_CLIENT_IP:8080",
        "callback_key": "COPY_FROM_CLIENT",
        "interval": 15,
        "heartbeat_interval": 5,
        "retry_interval": 10
    }
    
    with open(callback_file, 'w') as f:
        json.dump(default_config, f, indent=4)
    
    return default_config

# Initialize directories
ensure_directories()

# Load configuration
config = load_config()
pc_id = config['pc_id']
API_KEY = config['api_key']