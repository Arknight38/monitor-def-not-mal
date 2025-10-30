import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import io
import base64
from datetime import datetime
import threading
import time
import json
from pathlib import Path

class PCMonitorClient:
    def __init__(self, server_url, api_key):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-API-Key': api_key}
        
    def get_status(self):
        try:
            resp = requests.get(f"{self.server_url}/api/status", timeout=5)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def start_monitoring(self):
        try:
            resp = requests.post(f"{self.server_url}/api/start", headers=self.headers)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def stop_monitoring(self):
        try:
            resp = requests.post(f"{self.server_url}/api/stop", headers=self.headers)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_events(self, limit=50):
        try:
            resp = requests.get(f"{self.server_url}/api/events?limit={limit}", headers=self.headers)
            return resp.json()
        except Exception as e:
            return []
    
    def get_latest_screenshot(self):
        try:
            resp = requests.get(f"{self.server_url}/api/screenshot/latest", headers=self.headers)
            data = resp.json()
            if 'image' in data:
                return base64.b64decode(data['image'])
            return None
        except Exception as e:
            return None
    
    def get_screenshots(self):
        try:
            resp = requests.get(f"{self.server_url}/api/screenshots", headers=self.headers)
            return resp.json()
        except Exception as e:
            return []
    
    def take_snapshot(self):
        try:
            resp = requests.post(f"{self.server_url}/api/snapshot", headers=self.headers)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

class MonitorGUI:
    def __init__(self, root, client):
        self.root = root
        self.client = client
        self.root.title("PC Monitor - Remote Dashboard")
        self.root.geometry("1200x800")
        
        # Menu
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change Server", command=self.change_server)
        settings_menu.add_separator()
        settings_menu.add_command(label="Exit", command=root.quit)
        
        # Status Frame
        status_frame = ttk.LabelFrame(root, text="Server Status", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Checking...", font=("Arial", 12))
        self.status_label.pack(side="left", padx=10)
        
        ttk.Button(status_frame, text="Refresh", command=self.update_status).pack(side="left", padx=5)
        ttk.Button(status_frame, text="Start Monitoring", command=self.start_monitoring).pack(side="left", padx=5)
        ttk.Button(status_frame, text="Stop Monitoring", command=self.stop_monitoring).pack(side="left", padx=5)
        ttk.Button(status_frame, text="Take Snapshot Now", command=self.take_snapshot).pack(side="left", padx=5)
        
        # Auto-refresh checkbox
        self.auto_refresh = tk.BooleanVar(value=True)
        ttk.Checkbutton(status_frame, text="Auto-refresh (10s)", variable=self.auto_refresh).pack(side="right", padx=10)
        
        # Main Content
        paned = ttk.PanedWindow(root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left Panel - Screenshot
        left_frame = ttk.LabelFrame(paned, text="Live View", padding=10)
        paned.add(left_frame, weight=2)
        
        self.screenshot_label = ttk.Label(left_frame, text="No screenshot available", background="gray")
        self.screenshot_label.pack(fill="both", expand=True)
        
        ttk.Button(left_frame, text="Refresh Screenshot", command=self.update_screenshot).pack(pady=5)
        
        # Right Panel - Events
        right_frame = ttk.LabelFrame(paned, text="Activity Log", padding=10)
        paned.add(right_frame, weight=1)
        
        self.events_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=30, font=("Consolas", 9))
        self.events_text.pack(fill="both", expand=True)
        
        ttk.Button(right_frame, text="Refresh Events", command=self.update_events).pack(pady=5)
        
        # Initial update
        self.update_all()
        
        # Start auto-refresh thread after a delay
        self.root.after(2000, self.start_auto_refresh)
    
    def change_server(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Server")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Server URL:").pack(pady=5)
        url_entry = ttk.Entry(dialog, width=40)
        url_entry.insert(0, self.client.server_url)
        url_entry.pack(pady=5)
        
        ttk.Label(dialog, text="API Key:").pack(pady=5)
        key_entry = ttk.Entry(dialog, width=40, show="*")
        key_entry.insert(0, self.client.api_key)
        key_entry.pack(pady=5)
        
        def save_settings():
            self.client.server_url = url_entry.get().rstrip('/')
            self.client.api_key = key_entry.get()
            self.client.headers = {'X-API-Key': self.client.api_key}
            
            # Save to config
            config = {
                "server_url": self.client.server_url,
                "api_key": self.client.api_key
            }
            with open("client_config.json", "w") as f:
                json.dump(config, f, indent=4)
            
            dialog.destroy()
            self.update_all()
        
        ttk.Button(dialog, text="Save", command=save_settings).pack(pady=10)
    
    def start_auto_refresh(self):
        """Start the auto-refresh thread"""
        self.refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.refresh_thread.start()
    
    def update_status(self):
        status = self.client.get_status()
        if 'error' in status:
            self.status_label.config(text=f"❌ Error: {status['error']}", foreground="red")
        else:
            monitoring = "🟢 MONITORING" if status.get('monitoring') else "🔴 STOPPED"
            events = status.get('event_count', 0)
            self.status_label.config(
                text=f"{monitoring} | Events: {events}", 
                foreground="green" if status.get('monitoring') else "red"
            )
    
    def start_monitoring(self):
        result = self.client.start_monitoring()
        if 'error' in result:
            messagebox.showerror("Error", result['error'])
        self.update_status()
    
    def stop_monitoring(self):
        result = self.client.stop_monitoring()
        if 'error' in result:
            messagebox.showerror("Error", result['error'])
        self.update_status()
    
    def take_snapshot(self):
        result = self.client.take_snapshot()
        if 'error' not in result:
            self.status_label.config(text="📸 Snapshot taken!", foreground="blue")
            self.root.after(2000, self.update_status)
            self.root.after(1000, self.update_screenshot)
    
    def update_screenshot(self):
        img_data = self.client.get_latest_screenshot()
        if img_data:
            try:
                image = Image.open(io.BytesIO(img_data))
                # Resize to fit window
                image.thumbnail((800, 600))
                photo = ImageTk.PhotoImage(image)
                self.screenshot_label.config(image=photo, text="")
                self.screenshot_label.image = photo  # Keep reference
            except Exception as e:
                self.screenshot_label.config(text=f"Error loading image: {e}")
        else:
            self.screenshot_label.config(text="No screenshot available")
    
    def update_events(self):
        events = self.client.get_events(100)
        self.events_text.delete(1.0, tk.END)
        
        if not events:
            self.events_text.insert(tk.END, "No events logged yet.\n")
            return
        
        for event in reversed(events[-50:]):  # Show last 50
            timestamp = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')
            event_type = event['type']
            details = event.get('details', {})
            
            self.events_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.events_text.insert(tk.END, f"{event_type}\n", "event_type")
            
            if event_type == "mouse_click":
                self.events_text.insert(tk.END, f"  → Clicked at ({details.get('x')}, {details.get('y')})\n\n")
            elif event_type == "key_press":
                key = details.get('key', '').replace('Key.', '')
                self.events_text.insert(tk.END, f"  → Key: {key}\n\n")
            elif event_type == "window_change":
                self.events_text.insert(tk.END, f"  → Window: {details.get('title')}\n\n")
            elif event_type == "screenshot":
                self.events_text.insert(tk.END, f"  → Screenshot saved\n\n")
            else:
                self.events_text.insert(tk.END, f"  → {details}\n\n")
        
        self.events_text.tag_config("timestamp", foreground="gray")
        self.events_text.tag_config("event_type", foreground="blue", font=("Consolas", 9, "bold"))
        self.events_text.see(tk.END)
    
    def update_all(self):
        self.update_status()
        self.update_screenshot()
        self.update_events()
    
    def auto_refresh_loop(self):
        # Wait for main loop to start
        time.sleep(3)
        while True:
            time.sleep(10)
            try:
                # Check if variable exists and get value safely
                should_refresh = self.auto_refresh.get()
                if should_refresh:
                    self.root.after(0, self.update_all)
            except RuntimeError:
                # Main loop not ready or window closed
                break
            except Exception as e:
                print(f"Auto-refresh error: {e}")
                break

def load_client_config():
    config_file = Path("client_config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Default config
        default = {
            "server_url": "http://192.168.1.100:5000",
            "api_key": "CHANGE_THIS_SECRET_KEY_12345"
        }
        with open(config_file, 'w') as f:
            json.dump(default, f, indent=4)
        return default

if __name__ == '__main__':
    config = load_client_config()
    
    client = PCMonitorClient(config['server_url'], config['api_key'])
    
    root = tk.Tk()
    app = MonitorGUI(root, client)
    
    print("PC Monitor Client Started")
    print(f"Connecting to: {config['server_url']}")
    print(f"Edit client_config.json to change settings")
    
    root.mainloop()