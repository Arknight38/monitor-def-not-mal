"""
Anti-Debugging Detection (Educational Demo)
Demonstrates awareness of debugging environments
"""
import ctypes
import time
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def is_debugger_present():
    """Check if process is being debugged using IsDebuggerPresent"""
    try:
        return ctypes.windll.kernel32.IsDebuggerPresent() != 0
    except:
        return False

def check_remote_debugger():
    """Check for remote debugger using CheckRemoteDebuggerPresent"""
    try:
        is_debugged = ctypes.c_bool()
        ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
            ctypes.windll.kernel32.GetCurrentProcess(),
            ctypes.byref(is_debugged)
        )
        return is_debugged.value
    except:
        return False

def check_debugger_processes():
    """Detect if debugger processes are running"""
    if not PSUTIL_AVAILABLE:
        return False
    
    debugger_processes = [
        'ollydbg.exe', 'x64dbg.exe', 'x32dbg.exe', 'ida.exe', 'ida64.exe',
        'windbg.exe', 'processhacker.exe', 'procexp.exe', 'procmon.exe',
        'cheatengine-x86_64.exe', 'cheatengine.exe'
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

def check_debugging_environment():
    """
    Perform all anti-debugging checks
    Returns dict with results
    """
    results = {
        'is_being_debugged': False,
        'debugger_present': False,
        'remote_debugger': False,
        'debugger_process': False,
        'timing_anomaly': False,
        'debugger_parent': False
    }
    
    if is_debugger_present():
        results['debugger_present'] = True
        results['is_being_debugged'] = True
    
    if check_remote_debugger():
        results['remote_debugger'] = True
        results['is_being_debugged'] = True
    
    if check_debugger_processes():
        results['debugger_process'] = True
        results['is_being_debugged'] = True
    
    if timing_check():
        results['timing_anomaly'] = True
    
    if check_parent_process():
        results['debugger_parent'] = True
        results['is_being_debugged'] = True
    
    return results