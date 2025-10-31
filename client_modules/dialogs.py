"""
Dialog Windows for Client GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox


class AddServerDialog:
    """Dialog for adding a new server manually"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Server")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_ui()
    
    def create_ui(self):
        """Create dialog UI"""
        ttk.Label(self.dialog, text="Server Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=5, pady=5)

        ttk.Label(self.dialog, text="Server URL:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_var = tk.StringVar(value="http://192.168.0.48:5000")
        ttk.Entry(self.dialog, textvariable=self.url_var, width=30).grid(
            row=1, column=1, padx=5, pady=5)

        ttk.Label(self.dialog, text="API Key:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.api_key_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.api_key_var, width=30).grid(
            row=2, column=1, padx=5, pady=5)

        ttk.Button(self.dialog, text="Add", command=self.add_server).grid(
            row=3, column=0, columnspan=2, pady=10)

    def add_server(self):
        """Add server to parent application"""
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        api_key = self.api_key_var.get().strip()

        if not name or not url or not api_key:
            messagebox.showerror("Error", "All fields are required")
            return

        self.parent.add_server_tab(name, url, api_key)
        self.parent.save_servers()
        self.dialog.destroy()


class CallbackSettingsDialog:
    """Dialog for callback listener settings"""
    
    def __init__(self, parent, callback_listener):
        self.parent = parent
        self.callback_listener = callback_listener
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Callback Listener Settings")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_ui()
    
    def create_ui(self):
        """Create dialog UI"""
        # Current status
        status_frame = ttk.LabelFrame(self.dialog, text="Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)

        status_text = "ACTIVE" if self.callback_listener.running else "INACTIVE"
        ttk.Label(status_frame, text=f"Status: {status_text}", 
                 font=('Arial', 10, 'bold')).pack(pady=5)

        if self.callback_listener.running:
            ttk.Label(status_frame, 
                     text=f"Listening on port {self.callback_listener.config['port']}").pack()

        # Configuration
        config_frame = ttk.LabelFrame(self.dialog, text="Configuration")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Enabled checkbox
        self.enabled_var = tk.BooleanVar(
            value=self.callback_listener.config.get('enabled', False))
        ttk.Checkbutton(config_frame, text="Enable Callback Listener", 
                       variable=self.enabled_var).grid(
            row=0, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)

        # Port
        ttk.Label(config_frame, text="Port:").grid(
            row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.port_var = tk.StringVar(
            value=str(self.callback_listener.config.get('port', 8080)))
        ttk.Entry(config_frame, textvariable=self.port_var, width=20).grid(
            row=1, column=1, padx=10, pady=5, sticky=tk.W)

        # Callback key
        ttk.Label(config_frame, text="Callback Key:").grid(
            row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.key_var = tk.StringVar(
            value=self.callback_listener.config.get('callback_key', ''))
        key_entry = ttk.Entry(config_frame, textvariable=self.key_var, width=40)
        key_entry.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

        # Copy key button
        ttk.Button(config_frame, text="Copy Key", 
                  command=self.copy_key).grid(row=2, column=2, padx=5, pady=5)

        # Auto-update GUI
        self.auto_update_var = tk.BooleanVar(
            value=self.callback_listener.config.get('auto_update_gui', True))
        ttk.Checkbutton(config_frame, text="Auto-update GUI from callbacks", 
                       variable=self.auto_update_var).grid(
            row=3, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)

        # Auto-accept servers
        self.auto_accept_var = tk.BooleanVar(
            value=self.callback_listener.config.get('auto_accept_servers', True))
        ttk.Checkbutton(config_frame, text="Auto-accept new servers", 
                       variable=self.auto_accept_var).grid(
            row=4, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)

        # Instructions
        info_frame = ttk.LabelFrame(self.dialog, text="Setup Instructions")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        local_ip = self.callback_listener.get_local_ip()
        instructions = (
            f"1. Copy the callback key above\n"
            f"2. On each server PC, edit callback_config.json:\n"
            f'   - Set "enabled": true\n'
            f'   - Set "callback_url": "http://{local_ip}:{self.port_var.get()}"\n'
            f'   - Paste the callback key\n'
            f"3. Restart the server\n"
            f"4. Server will auto-register and appear in a new tab!"
        )
        ttk.Label(info_frame, text=instructions, justify=tk.LEFT).pack(
            padx=10, pady=10)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Save & Apply", 
                  command=self.save_and_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def copy_key(self):
        """Copy callback key to clipboard"""
        try:
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(self.key_var.get())
            messagebox.showinfo("Copied", "Callback key copied to clipboard!")
        except Exception:
            messagebox.showinfo("Key", f"Copy this key:\n\n{self.key_var.get()}")

    def save_and_apply(self):
        """Save settings and apply changes"""
        try:
            self.callback_listener.config['enabled'] = self.enabled_var.get()
            self.callback_listener.config['port'] = int(self.port_var.get())
            self.callback_listener.config['callback_key'] = self.key_var.get()
            self.callback_listener.config['auto_update_gui'] = self.auto_update_var.get()
            self.callback_listener.config['auto_accept_servers'] = self.auto_accept_var.get()

            self.callback_listener.save_config()

            # Start/stop listener based on enabled state
            if self.enabled_var.get() and not self.callback_listener.running:
                self.callback_listener.start()
                self.parent.update_status_bar("Callback listener started")
            elif not self.enabled_var.get() and self.callback_listener.running:
                self.callback_listener.stop()
                self.parent.update_status_bar("Callback listener stopped")

            messagebox.showinfo(
                "Success", 
                "Callback listener settings saved!\n\n"
                "Note: Restart required for port changes."
            )
            self.dialog.destroy()

        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")