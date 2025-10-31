"""
Client Configuration Management
"""

import json
import os

CONFIG_FILE = "multi_client_config.json"


def load_config():
    """Load client configuration"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {'servers': []}
    return {'servers': []}


def save_config(config):
    """Save client configuration"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False