import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import socket

from .callback_listener import CallbackListener
from .server_tab import PCTab
from .config import load_config, save_config


class PCMonitorAutoClient(tk.Tk):
    """Main client application - 100% auto-callback mode"""

    def __init__(self):
        super().__init__()
        self.title("PC Monitor Manager - Auto Discovery Mode")
        self.geometry("1200x800")
        self.minsize(800, 600)

        self.config_file = "multi_client_config.json"
        self.pc_tabs = {}

        # Create UI first
        self.create_ui()

        # Initialize callback listener
        self.callback_listener = CallbackListener(self)

        # Load any previously connected servers
        self.load_servers()

        # Auto-start callback listener
        if self.callback_listener.start():
            self.show_ready_message()
        else:
            messagebox.showerror(
                "Error",
                "Failed to start callback listener!\n\n"
                "Manager station cannot accept connections."
            )

    def show_ready_message(self):
        """Show first-run setup instructions"""
        local_ip = self.callback_listener.get_local_ip()
        port = self.callback_listener.config['port']
        key = self.callback_listener.config['callback_key']

        instructions = (
            f"🎯 MANAGER STATION READY 🎯\n\n"
            f"This station is now listening for automatic connections.\n"
            f"Servers will appear automatically when they connect!\n\n"
            f"{'='*50}\n\n"
            f"📡 CONNECTION INFO:\n\n"
            f"IP Address: {local_ip}\n"
            f"Port: {port}\n"
            f"Callback Key: {key[:20]}...\n\n"
            f"{'='*50}\n\n"
            f"📝 TO CONNECT A SERVER:\n\n"
            f"1. On target PC, edit callback_config.json:\n\n"
            f'   "enabled": true,\n'
            f'   "callback_url": "http://{local_ip}:{port}",\n'
            f'   "callback_key": "{key}"\n\n'
            f"2. Start/restart the server\n\n"
            f"3. Server will automatically appear in a new tab!\n\n"
            f"{'='*50}\n\n"
            f"✓ No manual configuration needed\n"
            f"✓ Servers auto-register on startup\n"
            f"✓ Automatic reconnection\n"
            f"✓ Real-time updates\n\n"
            f"Ready to accept connections!"
        )

        self.update_status_bar(
            f"🟢 LISTENING on {local_ip}:{port} - Ready for connections"
        )

        try:
            messagebox.showinfo("Manager Station Ready", instructions)
        except Exception:
            print(instructions)

        # Mark as configured
        try:
            with open("auto_callback.configured", 'w') as f:
                import datetime
                f.write(datetime.datetime.now().isoformat())
        except Exception:
            pass

    def process_callback_data(self, data):
        """Process incoming callback data and update GUI"""
        try:
            pc_id = data.get('pc_id')
            
            # Find the matching tab
            for name, tab in self.pc_tabs.items():
                if hasattr(tab, 'last_pc_id') and tab.last_pc_id == pc_id:
                    tab.update_from_callback(data)
                    break

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
        self.control_frame = ttk.LabelFrame(self, text="Manager Station")
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Connection info button
        self.info_btn = ttk.Button(
            self.control_frame,
            text="📡 Connection Info",
            command=self.show_connection_info
        )
        self.info_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Settings button
        self.settings_btn = ttk.Button(
            self.control_frame,
            text="⚙️ Settings",
            command=self.show_settings
        )
        self.settings_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Refresh all button
        self.refresh_btn = ttk.Button(
            self.control_frame,
            text="🔄 Refresh All",
            command=self.refresh_all_tabs
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Server count label
        self.server_count_var = tk.StringVar(value="Servers: 0")
        self.server_count_label = ttk.Label(
            self.control_frame,
            textvariable=self.server_count_var,
            font=('Arial', 10, 'bold')
        )
        self.server_count_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Starting manager station...")
        self.status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

    def show_connection_info(self):
        """Show connection information dialog"""
        local_ip = self.callback_listener.get_local_ip()
        port = self.callback_listener.config['port']
        key = self.callback_listener.config['callback_key']

        info = (
            f"MANAGER STATION CONNECTION INFO\n\n"
            f"{'='*50}\n\n"
            f"Listening Address: {local_ip}:{port}\n\n"
            f"Callback Key:\n{key}\n\n"
            f"{'='*50}\n\n"
            f"SERVER CONFIGURATION:\n\n"
            f"Edit callback_config.json on each target PC:\n\n"
            f'{{\n'
            f'  "enabled": true,\n'
            f'  "callback_url": "http://{local_ip}:{port}",\n'
            f'  "callback_key": "{key}",\n'
            f'  "interval": 15\n'
            f'}}\n\n'
            f"Then start/restart the server.\n"
            f"It will automatically appear here!"
        )

        messagebox.showinfo("Connection Information", info)

        # Also copy to clipboard
        try:
            self.clipboard_clear()
            self.clipboard_append(key)
            messagebox.showinfo(
                "Copied",
                "Callback key copied to clipboard!"
            )
        except:
            pass

    def show_settings(self):
        """Show settings dialog"""
        from .dialogs import CallbackSettingsDialog
        CallbackSettingsDialog(self, self.callback_listener)

    def refresh_all_tabs(self):
        """Refresh all server tabs"""
        for tab in self.pc_tabs.values():
            try:
                tab.refresh()
            except Exception as e:
                print(f"Error refreshing tab: {e}")

        self.update_status_bar(
            f"✓ Refreshed {len(self.pc_tabs)} server(s)"
        )

    def load_servers(self):
        """Load previously connected servers from config"""
        try:
            config = load_config()
            servers = config.get('servers', [])

            if servers:
                print(f"[*] Loading {len(servers)} previously connected servers...")

            for server in servers:
                self.add_server_tab(
                    server['name'],
                    server['url'],
                    server['api_key']
                )

            self.update_server_count()

        except Exception as e:
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
            print(f"Failed to save servers: {e}")

    def add_server_tab(self, name, url, api_key):
        """Add a new server tab"""
        try:
            # Check if server already exists
            if name in self.pc_tabs:
                print(f"[!] Server '{name}' already exists")
                return self.pc_tabs[name]

            print(f"[*] Creating tab for {name}")

            # Create tab
            tab = PCTab(self.notebook, self, name, url, api_key)
            self.notebook.add(tab, text=f"🖥️ {name}")
            self.pc_tabs[name] = tab

            # Update count
            self.update_server_count()

            # Save configuration
            self.save_servers()

            print(f"[*] Tab created and added: {name}")
            return tab

        except Exception as e:
            print(f"[!] Error creating tab: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_server_count(self):
        """Update server count display"""
        count = len(self.pc_tabs)
        self.server_count_var.set(f"Servers: {count}")

        if count == 0:
            self.update_status_bar(
                "🟡 Waiting for servers to connect..."
            )
        else:
            self.update_status_bar(
                f"🟢 {count} server(s) connected"
            )

    def get_current_tab(self):
        """Get the currently selected tab"""
        current = self.notebook.select()
        if current:
            return self.notebook.nametowidget(current)
        return None

    def remove_server_tab(self, name):
        """Remove a server tab"""
        if name in self.pc_tabs:
            tab = self.pc_tabs[name]

            # Find tab index
            for i in range(self.notebook.index('end')):
                if self.notebook.tab(i, 'text') == f"🖥️ {name}":
                    self.notebook.forget(i)
                    break

            # Remove from dictionary
            del self.pc_tabs[name]

            # Update count
            self.update_server_count()

            # Save configuration
            self.save_servers()

            print(f"[*] Removed server: {name}")