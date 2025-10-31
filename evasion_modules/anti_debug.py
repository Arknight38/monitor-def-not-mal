import ctypes
import time
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def is_debugger_present():
    """Check if process is being debugged"""
    try:
        return ctypes.windll.kernel32.IsDebuggerPresent() != 0
    except:
        return False

def check_debugger_processes():
    """Detect if debugger processes are running"""
    if not PSUTIL_AVAILABLE:
        return False
    
    debugger_processes = [
        'ollydbg.exe', 'x64dbg.exe', 'x32dbg.exe', 'ida.exe', 'ida64.exe',
        'windbg.exe', 'processhacker.exe', 'procexp.exe', 'procmon.exe',
        'cheatengine-x86_64.exe'
    ]
    
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() in debugger_processes:
                return True
    except:
        pass
    
    return False

def timing_check():
    """Detect timing anomalies from debugger stepping"""
    start = time.perf_counter()
    # Normal operation
    for _ in range(1000):
        x = 1 + 1
    elapsed = time.perf_counter() - start
    
    # Should take < 0.001s normally
    # Debugger stepping makes it much slower
    return elapsed > 0.01

def check_parent_process():
    """Detect if launched from debugger"""
    if not PSUTIL_AVAILABLE:
        return False
    
    try:
        parent_name = psutil.Process(os.getppid()).name().lower()
        debuggers = ['ida', 'ollydbg', 'x64dbg', 'windbg', 'processhacker']
        return any(d in parent_name for d in debuggers)
    except:
        return False

def perform_anti_debug_checks():
    """Perform all anti-debugging checks"""
    checks_failed = []
    
    if is_debugger_present():
        checks_failed.append("IsDebuggerPresent detected")
    
    if check_debugger_processes():
        checks_failed.append("Debugger process detected")
    
    if timing_check():
        checks_failed.append("Timing anomaly detected")
    
    if check_parent_process():
        checks_failed.append("Debugger parent process detected")
    
    return checks_failed