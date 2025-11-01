import json
import os
import secrets
import threading
import datetime
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS


class CallbackListener:
    """Enhanced callback listener - fully automatic server discovery"""

    def __init__(self, client_app):
        self.client_app = client_app
        self.app = Flask(__name__)
        CORS(self.app)
        self.running = False
        self.thread = None
        self.server = None
        self.config = self.load_config()
        self.registered_servers = {}

        # Setup Flask routes
        @self.app.route('/register', methods=['POST'])
        def handle_registration():
            return self.receive_registration()

        @self.app.route('/callback', methods=['POST'])
        def handle_callback():
            return self.receive_callback()

        @self.app.route('/heartbeat', methods=['POST'])
        def handle_heartbeat():
            return self.receive_heartbeat()

        @self.app.route('/status', methods=['GET'])
        def handle_status():
            return self.get_status()

    def load_config(self):
        """Load callback listener configuration"""
        config_file = "callback_listener_config.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                    # Ensure required fields exist
                    if 'callback_key' not in config:
                        config['callback_key'] = secrets.token_urlsafe(32)

                    return config
            except Exception:
                pass

        # Default configuration - fully automatic
        default_config = {
            "enabled": True,
            "port": 8080,
            "callback_key": secrets.token_urlsafe(32),
            "auto_accept_servers": True,  # Always auto-accept
            "auto_update_gui": True,
            "require_approval": False,
            "show_notifications": True,
            "auto_refresh_interval": 30
        }

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
        except Exception:
            pass

        return default_config

    def save_config(self):
        """Save callback listener configuration"""
        try:
            with open("callback_listener_config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving callback config: {e}")

    def start(self):
        """Start the callback listener"""
        if self.running:
            return False

        if not self.config.get('enabled', False):
            return False

        self.running = True
        self.thread = Thread(target=self._run_server, daemon=True)
        self.thread.start()

        local_ip = self.get_local_ip()
        port = self.config['port']

        print(f"\n{'='*70}")
        print("🎯 AUTO-CALLBACK LISTENER STARTED")
        print(f"{'='*70}")
        print(f"Listening on: {local_ip}:{port}")
        print(f"Callback Key: {self.config['callback_key']}")
        print(f"\nServers will automatically connect!")
        print(f"Mode: 100% Automatic Discovery")
        print(f"{'='*70}\n")

        return True

    def get_local_ip(self):
        """Get local IP address"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def stop(self):
        """Stop the callback listener"""
        self.running = False
        try:
            if hasattr(self, 'server') and self.server:
                self.server.shutdown()
        except Exception:
            pass
        print("Callback listener stopped")

    def _run_server(self):
        """Run Flask server in background thread"""
        try:
            from werkzeug.serving import make_server
            host = '0.0.0.0'
            port = int(self.config.get('port', 8080))
            self.server = make_server(host, port, self.app, threaded=True)
            self.server.serve_forever()
        except Exception as e:
            print(f"Callback listener error: {e}")
            self.running = False

    def receive_registration(self):
        """Handle server registration - AUTOMATIC"""
        try:
            # Verify callback key
            callback_key = request.headers.get('X-Callback-Key')
            if callback_key != self.config['callback_key']:
                print(f"[!] ⚠️  Unauthorized registration attempt")
                return jsonify({"error": "Unauthorized", "status": "rejected"}), 401

            data = request.json

            if not data or data.get('type') != 'register':
                print(f"[!] Invalid registration data")
                return jsonify({"error": "Invalid registration"}), 400

            pc_id = data.get('pc_id')
            pc_name = data.get('pc_name', 'Unknown')
            server_url = data.get('server_url')
            api_key = data.get('api_key')
            capabilities = data.get('capabilities', {})

            print(f"\n{'='*70}")
            print(f"🆕 NEW SERVER AUTO-REGISTRATION")
            print(f"{'='*70}")
            print(f"PC Name: {pc_name}")
            print(f"PC ID: {pc_id}")
            print(f"Server URL: {server_url}")
            print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # ALWAYS auto-accept (100% automatic mode)
            self.registered_servers[pc_id] = {
                'name': pc_name,
                'url': server_url,
                'api_key': api_key,
                'registered_at': datetime.datetime.now().isoformat(),
                'last_seen': datetime.datetime.now().isoformat(),
                'capabilities': capabilities,
                'status': 'active'
            }

            # Schedule GUI update in main thread
            print(f"[*] 📊 Adding server to GUI...")
            try:
                self.client_app.after(
                    100,
                    lambda: self.add_server_to_gui(pc_name, server_url, api_key)
                )
            except Exception as e:
                print(f"[!] Error scheduling GUI update: {e}")

            print(f"Status: ✅ AUTO-ACCEPTED")
            print(f"{'='*70}\n")

            return jsonify({
                "status": "accepted",
                "message": "Server registered automatically",
                "client_info": {
                    "manager_name": "Auto-Discovery Manager",
                    "auto_mode": True
                }
            }), 200

        except Exception as e:
            print(f"[!] Registration error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e), "status": "error"}), 500

    def receive_heartbeat(self):
        """Handle heartbeat from server"""
        try:
            callback_key = request.headers.get('X-Callback-Key')
            if callback_key != self.config['callback_key']:
                return jsonify({"error": "Unauthorized"}), 401

            data = request.json or {}
            pc_id = data.get('pc_id')

            if pc_id in self.registered_servers:
                self.registered_servers[pc_id]['last_seen'] = \
                    datetime.datetime.now().isoformat()
                self.registered_servers[pc_id]['status'] = 'active'

            return jsonify({"status": "ok"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def receive_callback(self):
        """Handle incoming callback from server"""
        try:
            callback_key = request.headers.get('X-Callback-Key')
            if callback_key != self.config['callback_key']:
                return jsonify({"error": "Unauthorized"}), 401

            data = request.json

            if not data:
                return jsonify({"error": "No data received"}), 400

            pc_id = data.get('pc_id')

            # Update last seen
            if pc_id in self.registered_servers:
                self.registered_servers[pc_id]['last_seen'] = \
                    datetime.datetime.now().isoformat()

            # Update GUI if enabled
            if self.config.get('auto_update_gui', True):
                try:
                    self.client_app.after(
                        0,
                        lambda: self.client_app.process_callback_data(data)
                    )
                except Exception as e:
                    print(f"Error scheduling GUI update: {e}")

            return jsonify({
                "status": "ok",
                "received": True,
                "timestamp": datetime.datetime.now().isoformat(),
                "commands": []
            }), 200

        except Exception as e:
            print(f"Error processing callback: {e}")
            return jsonify({"error": str(e)}), 500

    def get_status(self):
        """Get current status of callback listener"""
        try:
            return jsonify({
                "status": "active" if self.running else "inactive",
                "registered_servers": len(self.registered_servers),
                "servers": {
                    pc_id: {
                        "name": info['name'],
                        "url": info['url'],
                        "status": info['status'],
                        "last_seen": info['last_seen']
                    }
                    for pc_id, info in self.registered_servers.items()
                },
                "config": {
                    "auto_accept": self.config.get('auto_accept_servers', True),
                    "port": self.config['port']
                }
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def add_server_to_gui(self, name, url, api_key):
        """Add server to GUI (called in main thread)"""
        try:
            print(f"[*] 🖥️  Adding server to GUI: {name}")

            # Check if server already exists
            if name in self.client_app.pc_tabs:
                print(f"[!] Server '{name}' already exists in GUI")
                # Update existing connection
                tab = self.client_app.pc_tabs[name]
                tab.server_url = url
                tab.api_key = api_key
                return

            # Add the server tab
            print(f"[*] Creating new tab for {name}")
            self.client_app.add_server_tab(name, url, api_key)

            # Update status
            self.client_app.update_status_bar(
                f"✅ New server connected: {name}"
            )

            # Show notification
            if self.config.get('show_notifications', True):
                print(f"[*] Showing connection notification")
                try:
                    from tkinter import messagebox
                    messagebox.showinfo(
                        "Server Connected",
                        f"✅ New server auto-connected!\n\n"
                        f"Name: {name}\n"
                        f"URL: {url}\n\n"
                        f"The server is now being monitored from\n"
                        f"the '{name}' tab."
                    )
                except Exception as e:
                    print(f"Could not show notification: {e}")

            print(f"[*] ✅ Server {name} successfully added to GUI")

        except Exception as e:
            print(f"[!] Error adding server to GUI: {e}")
            import traceback
            traceback.print_exc()

    def get_registered_servers(self):
        """Get list of all registered servers"""
        return self.registered_servers.copy()

    def check_server_health(self):
        """Check health of all registered servers"""
        now = datetime.datetime.now()

        for pc_id, info in self.registered_servers.items():
            try:
                last_seen = datetime.datetime.fromisoformat(info['last_seen'])
                age = (now - last_seen).total_seconds()

                # Mark as inactive if no heartbeat for 2 minutes
                if age > 120:
                    if info['status'] != 'inactive':
                        info['status'] = 'inactive'
                        print(f"[!] Server {info['name']} marked as inactive")

            except Exception:
                pass