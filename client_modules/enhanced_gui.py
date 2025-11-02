"""
Enhanced GUI Module
Better interface design, responsiveness, and real-time updates
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
from datetime import datetime
import queue
import logging
from pathlib import Path

# Import callback listener
from .callback_listener import CallbackListener

class ModernTheme:
    """Modern dark theme for the GUI"""
    
    COLORS = {
        'bg_primary': '#1e1e1e',
        'bg_secondary': '#2d2d2d', 
        'bg_tertiary': '#3c3c3c',
        'fg_primary': '#ffffff',
        'fg_secondary': '#cccccc',
        'accent': '#0078d4',
        'accent_hover': '#106ebe',
        'success': '#107c10',
        'warning': '#ff8c00',
        'error': '#d13438',
        'border': '#484848'
    }
    
    @classmethod
    def apply_theme(cls, root):
        """Apply modern theme to tkinter root"""
        root.configure(bg=cls.COLORS['bg_primary'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure widget styles
        style.configure('Modern.TFrame', background=cls.COLORS['bg_secondary'])
        style.configure('Modern.TLabel', background=cls.COLORS['bg_secondary'], 
                       foreground=cls.COLORS['fg_primary'])
        style.configure('Modern.TButton', background=cls.COLORS['accent'],
                       foreground=cls.COLORS['fg_primary'])
        style.map('Modern.TButton', background=[('active', cls.COLORS['accent_hover'])])
        
        style.configure('Modern.TNotebook', background=cls.COLORS['bg_primary'])
        style.configure('Modern.TNotebook.Tab', background=cls.COLORS['bg_tertiary'],
                       foreground=cls.COLORS['fg_secondary'])
        style.map('Modern.TNotebook.Tab', 
                 background=[('selected', cls.COLORS['accent'])],
                 foreground=[('selected', cls.COLORS['fg_primary'])])

class EnhancedStatusBar:
    """Enhanced status bar with real-time updates"""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, style='Modern.TFrame')
        self.frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        # Status components
        self.status_var = tk.StringVar(value="Ready")
        self.connection_var = tk.StringVar(value="Disconnected")
        self.servers_var = tk.StringVar(value="0 servers")
        self.time_var = tk.StringVar()
        
        # Create status widgets
        self._create_status_widgets()
        
        # Start time update
        self._update_time()
    
    def _create_status_widgets(self):
        """Create status bar widgets"""
        # Main status
        ttk.Label(self.frame, textvariable=self.status_var, 
                 style='Modern.TLabel').pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self.frame, orient=tk.VERTICAL).pack(side=tk.LEFT, 
                                                          fill=tk.Y, padx=5)
        
        # Connection status
        self.connection_label = ttk.Label(self.frame, textvariable=self.connection_var,
                                         style='Modern.TLabel')
        self.connection_label.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self.frame, orient=tk.VERTICAL).pack(side=tk.LEFT, 
                                                          fill=tk.Y, padx=5)
        
        # Server count
        ttk.Label(self.frame, textvariable=self.servers_var,
                 style='Modern.TLabel').pack(side=tk.LEFT, padx=5)
        
        # Time (right aligned)
        ttk.Label(self.frame, textvariable=self.time_var,
                 style='Modern.TLabel').pack(side=tk.RIGHT, padx=5)
    
    def _update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(current_time)
        
        # Schedule next update
        self.frame.after(1000, self._update_time)
    
    def update_status(self, message):
        """Update main status message"""
        self.status_var.set(message)
    
    def update_connection(self, status, color=None):
        """Update connection status"""
        self.connection_var.set(status)
        if color:
            self.connection_label.configure(foreground=color)
    
    def update_server_count(self, count):
        """Update server count"""
        self.servers_var.set(f"{count} server{'s' if count != 1 else ''}")

class RealTimeDataWidget:
    """Widget for displaying real-time data with charts"""
    
    def __init__(self, parent, title="Data"):
        self.frame = ttk.LabelFrame(parent, text=title, style='Modern.TFrame')
        self.data_queue = queue.Queue()
        self.data_history = []
        self.max_history = 100
        
        self._create_widgets()
        self._start_update_thread()
    
    def _create_widgets(self):
        """Create data display widgets"""
        # Create canvas for simple chart
        self.canvas = tk.Canvas(self.frame, width=300, height=150,
                               bg=ModernTheme.COLORS['bg_tertiary'],
                               highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        
        # Data labels
        self.current_value = tk.StringVar(value="0")
        self.avg_value = tk.StringVar(value="0")
        self.max_value = tk.StringVar(value="0")
        
        info_frame = ttk.Frame(self.frame, style='Modern.TFrame')
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(info_frame, text="Current:", style='Modern.TLabel').grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.current_value, style='Modern.TLabel').grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Average:", style='Modern.TLabel').grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.avg_value, style='Modern.TLabel').grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Maximum:", style='Modern.TLabel').grid(row=2, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.max_value, style='Modern.TLabel').grid(row=2, column=1, sticky=tk.W)
    
    def _start_update_thread(self):
        """Start background thread for updates"""
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        """Background update loop"""
        while True:
            try:
                # Get new data from queue
                while not self.data_queue.empty():
                    data = self.data_queue.get_nowait()
                    self.data_history.append(data)
                    
                    # Limit history size
                    if len(self.data_history) > self.max_history:
                        self.data_history = self.data_history[-self.max_history:]
                
                # Update display
                if self.data_history:
                    self._update_display()
                
                time.sleep(0.1)  # Update every 100ms
                
            except Exception as e:
                logging.error(f"Real-time widget update error: {e}")
                time.sleep(1)
    
    def _update_display(self):
        """Update the display with current data"""
        if not self.data_history:
            return
        
        try:
            # Calculate statistics
            current = self.data_history[-1]
            average = sum(self.data_history) / len(self.data_history)
            maximum = max(self.data_history)
            
            # Update labels
            self.current_value.set(f"{current:.1f}")
            self.avg_value.set(f"{average:.1f}")
            self.max_value.set(f"{maximum:.1f}")
            
            # Update chart
            self._draw_chart()
            
        except Exception as e:
            logging.error(f"Display update error: {e}")
    
    def _draw_chart(self):
        """Draw simple line chart"""
        try:
            self.canvas.delete("all")
            
            if len(self.data_history) < 2:
                return
            
            # Calculate dimensions
            width = self.canvas.winfo_width() or 300
            height = self.canvas.winfo_height() or 150
            margin = 20
            
            # Calculate data bounds
            min_val = min(self.data_history)
            max_val = max(self.data_history)
            
            if max_val == min_val:
                max_val += 1  # Avoid division by zero
            
            # Draw grid lines
            for i in range(5):
                y = margin + (height - 2 * margin) * i / 4
                self.canvas.create_line(margin, y, width - margin, y,
                                      fill=ModernTheme.COLORS['border'], width=1)
            
            # Draw data line
            points = []
            for i, value in enumerate(self.data_history):
                x = margin + (width - 2 * margin) * i / (len(self.data_history) - 1)
                y = height - margin - (height - 2 * margin) * (value - min_val) / (max_val - min_val)
                points.extend([x, y])
            
            if len(points) >= 4:
                self.canvas.create_line(points, fill=ModernTheme.COLORS['accent'],
                                      width=2, smooth=True)
                
        except Exception as e:
            logging.error(f"Chart drawing error: {e}")
    
    def add_data(self, value):
        """Add new data point"""
        self.data_queue.put(value)

class EnhancedServerTab:
    """Enhanced server tab with improved layout and features"""
    
    def __init__(self, parent, server_name, server_url, api_key):
        self.server_name = server_name
        self.server_url = server_url
        self.api_key = api_key
        
        # Create main frame
        self.frame = ttk.Frame(parent, style='Modern.TFrame')
        
        # Data widgets
        self.cpu_widget = None
        self.memory_widget = None
        self.network_widget = None
        
        # Create interface
        self._create_interface()
        
        # Start data updates
        self._start_data_updates()
    
    def _create_interface(self):
        """Create the server tab interface"""
        # Create paned window for resizable layout
        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Controls and info
        left_panel = ttk.Frame(paned, style='Modern.TFrame')
        paned.add(left_panel, weight=1)
        
        # Right panel - Real-time data
        right_panel = ttk.Frame(paned, style='Modern.TFrame')
        paned.add(right_panel, weight=2)
        
        self._create_control_panel(left_panel)
        self._create_data_panel(right_panel)
    
    def _create_control_panel(self, parent):
        """Create control panel"""
        # Server info
        info_frame = ttk.LabelFrame(parent, text="Server Information", 
                                   style='Modern.TFrame')
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text=f"Name: {self.server_name}",
                 style='Modern.TLabel').pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"URL: {self.server_url}",
                 style='Modern.TLabel').pack(anchor=tk.W, padx=10, pady=2)
        
        # Connection status
        self.connection_status = tk.StringVar(value="Connecting...")
        ttk.Label(info_frame, textvariable=self.connection_status,
                 style='Modern.TLabel').pack(anchor=tk.W, padx=10, pady=2)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(parent, text="Quick Actions",
                                      style='Modern.TFrame')
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Take Screenshot",
                  command=self._take_screenshot,
                  style='Modern.TButton').pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Button(actions_frame, text="Get System Info",
                  command=self._get_system_info,
                  style='Modern.TButton').pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Button(actions_frame, text="File Manager",
                  command=self._open_file_manager,
                  style='Modern.TButton').pack(fill=tk.X, padx=10, pady=2)
        
        # Logs
        logs_frame = ttk.LabelFrame(parent, text="Activity Log",
                                   style='Modern.TFrame')
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(logs_frame, height=10, width=30,
                               bg=ModernTheme.COLORS['bg_tertiary'],
                               fg=ModernTheme.COLORS['fg_primary'],
                               insertbackground=ModernTheme.COLORS['fg_primary'])
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar to log
        scrollbar = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
    
    def _create_data_panel(self, parent):
        """Create real-time data panel"""
        # Create notebook for different data views
        notebook = ttk.Notebook(parent, style='Modern.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # System monitoring tab
        system_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(system_frame, text="System Monitor")
        
        # Create data widgets
        self.cpu_widget = RealTimeDataWidget(system_frame, "CPU Usage (%)")
        self.cpu_widget.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.memory_widget = RealTimeDataWidget(system_frame, "Memory Usage (%)")
        self.memory_widget.frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Network monitoring tab
        network_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(network_frame, text="Network Monitor")
        
        self.network_widget = RealTimeDataWidget(network_frame, "Network Activity")
        self.network_widget.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Screenshots tab
        screenshot_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(screenshot_frame, text="Screenshots")
        
        self._create_screenshot_panel(screenshot_frame)
    
    def _create_screenshot_panel(self, parent):
        """Create screenshot viewing panel"""
        # Screenshot display
        self.screenshot_label = ttk.Label(parent, text="No screenshot available",
                                         style='Modern.TLabel')
        self.screenshot_label.pack(expand=True)
        
        # Screenshot controls
        controls_frame = ttk.Frame(parent, style='Modern.TFrame')
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Refresh",
                  command=self._refresh_screenshot,
                  style='Modern.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Save",
                  command=self._save_screenshot,
                  style='Modern.TButton').pack(side=tk.LEFT, padx=5)
    
    def _start_data_updates(self):
        """Start background data updates"""
        def update_loop():
            while True:
                try:
                    # Simulate getting data from server
                    import random
                    
                    if self.cpu_widget:
                        cpu_usage = random.uniform(10, 80)
                        self.cpu_widget.add_data(cpu_usage)
                    
                    if self.memory_widget:
                        memory_usage = random.uniform(30, 90)
                        self.memory_widget.add_data(memory_usage)
                    
                    if self.network_widget:
                        network_activity = random.uniform(0, 100)
                        self.network_widget.add_data(network_activity)
                    
                    time.sleep(2)  # Update every 2 seconds
                    
                except Exception as e:
                    logging.error(f"Data update error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=update_loop, daemon=True).start()
    
    def _take_screenshot(self):
        """Take screenshot from server"""
        self.log_message("Taking screenshot...")
        # Implementation would connect to server API
        
    def _get_system_info(self):
        """Get system information from server"""
        self.log_message("Retrieving system information...")
        # Implementation would connect to server API
        
    def _open_file_manager(self):
        """Open file manager for remote server"""
        self.log_message("Opening file manager...")
        # Implementation would open file manager dialog
        
    def _refresh_screenshot(self):
        """Refresh screenshot display"""
        self.log_message("Refreshing screenshot...")
        
    def _save_screenshot(self):
        """Save current screenshot"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.log_message(f"Screenshot saved to {filename}")
    
    def log_message(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Limit log size
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            # Keep only last 100 lines
            self.log_text.delete("1.0", f"{len(lines) - 100}.0")
    
    def update_from_callback(self, data):
        """Update tab with data from callback"""
        try:
            # Store PC ID for future reference
            self.last_pc_id = data.get('pc_id')
            
            # Log the callback reception
            timestamp = data.get('timestamp', 'Unknown')
            self.log_message(f"Callback received: {timestamp}")
            
            # Update connection status
            self.connection_status.set("Connected (Active)")
            
            # Update monitoring data if available
            monitoring_data = data.get('monitoring', {})
            if monitoring_data:
                # Update CPU usage if available
                cpu_usage = monitoring_data.get('cpu_usage')
                if cpu_usage is not None and self.cpu_widget:
                    self.cpu_widget.add_data(float(cpu_usage))
                
                # Update memory usage if available  
                memory_usage = monitoring_data.get('memory_usage')
                if memory_usage is not None and self.memory_widget:
                    self.memory_widget.add_data(float(memory_usage))
                
                # Update network activity if available
                network_activity = monitoring_data.get('network_activity', 0)
                if self.network_widget:
                    self.network_widget.add_data(float(network_activity))
            
            # Log events if present
            events = data.get('events', [])
            for event in events[-5:]:  # Show last 5 events
                event_msg = event.get('message', 'Unknown event')
                self.log_message(f"Event: {event_msg}")
            
            # Log keystrokes count if present
            keystroke_count = data.get('keystroke_count', 0)
            if keystroke_count > 0:
                self.log_message(f"Keystrokes logged: {keystroke_count}")
            
            # Log screenshot count if present
            screenshot_count = data.get('screenshot_count', 0)
            if screenshot_count > 0:
                self.log_message(f"Screenshots taken: {screenshot_count}")
                
        except Exception as e:
            self.log_message(f"Error updating from callback: {e}")
            print(f"Callback update error: {e}")
            import traceback
            traceback.print_exc()

class EnhancedMainWindow:
    """Enhanced main window with modern GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Advanced Monitor Client v3.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Apply modern theme
        ModernTheme.apply_theme(self.root)
        
        # Server tabs
        self.server_tabs = {}
        
        # Create interface
        self._create_interface()
        
        # Initialize and start callback listener
        self.callback_listener = CallbackListener(self)
        self._start_callback_listener()
        
        # Setup callbacks and updates
        self._setup_callbacks()
    
    def _start_callback_listener(self):
        """Start the callback listener"""
        try:
            if self.callback_listener.start():
                local_ip = self.callback_listener.get_local_ip()
                port = self.callback_listener.config['port']
                self.status_bar.update_status(f"🟢 Listening on {local_ip}:{port}")
                self.status_bar.update_connection("Ready for connections", ModernTheme.COLORS['success'])
                print(f"✅ Callback listener started on {local_ip}:{port}")
                
                # Show setup info if this is first run
                self._show_setup_info()
            else:
                self.status_bar.update_status("❌ Failed to start callback listener")
                self.status_bar.update_connection("Listener failed", ModernTheme.COLORS['error'])
                messagebox.showerror(
                    "Error",
                    "Failed to start callback listener!\n\n"
                    "The client cannot accept connections from servers."
                )
        except Exception as e:
            print(f"Error starting callback listener: {e}")
            self.status_bar.update_status(f"❌ Callback listener error: {e}")
    
    def _show_setup_info(self):
        """Show setup information for first-time users"""
        # Check if this is first run
        if not hasattr(self, '_setup_shown'):
            local_ip = self.callback_listener.get_local_ip()
            port = self.callback_listener.config['port']
            key = self.callback_listener.config['callback_key']
            
            setup_msg = (
                f"🎯 ADVANCED MONITOR CLIENT READY\n\n"
                f"Listening for server connections on:\n"
                f"• IP: {local_ip}\n"
                f"• Port: {port}\n\n"
                f"To connect servers, configure their callback_config.json:\n\n"
                f'{{\n'
                f'  "enabled": true,\n'
                f'  "callback_url": "http://{local_ip}:{port}",\n'
                f'  "callback_key": "{key}"\n'
                f'}}\n\n'
                f"Servers will automatically appear as new tabs!"
            )
            
            messagebox.showinfo("Client Ready", setup_msg)
            self._setup_shown = True
    
    def update_status_bar(self, message):
        """Update status bar (for compatibility with callback listener)"""
        self.status_bar.update_status(message)
    
    def _create_interface(self):
        """Create main interface"""
        # Menu bar
        self._create_menu_bar()
        
        # Main content area
        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Dashboard tab
        self._create_dashboard_tab()
        
        # Status bar
        self.status_bar = EnhancedStatusBar(self.root)
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root, bg=ModernTheme.COLORS['bg_secondary'],
                         fg=ModernTheme.COLORS['fg_primary'])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Server", command=self._add_server_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh All", command=self._refresh_all)
        view_menu.add_command(label="Full Screen", command=self._toggle_fullscreen)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Settings", command=self._open_settings)
        tools_menu.add_command(label="Connection Info", command=self._show_connection_info)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_dashboard_tab(self):
        """Create dashboard overview tab"""
        dashboard_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Welcome message
        welcome_label = ttk.Label(dashboard_frame, 
                                 text="Advanced Monitor Client v3.0",
                                 style='Modern.TLabel',
                                 font=('Arial', 16, 'bold'))
        welcome_label.pack(pady=20)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(dashboard_frame, text="System Overview",
                                    style='Modern.TFrame')
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Add dashboard widgets here
        ttk.Label(stats_frame, text="Connected Servers: 0",
                 style='Modern.TLabel').pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(stats_frame, text="Active Connections: 0",
                 style='Modern.TLabel').pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(stats_frame, text="Data Transferred: 0 MB",
                 style='Modern.TLabel').pack(anchor=tk.W, padx=10, pady=5)
    
    def _setup_callbacks(self):
        """Setup callbacks and periodic updates"""
        # Update status bar periodically
        def update_status():
            server_count = len(self.server_tabs)
            self.status_bar.update_server_count(server_count)
            
            if server_count > 0:
                self.status_bar.update_connection("Connected", ModernTheme.COLORS['success'])
            else:
                self.status_bar.update_connection("No servers", ModernTheme.COLORS['warning'])
            
            # Schedule next update
            self.root.after(5000, update_status)
        
        # Start status updates
        self.root.after(1000, update_status)
    
    def add_server_tab(self, server_name, server_url, api_key):
        """Add new server tab"""
        if server_name not in self.server_tabs:
            server_tab = EnhancedServerTab(self.notebook, server_name, server_url, api_key)
            self.notebook.add(server_tab.frame, text=server_name)
            self.server_tabs[server_name] = server_tab
            
            self.status_bar.update_status(f"Connected to {server_name}")
            server_tab.log_message("Connected to server")
    
    def process_callback_data(self, data):
        """Process incoming callback data and update GUI"""
        try:
            pc_id = data.get('pc_id')
            pc_name = data.get('pc_name', 'Unknown')
            
            print(f"[*] Processing callback data for PC: {pc_id} ({pc_name})")
            
            # Find the matching tab by server name or PC ID
            matching_tab = None
            for name, tab in self.server_tabs.items():
                if hasattr(tab, 'last_pc_id') and tab.last_pc_id == pc_id:
                    matching_tab = tab
                    break
                elif name == pc_name:
                    matching_tab = tab
                    # Store PC ID for future reference
                    tab.last_pc_id = pc_id
                    break
            
            if matching_tab:
                print(f"[*] Found matching tab, updating data")
                # Update the tab with callback data
                if hasattr(matching_tab, 'update_from_callback'):
                    matching_tab.update_from_callback(data)
                else:
                    # Fallback: just log the activity
                    matching_tab.log_message(f"Received callback data")
                
                # Update status
                self.status_bar.update_status(f"Updated data from {pc_name}")
            else:
                print(f"[!] No matching tab found for PC: {pc_id} ({pc_name})")
                
        except Exception as e:
            print(f"Error processing callback data: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_server_dialog(self):
        """Show add server dialog"""
        # This would show a dialog to add new server
        pass
    
    def _refresh_all(self):
        """Refresh all server tabs"""
        self.status_bar.update_status("Refreshing all servers...")
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        pass
    
    def _open_settings(self):
        """Open settings dialog"""
        pass
    
    def _show_connection_info(self):
        """Show connection information"""
        pass
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", "Advanced Monitor Client v3.0\nEnhanced GUI with real-time monitoring")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def create_enhanced_gui():
    """Create and return enhanced GUI instance"""
    return EnhancedMainWindow()