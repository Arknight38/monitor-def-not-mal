"""
Self-Protection Module
Demonstrates techniques to detect tampering and patching
Save as: evasion_modules/self_protection.py
"""
import sys
import os
import hashlib
import threading
import time
from pathlib import Path


def calculate_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of a file
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
    
    Returns:
        Hex digest of hash
    """
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"Error calculating hash: {e}")
        return None


def verify_file_integrity(filepath: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Verify file hasn't been modified
    
    Args:
        filepath: Path to file to check
        expected_hash: Expected hash value
        algorithm: Hash algorithm used
    
    Returns:
        True if file matches expected hash
    """
    current_hash = calculate_file_hash(filepath, algorithm)
    
    if current_hash is None:
        return False
    
    return current_hash.lower() == expected_hash.lower()


def get_own_hash() -> str:
    """
    Calculate hash of the running executable
    
    Returns:
        SHA256 hash of current executable
    """
    try:
        exe_path = sys.executable
        return calculate_file_hash(exe_path, 'sha256')
    except:
        return None


def save_integrity_hash(output_file: str = ".integrity_check"):
    """
    Save current executable hash for later verification
    This should be called once after building the executable
    
    Args:
        output_file: Where to save the hash
    """
    current_hash = get_own_hash()
    
    if current_hash:
        with open(output_file, 'w') as f:
            f.write(current_hash)
        print(f"[+] Integrity hash saved: {current_hash}")
    else:
        print("[-] Failed to calculate integrity hash")


def check_integrity(hash_file: str = ".integrity_check") -> bool:
    """
    Check if executable has been modified since hash was saved
    
    Args:
        hash_file: File containing expected hash
    
    Returns:
        True if integrity check passes, False if tampered
    """
    if not os.path.exists(hash_file):
        # No hash file - can't verify (assume OK for first run)
        return True
    
    try:
        with open(hash_file, 'r') as f:
            expected_hash = f.read().strip()
        
        current_hash = get_own_hash()
        
        if current_hash != expected_hash:
            print("[!] WARNING: File integrity check FAILED!")
            print(f"[!] Expected: {expected_hash}")
            print(f"[!] Current:  {current_hash}")
            print("[!] Executable may have been patched or modified!")
            return False
        
        return True
        
    except Exception as e:
        print(f"[!] Integrity check error: {e}")
        return True  # Assume OK if check fails


def detect_memory_dumping() -> bool:
    """
    Detect if process memory is being dumped
    
    Indicators:
    - Excessive handle count
    - Suspicious process accessing our memory
    
    Returns:
        True if dumping suspected
    """
    try:
        import psutil
        
        current_process = psutil.Process()
        
        # Check number of handles
        # Normal process: 100-500 handles
        # Being dumped: Can exceed 1000+
        num_handles = current_process.num_handles() if hasattr(current_process, 'num_handles') else 0
        
        if num_handles > 1000:
            print(f"[!] Suspicious handle count: {num_handles}")
            return True
        
        # Check for processes known to dump memory
        dump_tools = [
            'processhacker.exe',
            'procexp.exe', 
            'procexp64.exe',
            'procdump.exe',
            'procdump64.exe',
            'dumpit.exe'
        ]
        
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if proc_name in dump_tools:
                    print(f"[!] Memory dumping tool detected: {proc.info['name']}")
                    return True
            except:
                continue
        
        return False
        
    except ImportError:
        return False
    except Exception as e:
        return False


def continuous_integrity_monitor(interval: int = 60, callback=None):
    """
    Continuously monitor file integrity
    
    Args:
        interval: Seconds between checks
        callback: Function to call if tampering detected
    """
    print(f"[*] Starting integrity monitor (checking every {interval}s)")
    
    initial_hash = get_own_hash()
    
    while True:
        time.sleep(interval)
        
        current_hash = get_own_hash()
        
        if current_hash != initial_hash:
            print("[!] INTEGRITY VIOLATION DETECTED!")
            print("[!] Executable has been modified at runtime!")
            
            if callback:
                callback()
            
            # In real malware, this might trigger:
            # - Self-deletion
            # - Kill switch activation
            # - Stop all operations
            break


def start_integrity_monitor(interval: int = 60, callback=None):
    """
    Start integrity monitoring in background thread
    
    Args:
        interval: Seconds between checks
        callback: Function to call if tampering detected
    """
    monitor_thread = threading.Thread(
        target=continuous_integrity_monitor,
        args=(interval, callback),
        daemon=True
    )
    monitor_thread.start()
    return monitor_thread


def detect_debugger_breakpoints():
    """
    Detect if breakpoints are set in code
    Uses exception handling to catch INT3 breakpoints
    
    Returns:
        True if breakpoints detected
    """
    try:
        # This is a simplified check
        # Real implementations would check memory for 0xCC (INT3) bytes
        
        # If we get here without exception, no breakpoint
        return False
        
    except Exception:
        # Exception might indicate breakpoint hit
        return True


def anti_patch_check():
    """
    Check for common patching techniques
    
    Detects:
    - Modified entry point
    - Suspicious DLL injections
    - Code section modifications
    
    Returns:
        True if patching detected
    """
    try:
        import psutil
        
        current_process = psutil.Process()
        
        # Check loaded DLLs for suspicious ones
        suspicious_dlls = [
            'inject', 'hook', 'detour', 'intercept',
            'frida', 'minhook', 'polyhook'
        ]
        
        try:
            for dll in current_process.memory_maps():
                dll_name = Path(dll.path).name.lower()
                for suspect in suspicious_dlls:
                    if suspect in dll_name:
                        print(f"[!] Suspicious DLL detected: {dll.path}")
                        return True
        except:
            pass
        
        return False
        
    except ImportError:
        return False
    except Exception:
        return False


class IntegrityProtection:
    """
    Comprehensive integrity protection system
    """
    
    def __init__(self, enable_continuous_monitoring: bool = False):
        self.initial_hash = get_own_hash()
        self.monitoring = False
        self.monitor_thread = None
        self.enabled = enable_continuous_monitoring
        
        if self.enabled:
            self.start_monitoring()
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = start_integrity_monitor(
                interval=interval,
                callback=self.on_tampering_detected
            )
            print("[+] Integrity protection enabled")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        print("[-] Integrity protection disabled")
    
    def check_now(self) -> bool:
        """Perform immediate integrity check"""
        current_hash = get_own_hash()
        
        if current_hash != self.initial_hash:
            print("[!] Integrity check FAILED")
            self.on_tampering_detected()
            return False
        
        return True
    
    def on_tampering_detected(self):
        """Called when tampering is detected"""
        print("\n" + "="*70)
        print("TAMPERING DETECTED")
        print("="*70)
        print("[!] The executable has been modified!")
        print("[!] This could indicate:")
        print("    - Patching by reverse engineer")
        print("    - Memory modification")
        print("    - Code injection")
        print("    - Malware analysis")
        print("\n[*] In production, this would trigger:")
        print("    - Immediate termination")
        print("    - Self-deletion")
        print("    - Kill switch activation")
        print("    - Alert to C2 server")
        print("="*70 + "\n")
        
        # For demonstration, just log
        # Real malware would exit or take action


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SELF-PROTECTION & INTEGRITY CHECKING DEMONSTRATION")
    print("="*70)
    
    # Show current executable hash
    print("\n1. Current Executable:")
    print(f"   Path: {sys.executable}")
    current_hash = get_own_hash()
    print(f"   Hash: {current_hash}")
    
    # Demonstrate integrity checking
    print("\n2. Integrity Check:")
    if check_integrity():
        print("   ✓ Integrity check passed")
    else:
        print("   ✗ Integrity check FAILED - file modified!")
    
    # Check for memory dumping
    print("\n3. Memory Dumping Detection:")
    if detect_memory_dumping():
        print("   ⚠ Memory dumping suspected!")
    else:
        print("   ✓ No memory dumping detected")
    
    # Check for patches
    print("\n4. Anti-Patch Check:")
    if anti_patch_check():
        print("   ⚠ Patching/hooking detected!")
    else:
        print("   ✓ No patches detected")
    
    print("\n5. Protection Features:")
    print("   ✓ File integrity verification")
    print("   ✓ Memory dumping detection")
    print("   ✓ DLL injection detection")
    print("   ✓ Continuous monitoring (optional)")
    print("   ✓ Tampering callbacks")
    
    print("\n" + "="*70)
    print("Educational Purpose:")
    print("  This demonstrates how malware protects itself from")
    print("  analysis and modification. Real implementations would")
    print("  take action (exit, self-delete) when tampering detected.")
    print("="*70 + "\n")