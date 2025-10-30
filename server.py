import os
import json
import time
import base64
import threading
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pynput import mouse, keyboard
from PIL import ImageGrab
import socket

class PCMonitorServer:
    def __init__(self, data_dir="monitor_data"):
        # Use executable directory if running as exe
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent
            
        self.data_dir = base_dir / data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.screenshots_dir = self.data_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        self.config_file = base_dir / "config.json"
        
        self.events = []
        self.is_monitoring = False
        self.last_activity = None
        self.screenshot_interval = 15
        self.last_screenshot_path = None
        
        # Load or create config
        self.load_config()
        
    def load_config(self):
        """Load configuration from config.json"""
        default_config = {
            "api_key": "CHANGE_THIS_SECRET_KEY_12345",
            "port": 5000,
            "screenshot_interval": 15,
            "auto_start": True
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.API_KEY = config.get('api_key', default_config['api_key'])
                self.port = config.get('port', default_config['port'])
                self.screenshot_interval = config.get('screenshot_interval', default_config['screenshot_interval'])
                self.auto_start = config.get('auto_start', default_config['auto_start'])
        else:
            # Create default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            self.API_KEY = default_config['api_key']
            self.port = default_config['port']
            self.auto_start = default_config['auto_start']
            print(f"Created config file: {self.config_file}")
            print("Please edit config.json to set your API key!")
    
    def verify_auth(self, request):
        auth_key = request.headers.get('X-API-Key')
        return auth_key == self.API_KEY
    
    def log_event(self, event_type, details):
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details
        }
        self.events.append(event)
        self.last_activity = time.time()
        
        # Save to file
        log_file = self.data_dir / f"events_{datetime.now().strftime('%Y%m%d')}.json"
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + "\n")
    
    def on_mouse_move(self, x, y):
        if self.is_monitoring and time.time() - (self.last_activity or 0) > 5:
            self.log_event("mouse_move", {"x": x, "y": y})
    
    def on_mouse_click(self, x, y, button, pressed):
        if self.is_monitoring and pressed:
            self.log_event("mouse_click", {"x": x, "y": y, "button": str(button)})
    
    def on_key_press(self, key):
        if self.is_monitoring:
            try:
                key_name = key.char if hasattr(key, 'char') else str(key)
            except:
                key_name = str(key)
            self.log_event("key_press", {"key": key_name})
    
    def take_screenshot(self):
        if self.is_monitoring:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = self.screenshots_dir / f"screenshot_{timestamp}.png"
            try:
                img = ImageGrab.grab()
                img.save(screenshot_path)
                self.last_screenshot_path = screenshot_path
                self.log_event("screenshot", {"filename": screenshot_path.name})
                return str(screenshot_path)
            except Exception as e:
                print(f"Screenshot error: {e}")
                return None
    
    def get_latest_screenshot_base64(self):
        if self.last_screenshot_path and self.last_screenshot_path.exists():
            with open(self.last_screenshot_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return None
    
    def monitor_windows(self):
        last_window = None
        while self.is_monitoring:
            try:
                import win32gui
                window = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(window)
                
                if window_title and window_title != last_window:
                    self.log_event("window_change", {"title": window_title})
                    last_window = window_title
            except:
                pass
            time.sleep(2)
    
    def monitor_screenshots(self):
        while self.is_monitoring:
            if self.last_activity and (time.time() - self.last_activity) < 120:
                self.take_screenshot()
            time.sleep(self.screenshot_interval)
    
    def start_monitoring(self):
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.log_event("monitoring_started", {"message": "Monitoring session started"})
        
        # Mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )
        self.mouse_listener.start()
        
        # Keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()
        
        # Window monitor
        self.window_thread = threading.Thread(target=self.monitor_windows, daemon=True)
        self.window_thread.start()
        
        # Screenshot monitor
        self.screenshot_thread = threading.Thread(target=self.monitor_screenshots, daemon=True)
        self.screenshot_thread.start()
    
    def stop_monitoring(self):
        self.is_monitoring = False
        self.log_event("monitoring_stopped", {"message": "Monitoring session stopped"})
    
    def get_recent_events(self, limit=100):
        return self.events[-limit:]
    
    def get_all_screenshots(self):
        screenshots = []
        for file in sorted(self.screenshots_dir.glob("*.png"), reverse=True):
            screenshots.append({
                "filename": file.name,
                "timestamp": file.stat().st_mtime,
                "size": file.stat().st_size
            })
        return screenshots

# Flask Server
app = Flask(__name__)
CORS(app)
monitor = PCMonitorServer()

@app.before_request
def check_auth():
    if request.endpoint in ['status']:
        return None
    if not monitor.verify_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/api/status')
def status():
    return jsonify({
        "monitoring": monitor.is_monitoring,
        "event_count": len(monitor.events),
        "last_activity": monitor.last_activity
    })

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    monitor.start_monitoring()
    return jsonify({"success": True, "message": "Monitoring started"})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    monitor.stop_monitoring()
    return jsonify({"success": True, "message": "Monitoring stopped"})

@app.route('/api/events')
def get_events():
    limit = request.args.get('limit', 100, type=int)
    return jsonify(monitor.get_recent_events(limit))

@app.route('/api/screenshots')
def get_screenshots():
    return jsonify(monitor.get_all_screenshots())

@app.route('/api/screenshot/latest')
def get_latest_screenshot():
    img_data = monitor.get_latest_screenshot_base64()
    if img_data:
        return jsonify({"image": img_data})
    return jsonify({"error": "No screenshot available"}), 404

@app.route('/api/screenshot/<filename>')
def get_screenshot_file(filename):
    file_path = monitor.screenshots_dir / filename
    if file_path.exists():
        return send_file(file_path, mimetype='image/png')
    return jsonify({"error": "File not found"}), 404

@app.route('/api/snapshot', methods=['POST'])
def take_snapshot():
    path = monitor.take_screenshot()
    return jsonify({"success": True, "path": path})

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    monitor.stop_monitoring()
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return jsonify({"success": True, "message": "Server shutting down"})

if __name__ == '__main__':
    # Print connection info
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "Unable to detect"
    
    print("\n" + "="*60)
    print("PC MONITOR SERVER")
    print("="*60)
    print(f"Local IP: {local_ip}")
    print(f"Port: {monitor.port}")
    print(f"API Key: {monitor.API_KEY}")
    print(f"\nConfig file: {monitor.config_file}")
    print(f"Data directory: {monitor.data_dir}")
    print("\nConnect from your laptop using:")
    print(f"  http://{local_ip}:{monitor.port}")
    print("\nIMPORTANT:")
    print("  1. Edit config.json to change your API key")
    print("  2. Open port in Windows Firewall if needed")
    print("  3. Server will run in this window")
    print("="*60 + "\n")
    
    # Auto-start monitoring if configured
    if monitor.auto_start:
        monitor.start_monitoring()
        print("✓ Monitoring started automatically\n")
    
    # Run server
    try:
        app.run(host='0.0.0.0', port=monitor.port, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor.stop_monitoring()