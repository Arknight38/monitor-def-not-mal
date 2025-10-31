"""
Clipboard Monitor Module - Fixed Version
Handles clipboard operations properly on Windows
"""
import threading
import time
from datetime import datetime

try:
    import win32clipboard
    import win32con
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("Warning: win32clipboard not available. Install pywin32.")

# Clipboard monitoring state
clipboard_history = []
clipboard_lock = threading.Lock()
last_clipboard_content = None
monitoring_clipboard = False
clipboard_monitor_thread = None


def get_clipboard_text():
    """Safely get clipboard text content"""
    if not CLIPBOARD_AVAILABLE:
        return None
    
    try:
        win32clipboard.OpenClipboard()
        try:
            # Try different formats
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                if isinstance(data, bytes):
                    data = data.decode('utf-8', errors='ignore')
            else:
                data = None
            return data
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        print(f"Error reading clipboard: {e}")
        return None


def set_clipboard_text(text):
    """Safely set clipboard text content"""
    if not CLIPBOARD_AVAILABLE:
        return False
    
    try:
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            return True
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        print(f"Error setting clipboard: {e}")
        return False


def log_clipboard_change(content, operation="changed"):
    """Log clipboard change to history"""
    global last_clipboard_content
    
    if content != last_clipboard_content:
        last_clipboard_content = content
        
        with clipboard_lock:
            clipboard_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "content": content[:500] if content else "",  # Limit size
                "length": len(content) if content else 0
            })
            
            # Keep last 50 entries
            if len(clipboard_history) > 50:
                clipboard_history.pop(0)


def clipboard_monitor_loop():
    """Background thread that monitors clipboard changes"""
    global monitoring_clipboard, last_clipboard_content
    
    print("[*] Clipboard monitoring started")
    
    while monitoring_clipboard:
        try:
            current_content = get_clipboard_text()
            
            if current_content and current_content != last_clipboard_content:
                log_clipboard_change(current_content, "detected")
                
        except Exception as e:
            print(f"Clipboard monitor error: {e}")
        
        time.sleep(1)  # Check every second
    
    print("[*] Clipboard monitoring stopped")


def start_clipboard_monitoring():
    """Start monitoring clipboard changes"""
    global monitoring_clipboard, clipboard_monitor_thread
    
    if not CLIPBOARD_AVAILABLE:
        print("[-] Clipboard monitoring unavailable (pywin32 not installed)")
        return False
    
    if monitoring_clipboard:
        return True
    
    monitoring_clipboard = True
    clipboard_monitor_thread = threading.Thread(
        target=clipboard_monitor_loop, 
        daemon=True
    )
    clipboard_monitor_thread.start()
    
    return True


def stop_clipboard_monitoring():
    """Stop monitoring clipboard changes"""
    global monitoring_clipboard
    monitoring_clipboard = False


def get_clipboard_history():
    """Get clipboard change history"""
    with clipboard_lock:
        return clipboard_history.copy()


def clear_clipboard_history():
    """Clear clipboard history"""
    with clipboard_lock:
        clipboard_history.clear()