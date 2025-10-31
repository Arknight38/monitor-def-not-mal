import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from PIL import ImageGrab

from .config import SCREENSHOTS_DIR

screenshot_history = []
last_screenshot_time = None
auto_screenshot_enabled = False
auto_screenshot_interval = 300

def take_screenshot():
    """Capture and save screenshot"""
    try:
        screenshot = ImageGrab.grab()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        
        screenshot.save(filepath, "PNG")
        
        screenshot_history.append({
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "path": str(filepath)
        })
        
        if len(screenshot_history) > 100:
            old = screenshot_history.pop(0)
            try:
                os.remove(old['path'])
            except:
                pass
        
        return filepath
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

def get_screenshot_history():
    """Get list of all screenshots"""
    return screenshot_history.copy()

def get_latest_screenshot():
    """Get the most recent screenshot"""
    if screenshot_history:
        return screenshot_history[-1]
    return None

def auto_screenshot_worker(config, get_monitoring_status, get_last_activity):
    """Background thread for automatic screenshots"""
    global last_screenshot_time, auto_screenshot_enabled, auto_screenshot_interval
    
    while True:
        time.sleep(10)
        
        if not get_monitoring_status() or not auto_screenshot_enabled or config is None:
            continue
        
        now = datetime.now()
        
        if last_screenshot_time is None or \
           (now - last_screenshot_time).total_seconds() >= auto_screenshot_interval:
            
            if config.get('motion_detection', False):
                if (now - get_last_activity()).total_seconds() > 60:
                    continue
            
            take_screenshot()
            last_screenshot_time = now

def set_auto_screenshot(enabled, interval=None):
    """Configure automatic screenshots"""
    global auto_screenshot_enabled, auto_screenshot_interval
    auto_screenshot_enabled = enabled
    if interval:
        auto_screenshot_interval = interval