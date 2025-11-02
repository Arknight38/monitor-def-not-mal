"""
Unified Client Core Module
Combines configuration, API client, and dialog functionality
"""
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Optional, Any

# Try to use unified config first, fallback to legacy
try:
    from unified_config import unified_config
    UNIFIED_MODE = True
    CONFIG_FILE = "app_config.json"
except ImportError:
    UNIFIED_MODE = False
    CONFIG_FILE = "multi_client_config.json"


class ConfigManager:
    """Unified configuration management for client"""
    
    @staticmethod
    def load_config():
        """Load client configuration"""
        if UNIFIED_MODE:
            config = unified_config.get_multi_client_config()
            if config:
                return config
        
        # Fallback to legacy mode
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return {'servers': []}
        return {'servers': []}
    
    @staticmethod
    def save_config(config):
        """Save client configuration"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False


class APIClient:
    """Unified API client for server communication"""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'MonitorClient/4.0'
        })
        self.last_response = None
        self.connection_healthy = False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            kwargs.setdefault('timeout', self.timeout)
            response = self.session.request(method, url, **kwargs)
            self.last_response = response
            
            if response.status_code == 200:
                self.connection_healthy = True
                try:
                    return response.json()
                except:
                    return {"data": response.text}
            elif response.status_code == 401:
                self.connection_healthy = False
                print("Authentication failed - check API key")
                return None
            else:
                self.connection_healthy = False
                print(f"Request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.connection_healthy = False
            print("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            self.connection_healthy = False
            print("Connection error - server may be offline")
            return None
        except Exception as e:
            self.connection_healthy = False
            print(f"Request error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to server"""
        result = self._make_request('GET', '/api/health')
        return result is not None
    
    def get_system_info(self) -> Optional[Dict]:
        """Get system information from server"""
        return self._make_request('GET', '/api/system-info')
    
    def take_screenshot(self) -> Optional[Dict]:
        """Request screenshot from server"""
        return self._make_request('POST', '/api/screenshot')
    
    def get_recent_screenshots(self, limit: int = 10) -> Optional[List]:
        """Get recent screenshots"""
        return self._make_request('GET', '/api/screenshots', params={'limit': limit})
    
    def get_keystrokes(self, hours: int = 24) -> Optional[List]:
        """Get keystroke logs"""
        return self._make_request('GET', '/api/keystrokes', params={'hours': hours})
    
    def execute_command(self, command: str) -> Optional[Dict]:
        """Execute remote command"""
        return self._make_request('POST', '/api/execute', json={'command': command})
    
    def get_clipboard_history(self) -> Optional[List]:
        """Get clipboard history"""
        return self._make_request('GET', '/api/clipboard')
    
    def set_clipboard(self, text: str) -> Optional[Dict]:
        """Set clipboard content"""
        return self._make_request('POST', '/api/clipboard', json={'text': text})
    
    def get_processes(self) -> Optional[List]:
        """Get running processes"""
        return self._make_request('GET', '/api/processes')
    
    def kill_process(self, pid: int) -> Optional[Dict]:
        """Kill a process"""
        return self._make_request('POST', '/api/processes/kill', json={'pid': pid})
    
    def upload_file(self, file_path: str, destination: str = None) -> Optional[Dict]:
        """Upload file to server"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'destination': destination} if destination else {}
                
                # Don't use session for file upload to avoid content-type conflict
                response = requests.post(
                    f"{self.base_url}/api/upload",
                    files=files,
                    data=data,
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    timeout=self.timeout * 3  # Longer timeout for uploads
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Upload failed: {response.status_code}")
                    return None
        except Exception as e:
            print(f"Upload error: {e}")
            return None
    
    def download_file(self, file_path: str, save_path: str = None) -> bool:
        """Download file from server"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/download",
                params={'path': file_path},
                stream=True
            )
            
            if response.status_code == 200:
                if not save_path:
                    save_path = os.path.basename(file_path)
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return True
            else:
                print(f"Download failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def export_data(self, data_type: str) -> Optional[Dict]:
        """Export data from server"""
        return self._make_request('GET', '/api/export', params={'type': data_type})


class DialogManager:
    """Unified dialog management for client GUI"""
    
    @staticmethod
    def show_add_server_dialog(parent):
        """Show add server dialog"""
        return AddServerDialog(parent)
    
    @staticmethod
    def show_callback_settings_dialog(parent, callback_listener):
        """Show callback settings dialog"""
        return CallbackSettingsDialog(parent, callback_listener)


class AddServerDialog:
    """Dialog for adding a new server manually"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Server")
        self.dialog.geometry("450x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        self.create_ui()
        self.dialog.wait_window()
    
    def create_ui(self):
        """Create dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Server Name
        ttk.Label(main_frame, text="Server Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=5, pady=5)
        
        # Server URL
        ttk.Label(main_frame, text="Server URL:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_var = tk.StringVar(value="http://192.168.1.100:5000")
        ttk.Entry(main_frame, textvariable=self.url_var, width=30).grid(
            row=1, column=1, padx=5, pady=5)
        
        # API Key
        ttk.Label(main_frame, text="API Key:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.api_key_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.api_key_var, width=30, show="*").grid(
            row=2, column=1, padx=5, pady=5)
        
        # Test Connection
        self.test_button = ttk.Button(main_frame, text="Test Connection", 
                                     command=self.test_connection)
        self.test_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Status Label
        self.status_var = tk.StringVar(value="Enter server details above")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Add Server", 
                  command=self.add_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.on_cancel).pack(side=tk.LEFT, padx=5)
    
    def test_connection(self):
        """Test connection to server"""
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        
        if not url or not api_key:
            self.status_var.set("Please enter URL and API key")
            return
        
        self.status_var.set("Testing connection...")
        self.test_button.configure(state='disabled')
        
        def test_in_thread():
            try:
                client = APIClient(url, api_key, timeout=10)
                if client.test_connection():
                    self.status_var.set("✓ Connection successful!")
                else:
                    self.status_var.set("✗ Connection failed")
            except Exception as e:
                self.status_var.set(f"✗ Error: {str(e)[:50]}")
            finally:
                self.test_button.configure(state='normal')
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def add_server(self):
        """Add server to parent application"""
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        
        if not name or not url or not api_key:
            messagebox.showerror("Error", "All fields are required")
            return
        
        self.result = {
            'name': name,
            'url': url,
            'api_key': api_key
        }
        
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle cancel"""
        self.result = None
        self.dialog.destroy()


class CallbackSettingsDialog:
    """Dialog for callback listener settings"""
    
    def __init__(self, parent, callback_listener):
        self.parent = parent
        self.callback_listener = callback_listener
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Callback Listener Settings")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_ui()
    
    def create_ui(self):
        """Create dialog UI"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status Tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="Status")
        self.create_status_tab(status_frame)
        
        # Configuration Tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.create_config_tab(config_frame)
        
        # Instructions Tab
        instructions_frame = ttk.Frame(notebook)
        notebook.add(instructions_frame, text="Setup Guide")
        self.create_instructions_tab(instructions_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save & Apply", 
                  command=self.save_and_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_status_tab(self, parent):
        """Create status tab"""
        status_text = "ACTIVE" if self.callback_listener.running else "INACTIVE"
        status_color = "green" if self.callback_listener.running else "red"
        
        ttk.Label(parent, text=f"Status: {status_text}", 
                 font=('Arial', 12, 'bold')).pack(pady=20)
        
        if self.callback_listener.running:
            ttk.Label(parent, 
                     text=f"Listening on port {self.callback_listener.config['port']}").pack()
            ttk.Label(parent, 
                     text=f"Servers connected: {len(self.callback_listener.connected_servers)}").pack()
        
        # Connection history
        history_frame = ttk.LabelFrame(parent, text="Recent Connections")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # This would show recent connection attempts
        ttk.Label(history_frame, text="Connection history would appear here").pack(pady=20)
    
    def create_config_tab(self, parent):
        """Create configuration tab"""
        # Enabled checkbox
        self.enabled_var = tk.BooleanVar(
            value=self.callback_listener.config.get('enabled', False))
        ttk.Checkbutton(parent, text="Enable Callback Listener", 
                       variable=self.enabled_var).pack(anchor=tk.W, padx=10, pady=10)
        
        # Port configuration
        port_frame = ttk.Frame(parent)
        port_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(
            value=str(self.callback_listener.config.get('port', 8080)))
        ttk.Entry(port_frame, textvariable=self.port_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Callback key
        key_frame = ttk.Frame(parent)
        key_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(key_frame, text="Callback Key:").pack(anchor=tk.W)
        self.key_var = tk.StringVar(
            value=self.callback_listener.config.get('callback_key', ''))
        key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=50)
        key_entry.pack(fill=tk.X, pady=5)
        
        ttk.Button(key_frame, text="Copy Key", 
                  command=self.copy_key).pack(anchor=tk.W, pady=5)
        
        # Additional options
        self.auto_update_var = tk.BooleanVar(
            value=self.callback_listener.config.get('auto_update_gui', True))
        ttk.Checkbutton(parent, text="Auto-update GUI from callbacks", 
                       variable=self.auto_update_var).pack(anchor=tk.W, padx=10, pady=5)
        
        self.auto_accept_var = tk.BooleanVar(
            value=self.callback_listener.config.get('auto_accept_servers', True))
        ttk.Checkbutton(parent, text="Auto-accept new servers", 
                       variable=self.auto_accept_var).pack(anchor=tk.W, padx=10, pady=5)
    
    def create_instructions_tab(self, parent):
        """Create instructions tab"""
        text_widget = tk.Text(parent, wrap=tk.WORD, height=20)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        local_ip = self.callback_listener.get_local_ip()
        instructions = f"""
CALLBACK SYSTEM SETUP GUIDE

1. PREPARATION
   - Ensure this computer (manager/client) is running
   - Note your local IP: {local_ip}
   - Port configured: {self.port_var.get()}

2. COPY CALLBACK KEY
   - Copy the callback key from the Configuration tab
   - You'll need this for each server you want to monitor

3. SERVER CONFIGURATION
   On each server computer:
   
   a) Edit callback_config.json:
      {{
        "enabled": true,
        "callback_url": "http://{local_ip}:{self.port_var.get()}",
        "callback_key": "PASTE_THE_KEY_HERE",
        "interval": 15,
        "retry_interval": 10
      }}
   
   b) Or use DuckDNS (if configured):
      {{
        "enabled": true,
        "callback_url": "http://monitor-client.duckdns.org:8080",
        "callback_key": "PASTE_THE_KEY_HERE"
      }}

4. START SERVERS
   - Restart the server application
   - Server will automatically connect back to this client
   - New tab will appear in the client interface

5. TROUBLESHOOTING
   - Check firewall settings on both computers
   - Ensure port {self.port_var.get()} is open
   - Verify network connectivity
   - Check the Status tab for connection attempts

SECURITY NOTES:
- Callback key acts as authentication
- Change the key regularly for security
- Use DuckDNS for external/remote monitoring
- Monitor the connection log for unauthorized attempts
        """
        
        text_widget.insert(tk.END, instructions)
        text_widget.configure(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def copy_key(self):
        """Copy callback key to clipboard"""
        try:
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(self.key_var.get())
            messagebox.showinfo("Copied", "Callback key copied to clipboard!")
        except Exception:
            messagebox.showinfo("Key", f"Copy this key:\n\n{self.key_var.get()}")
    
    def save_and_apply(self):
        """Save settings and apply changes"""
        try:
            self.callback_listener.config['enabled'] = self.enabled_var.get()
            self.callback_listener.config['port'] = int(self.port_var.get())
            self.callback_listener.config['callback_key'] = self.key_var.get()
            self.callback_listener.config['auto_update_gui'] = self.auto_update_var.get()
            self.callback_listener.config['auto_accept_servers'] = self.auto_accept_var.get()
            
            self.callback_listener.save_config()
            
            # Start/stop listener based on enabled state
            if self.enabled_var.get() and not self.callback_listener.running:
                self.callback_listener.start()
                self.parent.update_status_bar("Callback listener started")
            elif not self.enabled_var.get() and self.callback_listener.running:
                self.callback_listener.stop()
                self.parent.update_status_bar("Callback listener stopped")
            
            messagebox.showinfo(
                "Success", 
                "Callback listener settings saved!\n\n"
                "Note: Restart required for port changes."
            )
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")


# Legacy function compatibility
def load_config():
    """Legacy interface for loading config"""
    return ConfigManager.load_config()

def save_config(config):
    """Legacy interface for saving config"""
    return ConfigManager.save_config(config)