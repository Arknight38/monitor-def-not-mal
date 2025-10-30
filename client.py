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
        return Path(sys.executable).parent / "multi_client_config.json"
    else:
        return Path(__file__).parent / "multi_client_config.json"

def load_multi_config():
    """Load multi-client configuration"""
    config_path = get_config_path()
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Return defaults with sample servers
    return {
        "servers": []
    }

def save_multi_config(config):
    """Save multi-client configuration"""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

class PCMonitorClient:
    def __init__(self, server_url, api_key, pc_name="Unknown"):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.pc_name = pc_name
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
        try:
            resp = self.session.post(f"{self.server_url}/api/kill", headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_events(self, limit=50):
        try:
            resp = self.session.get(f"{self.server_url}/api/events", 
                                   headers=self.headers, params={'limit': limit}, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return []
    
    def get_latest_screenshot(self):
        try:
            resp = self.session.get(f"{self.server_url}/api/screenshot/latest", 
                                   headers=self.headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if 'image' in data:
                return base64.b64decode(data['image'])
            return None
        except Exception as e:
            return None
    
    def take_snapshot(self):
        try:
            resp = self.session.post(f"{self.server_url}/api/snapshot", 
                                    headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def execute_command(self, cmd_type, **kwargs):
        try:
            data = {"type": cmd_type, **kwargs}
            resp = self.session.post(f"{self.server_url}/api/command", 
                                    headers=self.headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

class PCTab:
    """Individual tab for monitoring one PC"""
    def __init__(self, parent, client, remove_callback):
        self.frame = ttk.Frame(parent)
        self.client = client
        self.remove_callback = remove_callback
        self.is_active = False
        self.current_image = None
        
        self.create_ui()
    
    def create_ui(self):
        # Control bar
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(control_frame, text="Checking...", font=("Arial", 10, "bold"))
        self.status_label.pack(side="left", padx=10)
        
        self.info_label = ttk.Label(control_frame, text="", font=("Arial", 9))
        self.info_label.pack(side="left", padx=10)
        
        ttk.Button(control_frame, text="Start", command=self.start_monitoring).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Stop", command=self.stop_monitoring).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Snapshot", command=self.take_snapshot).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Command", command=self.show_commands).pack(side="left", padx=2)
        
        # Remove button
        ttk.Button(control_frame, text="❌ Remove", command=self.remove_tab).pack(side="right", padx=5)
        
        # Paned window for layout
        paned = ttk.PanedWindow(self.frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left: Screenshot
        left_frame = ttk.LabelFrame(paned, text="Live View", padding=10)
        paned.add(left_frame, weight=2)
        
        self.screenshot_label = ttk.Label(left_frame, text="No screenshot", background="gray")
        self.screenshot_label.pack(fill="both", expand=True)
        
        ttk.Button(left_frame, text="Refresh Screenshot", 
                  command=self.refresh_screenshot).pack(pady=5)
        
        # Right: Activity log
        right_frame = ttk.LabelFrame(paned, text="Activity Log", padding=10)
        paned.add(right_frame, weight=1)
        
        self.events_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, 
                                                     height=30, font=("Consolas", 9))
        self.events_text.pack(fill="both", expand=True)
        
        ttk.Button(right_frame, text="Refresh Events", 
                  command=self.refresh_events).pack(pady=5)
    
    def update_status(self):
        """Update status display"""
        def _update():
            status = self.client.get_status()
            
            def _display():
                if 'error' in status:
                    self.status_label.config(text=f"❌ {status['error']}", foreground="red")
                    self.info_label.config(text="")
                else:
                    mon_status = "🟢 ACTIVE" if status.get('monitoring') else "🔴 STOPPED"
                    self.status_label.config(text=mon_status, 
                                           foreground="green" if status.get('monitoring') else "red")
                    
                    pc_name = status.get('pc_name', 'Unknown')
                    event_count = status.get('event_count', 0)
                    self.info_label.config(text=f"PC: {pc_name} | Events: {event_count}")
            
            if self.frame.winfo_exists():
                self.frame.after(0, _display)
        
        threading.Thread(target=_update, daemon=True).start()
    
    def refresh_screenshot(self):
        """Refresh screenshot display"""
        def _update():
            img_data = self.client.get_latest_screenshot()
            
            def _display():
                if img_data and self.frame.winfo_exists():
                    try:
                        img = Image.open(io.BytesIO(img_data))
                        img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.current_image = photo
                        self.screenshot_label.config(image=photo, text="")
                    except Exception as e:
                        self.screenshot_label.config(text=f"Error: {e}", image="")
                else:
                    self.screenshot_label.config(text="No screenshot", image="")
            
            if self.frame.winfo_exists():
                self.frame.after(0, _display)
        
        threading.Thread(target=_update, daemon=True).start()
    
    def refresh_events(self):
        """Refresh events display"""
        def _update():
            events = self.client.get_events(limit=50)
            
            def _display():
                if self.frame.winfo_exists():
                    self.events_text.delete(1.0, tk.END)
                    
                    for event in reversed(events[-30:]):
                        timestamp = event.get('timestamp', '')
                        event_type = event.get('type', '')
                        details = event.get('details', {})
                        
                        self.events_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                        self.events_text.insert(tk.END, f"{event_type.upper()}\n", "type")
                        
                        if details:
                            detail_str = json.dumps(details, indent=2)
                            self.events_text.insert(tk.END, f"  {detail_str}\n\n")
                    
                    self.events_text.tag_config("timestamp", foreground="gray")
                    self.events_text.tag_config("type", foreground="blue", font=("Consolas", 9, "bold"))
            
            if self.frame.winfo_exists():
                self.frame.after(0, _display)
        
        threading.Thread(target=_update, daemon=True).start()
    
    def start_monitoring(self):
        def _start():
            result = self.client.start_monitoring()
            
            def _show():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", f"Monitoring started on {self.client.pc_name}")
                self.update_status()
            
            if self.frame.winfo_exists():
                self.frame.after(0, _show)
        
        threading.Thread(target=_start, daemon=True).start()
    
    def stop_monitoring(self):
        def _stop():
            result = self.client.stop_monitoring()
            
            def _show():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", f"Monitoring stopped on {self.client.pc_name}")
                self.update_status()
            
            if self.frame.winfo_exists():
                self.frame.after(0, _show)
        
        threading.Thread(target=_stop, daemon=True).start()
    
    def take_snapshot(self):
        def _snap():
            result = self.client.take_snapshot()
            
            def _show():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", f"Snapshot saved: {result.get('filename')}")
                self.refresh_screenshot()
            
            if self.frame.winfo_exists():
                self.frame.after(0, _show)
        
        threading.Thread(target=_snap, daemon=True).start()
    
    def show_commands(self):
        """Show remote command dialog"""
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Remote Control - {self.client.pc_name}")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text=f"Remote Control: {self.client.pc_name}", 
                 font=("Arial", 11, "bold")).pack(pady=10)
        
        # System commands
        cmd_frame = ttk.LabelFrame(dialog, text="System Commands", padding=10)
        cmd_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(cmd_frame, text="Shutdown PC", 
                  command=lambda: self.execute_cmd('shutdown')).pack(fill="x", pady=5)
        ttk.Button(cmd_frame, text="Restart PC", 
                  command=lambda: self.execute_cmd('restart')).pack(fill="x", pady=5)
        
        # Launch app
        launch_frame = ttk.LabelFrame(dialog, text="Launch Application", padding=10)
        launch_frame.pack(fill="x", padx=10, pady=10)
        
        app_entry = ttk.Entry(launch_frame, width=40)
        app_entry.insert(0, "notepad.exe")
        app_entry.pack(pady=5)
        
        ttk.Button(launch_frame, text="Launch", 
                  command=lambda: self.execute_cmd('launch', path=app_entry.get())).pack()
    
    def execute_cmd(self, cmd_type, **kwargs):
        """Execute remote command"""
        def _exec():
            result = self.client.execute_command(cmd_type, **kwargs)
            
            def _show():
                if 'error' in result:
                    messagebox.showerror("Error", result['error'])
                else:
                    messagebox.showinfo("Success", f"Command executed: {result.get('status')}")
            
            if self.frame.winfo_exists():
                self.frame.after(0, _show)
        
        threading.Thread(target=_exec, daemon=True).start()
    
    def remove_tab(self):
        """Remove this tab"""
        if messagebox.askyesno("Confirm", f"Remove {self.client.pc_name} from monitoring?"):
            self.remove_callback(self)
    
    def refresh_all(self):
        """Refresh all data"""
        self.update_status()
        self.refresh_screenshot()
        self.refresh_events()

class MultiPCMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-PC Monitor Dashboard")
        self.root.geometry("1600x900")
        
        self.config = load_multi_config()
        self.pc_tabs = {}
        self.is_running = True
        
        self.create_menu()
        self.create_ui()
        
        # Load saved servers
        self.load_saved_servers()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start auto-refresh
        self.start_auto_refresh()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Server", command=self.add_server_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dashboard Overview", command=self.show_dashboard)
        view_menu.add_command(label="Refresh All", command=self.refresh_all_tabs)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_ui(self):
        # Top control bar
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(control_frame, text="Multi-PC Monitor Dashboard", 
                 font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        ttk.Button(control_frame, text="➕ Add Server", 
                  command=self.add_server_dialog).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh All", 
                  command=self.refresh_all_tabs).pack(side="left", padx=5)
        ttk.Button(control_frame, text="📊 Dashboard", 
                  command=self.show_dashboard).pack(side="left", padx=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Auto-refresh (15s)", 
                       variable=self.auto_refresh_var).pack(side="right", padx=10)
        
        # Notebook for PC tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Welcome tab
        self.create_welcome_tab()
    
    def create_welcome_tab(self):
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="Welcome")
        
        ttk.Label(welcome_frame, text="Multi-PC Monitor Dashboard", 
                 font=("Arial", 16, "bold")).pack(pady=30)
        
        ttk.Label(welcome_frame, text="Monitor multiple PCs simultaneously", 
                 font=("Arial", 11)).pack(pady=10)
        
        ttk.Label(welcome_frame, text="Click 'Add Server' to begin", 
                 font=("Arial", 10, "italic")).pack(pady=10)
        
        ttk.Button(welcome_frame, text="➕ Add Your First Server", 
                  command=self.add_server_dialog).pack(pady=20)
    
    def add_server_dialog(self):
        """Show dialog to add new server"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Server")
        dialog.geometry("450x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Add New Server", font=("Arial", 12, "bold")).pack(pady=10)
        
        # PC Name
        ttk.Label(dialog, text="PC Name (for identification):").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        name_entry.insert(0, f"PC-{len(self.pc_tabs)+1}")
        
        # Server URL
        ttk.Label(dialog, text="Server URL:").pack(pady=5)
        url_entry = ttk.Entry(dialog, width=40)
        url_entry.pack(pady=5)
        url_entry.insert(0, "http://192.168.1.100:5000")
        
        # API Key
        ttk.Label(dialog, text="API Key:").pack(pady=5)
        key_entry = ttk.Entry(dialog, width=40, show="*")
        key_entry.pack(pady=5)
        
        show_var = tk.BooleanVar(value=False)
        def toggle_show():
            key_entry.config(show="" if show_var.get() else "*")
        ttk.Checkbutton(dialog, text="Show API Key", variable=show_var, 
                       command=toggle_show).pack(pady=5)
        
        def save_server():
            pc_name = name_entry.get().strip()
            server_url = url_entry.get().strip()
            api_key = key_entry.get().strip()
            
            if not pc_name or not server_url or not api_key:
                messagebox.showerror("Error", "All fields are required!")
                return
            
            # Add to config
            self.config['servers'].append({
                "pc_name": pc_name,
                "server_url": server_url,
                "api_key": api_key
            })
            save_multi_config(self.config)
            
            # Create client and tab
            self.add_pc_tab(server_url, api_key, pc_name)
            
            dialog.destroy()
            messagebox.showinfo("Success", f"Added {pc_name}!")
        
        ttk.Button(dialog, text="Add Server", command=save_server).pack(pady=20)
    
    def add_pc_tab(self, server_url, api_key, pc_name):
        """Add a new PC monitoring tab"""
        client = PCMonitorClient(server_url, api_key, pc_name)
        
        def remove_callback(tab):
            self.remove_pc_tab(pc_name)
        
        tab = PCTab(self.notebook, client, remove_callback)
        self.pc_tabs[pc_name] = tab
        
        self.notebook.add(tab.frame, text=pc_name)
        self.notebook.select(tab.frame)
        
        # Initial refresh
        tab.refresh_all()
    
    def remove_pc_tab(self, pc_name):
        """Remove a PC tab"""
        if pc_name in self.pc_tabs:
            tab = self.pc_tabs[pc_name]
            self.notebook.forget(tab.frame)
            del self.pc_tabs[pc_name]
            
            # Remove from config
            self.config['servers'] = [s for s in self.config['servers'] 
                                     if s['pc_name'] != pc_name]
            save_multi_config(self.config)
    
    def load_saved_servers(self):
        """Load servers from config"""
        for server in self.config.get('servers', []):
            self.add_pc_tab(
                server['server_url'],
                server['api_key'],
                server['pc_name']
            )
    
    def refresh_all_tabs(self):
        """Refresh all PC tabs"""
        for tab in self.pc_tabs.values():
            tab.refresh_all()
    
    def show_dashboard(self):
        """Show overview dashboard of all PCs"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Dashboard Overview")
        dialog.geometry("800x600")
        
        ttk.Label(dialog, text="All PCs Status", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Create status list
        status_frame = ttk.Frame(dialog)
        status_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for pc_name, tab in self.pc_tabs.items():
            pc_frame = ttk.LabelFrame(status_frame, text=pc_name, padding=10)
            pc_frame.pack(fill="x", pady=5)
            
            # Get status in background
            def update_dashboard(pc_frame, client):
                status = client.get_status()
                
                def display():
                    if 'error' in status:
                        status_text = f"❌ {status['error']}"
                        color = "red"
                    else:
                        mon = "🟢 Active" if status.get('monitoring') else "🔴 Stopped"
                        events = status.get('event_count', 0)
                        status_text = f"{mon} | Events: {events}"
                        color = "green" if status.get('monitoring') else "red"
                    
                    label = ttk.Label(pc_frame, text=status_text, foreground=color)
                    label.pack()
                
                dialog.after(0, display)
            
            threading.Thread(target=update_dashboard, args=(pc_frame, tab.client), 
                           daemon=True).start()
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def show_about(self):
        messagebox.showinfo("About", 
                           "Multi-PC Monitor Dashboard\n\n"
                           "Monitor multiple PCs simultaneously\n"
                           "with individual tabs and unified controls.\n\n"
                           "Features:\n"
                           "• Multiple PC monitoring\n"
                           "• Individual control per PC\n"
                           "• Dashboard overview\n"
                           "• Auto-refresh\n"
                           "• Remote commands")
    
    def start_auto_refresh(self):
        """Background auto-refresh thread"""
        def refresh_loop():
            while self.is_running:
                time.sleep(15)
                if self.auto_refresh_var.get() and self.is_running:
                    self.root.after(0, self.refresh_all_tabs)
        
        threading.Thread(target=refresh_loop, daemon=True).start()
    
    def on_closing(self):
        self.is_running = False
        time.sleep(0.5)
        self.root.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MultiPCMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()