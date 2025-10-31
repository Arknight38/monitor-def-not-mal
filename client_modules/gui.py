"""
Main GUI Application Window
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import json

from .callback_listener import CallbackListener
from .server_tab import PCTab
from .config import load_config, save_config


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
                import datetime
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
        self.add_server_btn = ttk.Button(
            self.control_frame, 
            text="Add Server", 
            command=self.show_add_server_dialog
        )
        self.add_server_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.settings_btn = ttk.Button(
            self.control_frame, 
            text="Settings", 
            command=self.show_settings
        )
        self.settings_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Callback listener button
        self.callback_btn = ttk.Button(
            self.control_frame, 
            text="Callback Listener", 
            command=self.show_callback_settings
        )
        self.callback_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Add a server to begin")
        self.status_bar = ttk.Label(
            self, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

    def show_callback_settings(self):
        """Show callback listener settings dialog"""
        from .dialogs import CallbackSettingsDialog
        CallbackSettingsDialog(self, self.callback_listener)

    def load_servers(self):
        """Load saved server connections"""
        try:
            config = load_config()
            servers = config.get('servers', [])
            for server in servers:
                self.add_server_tab(server['name'], server['url'], server['api_key'])
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

            save_config({'servers': servers})
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
        from .dialogs import AddServerDialog
        AddServerDialog(self)

    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo(
            "Settings", 
            f"Settings file location:\n{os.path.abspath(self.config_file)}\n\n"
            f"Edit manually if needed."
        )

    def get_current_tab(self):
        """Get the currently selected tab"""
        current = self.notebook.select()
        if current:
            return self.notebook.nametowidget(current)
        return None