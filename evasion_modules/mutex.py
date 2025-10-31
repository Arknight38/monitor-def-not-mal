import sys

try:
    import win32event
    import win32api
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False

MUTEX_NAME = "Global\\PCMonitor_Mutex_92847563"
_mutex_handle = None

def check_single_instance():
    """Check if another instance is already running"""
    global _mutex_handle
    
    if not WINDOWS_SUPPORT:
        return True  # Skip check on non-Windows
    
    try:
        _mutex_handle = win32event.CreateMutex(None, False, MUTEX_NAME)
        last_error = win32api.GetLastError()
        
        if last_error == 183:  # ERROR_ALREADY_EXISTS
            print("Another instance is already running!")
            return False
        
        return True
    except Exception as e:
        print(f"Mutex check failed: {e}")
        return True  # Allow execution if check fails

def release_mutex():
    """Release the mutex on exit"""
    global _mutex_handle
    
    if _mutex_handle and WINDOWS_SUPPORT:
        try:
            win32api.CloseHandle(_mutex_handle)
        except:
            pass