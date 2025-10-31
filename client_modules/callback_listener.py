"""
Callback Listener - Receives data pushed from servers
Allows servers to auto-register and push updates to client
"""

import json
import os
import secrets
import threading
import datetime
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS


class CallbackListener:
    """Enhanced callback listener - auto-accepts server registrations"""

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

    def load_config(self):
        """Load callback listener configuration"""
        config_file = "callback_listener_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # Default configuration
        default_config = {
            "enabled": True,
            "port": 8080,
            "callback_key": secrets.token_urlsafe(32),
            "auto_update_gui": True,
            "auto_accept_servers": True,
            "require_approval": False
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
        print("CALLBACK LISTENER STARTED")
        print(f"{'='*70}")
        print(f"Listening on: {local_ip}:{port}")
        print(f"Callback Key: {self.config['callback_key']}")
        print(f"\nServers should connect to:")
        print(f"  http://{local_ip}:{port}")
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
        """Run Flask server in background thread using make_server"""
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
        """Handle server registration"""
        try:
            # Verify callback key
            callback_key = request.headers.get('X-Callback-Key')
            if callback_key != self.config['callback_key']:
                print(f"[!] Unauthorized registration attempt")
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
            print(f"NEW SERVER REGISTRATION")
            print(f"{'='*70}")
            print(f"PC Name: {pc_name}")
            print(f"PC ID: {pc_id}")
            print(f"Server URL: {server_url}")
            print(f"Capabilities: {', '.join(k for k, v in capabilities.items() if v)}")

            # Auto-accept if enabled
            if self.config.get('auto_accept_servers', True):
                self.registered_servers[pc_id] = {
                    'name': pc_name,
                    'url': server_url,
                    'api_key': api_key,
                    'registered_at': datetime.datetime.now().isoformat(),
                    'last_seen': datetime.datetime.now().isoformat(),
                    'capabilities': capabilities
                }

                # Schedule GUI update in main thread
                print(f"[*] Scheduling GUI update for {pc_name}")
                try:
                    self.client_app.after(100, lambda: self.add_server_to_gui(pc_name, server_url, api_key))
                except Exception as e:
                    print(f"[!] Error scheduling GUI update: {e}")
                    # Fallback - try direct call
                    try:
                        self.add_server_to_gui(pc_name, server_url, api_key)
                    except Exception as e2:
                        print(f"[!] Direct GUI update also failed: {e2}")

                print(f"Status: AUTO-ACCEPTED")
                print(f"{'='*70}\n")

                return jsonify({
                    "status": "accepted",
                    "message": "Server registered successfully"
                }), 200
            else:
                # Manual approval required
                print(f"Status: PENDING APPROVAL")
                print(f"{'='*70}\n")
                self.client_app.after(0, lambda: self.show_approval_dialog(data))
                return jsonify({
                    "status": "pending",
                    "message": "Waiting for approval"
                }), 202

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
                self.registered_servers[pc_id]['last_seen'] = datetime.datetime.now().isoformat()

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

            # Update GUI if enabled
            if self.config.get('auto_update_gui', True):
                try:
                    self.client_app.after(0, lambda: self.client_app.process_callback_data(data))
                except Exception as e:
                    print(f"Error scheduling GUI update: {e}")
                    # Fallback to direct call
                    try:
                        self.client_app.process_callback_data(data)
                    except Exception as e2:
                        print(f"Direct GUI update failed: {e2}")

            return jsonify({
                "status": "ok",
                "received": True,
                "timestamp": datetime.datetime.now().isoformat(),
                "commands": []
            }), 200

        except Exception as e:
            print(f"Error processing callback: {e}")
            return jsonify({"error": str(e)}), 500

    def add_server_to_gui(self, name, url, api_key):
        """Add server to GUI (called in main thread)"""
        try:
            print(f"[*] Adding server to GUI: {name}")

            # Check if server already exists
            if name in self.client_app.pc_tabs:
                print(f"[!] Server '{name}' already exists in GUI")
                return

            # Add the server tab
            print(f"[*] Creating tab for {name}")
            self.client_app.add_server_tab(name, url, api_key)

            # Save configuration
            print(f"[*] Saving server configuration")
            self.client_app.save_servers()

            # Update status
            self.client_app.update_status_bar(f"New server added: {name}")

            # Show notification
            print(f"[*] Showing notification")
            try:
                from tkinter import messagebox
                messagebox.showinfo(
                    "Server Connected",
                    f"New server '{name}' has been automatically added!\n\n"
                    f"URL: {url}\n\n"
                    f"You can now monitor this PC from the '{name}' tab."
                )
            except Exception as e:
                print(f"Could not show notification: {e}")

            print(f"[*] Server {name} successfully added to GUI")

        except Exception as e:
            print(f"[!] Error adding server to GUI: {e}")
            import traceback
            traceback.print_exc()

    def show_approval_dialog(self, registration_data):
        """Show dialog for manual server approval"""
        try:
            from tkinter import messagebox
            
            pc_name = registration_data.get('pc_name', 'Unknown')
            pc_id = registration_data.get('pc_id')
            server_url = registration_data.get('server_url')
            api_key = registration_data.get('api_key')

            result = messagebox.askyesno(
                "New Server Registration",
                f"A new server wants to connect:\n\n"
                f"Name: {pc_name}\n"
                f"ID: {pc_id}\n"
                f"URL: {server_url}\n\n"
                f"Do you want to accept this connection?"
            )

            if result:
                self.add_server_to_gui(pc_name, server_url, api_key)

        except Exception as e:
            print(f"Error showing approval dialog: {e}")