"""
Auto-Updater Module
Automatic system updates and version management
"""
import os
import sys
import json
import hashlib
import shutil
import subprocess
import requests
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
import logging
import zipfile
import tempfile

class AutoUpdater:
    """Automatic update system with version control"""
    
    def __init__(self, current_version="3.0.0", update_server=None):
        self.current_version = current_version
        self.update_server = update_server or "https://your-update-server.com"
        self.update_channel = "stable"  # stable, beta, dev
        
        # Update settings
        self.auto_check = True
        self.auto_install = False
        self.check_interval = 3600  # 1 hour
        self.backup_count = 3
        
        # Paths
        self.app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
        self.backup_dir = self.app_dir / "backups"
        self.temp_dir = Path(tempfile.gettempdir()) / "monitor_updates"
        
        # State
        self.checking_updates = False
        self.installing_update = False
        self.last_check = None
        self.available_updates = []
        
        # Callbacks
        self.update_callbacks = {
            'update_available': [],
            'update_progress': [],
            'update_complete': [],
            'update_error': []
        }
        
        self.logger = logging.getLogger('AutoUpdater')
        
        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Start automatic checking if enabled
        if self.auto_check:
            self._start_update_checker()
    
    def _start_update_checker(self):
        """Start background update checking thread"""
        def check_loop():
            while self.auto_check:
                try:
                    if self._should_check_updates():
                        self.check_for_updates()
                    
                    time.sleep(300)  # Check every 5 minutes if we should check
                    
                except Exception as e:
                    self.logger.error(f"Update checker error: {e}")
                    time.sleep(3600)  # Wait 1 hour on error
        
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()
        self.logger.info("Auto-update checker started")
    
    def _should_check_updates(self):
        """Check if we should check for updates"""
        if not self.last_check:
            return True
        
        time_since_check = (datetime.now() - self.last_check).total_seconds()
        return time_since_check >= self.check_interval
    
    def check_for_updates(self, force=False):
        """Check for available updates"""
        if self.checking_updates and not force:
            return False
        
        self.checking_updates = True
        self.last_check = datetime.now()
        
        try:
            self.logger.info("Checking for updates...")
            
            # Get version information from server
            version_info = self._get_version_info()
            
            if not version_info:
                self.logger.warning("Could not retrieve version information")
                return False
            
            # Compare versions
            available_version = version_info.get('latest_version')
            if available_version and self._is_newer_version(available_version):
                self.available_updates = [version_info]
                self.logger.info(f"Update available: {available_version}")
                
                # Notify callbacks
                self._notify_callbacks('update_available', version_info)
                
                # Auto-install if enabled
                if self.auto_install:
                    self.install_update(version_info)
                
                return True
            else:
                self.logger.info("No updates available")
                self.available_updates = []
                return False
                
        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            self._notify_callbacks('update_error', str(e))
            return False
        finally:
            self.checking_updates = False
    
    def _get_version_info(self):
        """Get version information from update server"""
        try:
            # Construct update URL
            url = f"{self.update_server}/api/version"
            params = {
                'channel': self.update_channel,
                'current_version': self.current_version,
                'platform': sys.platform,
                'arch': 'x64' if sys.maxsize > 2**32 else 'x86'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get version info: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid version info response: {e}")
            return None
    
    def _is_newer_version(self, version):
        """Check if version is newer than current"""
        try:
            def version_tuple(v):
                return tuple(map(int, v.split('.')))
            
            return version_tuple(version) > version_tuple(self.current_version)
        except Exception:
            return False
    
    def install_update(self, version_info):
        """Install available update"""
        if self.installing_update:
            self.logger.warning("Update installation already in progress")
            return False
        
        self.installing_update = True
        
        try:
            self.logger.info(f"Installing update {version_info['latest_version']}")
            
            # Create backup
            if not self._create_backup():
                raise Exception("Failed to create backup")
            
            # Download update
            update_file = self._download_update(version_info)
            if not update_file:
                raise Exception("Failed to download update")
            
            # Verify download
            if not self._verify_update(update_file, version_info):
                raise Exception("Update verification failed")
            
            # Install update
            if not self._apply_update(update_file, version_info):
                raise Exception("Failed to apply update")
            
            self.logger.info("Update installed successfully")
            self._notify_callbacks('update_complete', version_info)
            
            # Schedule restart if needed
            if version_info.get('requires_restart', False):
                self._schedule_restart()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Update installation failed: {e}")
            self._notify_callbacks('update_error', str(e))
            
            # Restore backup if installation failed
            self._restore_backup()
            return False
        finally:
            self.installing_update = False
    
    def _create_backup(self):
        """Create backup of current installation"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{self.current_version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            self.logger.info(f"Creating backup: {backup_name}")
            
            # Copy current application files
            if getattr(sys, 'frozen', False):
                # Backup executable
                exe_path = Path(sys.executable)
                shutil.copy2(exe_path, backup_path.with_suffix('.exe'))
            else:
                # Backup entire directory for development
                shutil.copytree(self.app_dir, backup_path, ignore=shutil.ignore_patterns(
                    'backups', '__pycache__', '*.pyc', '*.log', 'temp*'
                ))
            
            # Clean old backups
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Remove old backup files"""
        try:
            backups = sorted(self.backup_dir.glob("backup_*"), key=os.path.getmtime)
            
            while len(backups) > self.backup_count:
                old_backup = backups.pop(0)
                if old_backup.is_file():
                    old_backup.unlink()
                elif old_backup.is_dir():
                    shutil.rmtree(old_backup)
                self.logger.info(f"Removed old backup: {old_backup.name}")
                
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
    
    def _download_update(self, version_info):
        """Download update file"""
        try:
            download_url = version_info.get('download_url')
            if not download_url:
                self.logger.error("No download URL provided")
                return None
            
            filename = version_info.get('filename', f"update_{version_info['latest_version']}.zip")
            update_file = self.temp_dir / filename
            
            self.logger.info(f"Downloading update from {download_url}")
            
            # Download with progress tracking
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Notify progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self._notify_callbacks('update_progress', {
                                'stage': 'download',
                                'progress': progress,
                                'downloaded': downloaded,
                                'total': total_size
                            })
            
            self.logger.info(f"Download completed: {update_file}")
            return update_file
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None
    
    def _verify_update(self, update_file, version_info):
        """Verify downloaded update file"""
        try:
            expected_hash = version_info.get('sha256_hash')
            if not expected_hash:
                self.logger.warning("No hash provided for verification")
                return True  # Skip verification if no hash
            
            self.logger.info("Verifying update file...")
            
            # Calculate file hash
            sha256_hash = hashlib.sha256()
            with open(update_file, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_hash = sha256_hash.hexdigest()
            
            if actual_hash.lower() == expected_hash.lower():
                self.logger.info("Update verification successful")
                return True
            else:
                self.logger.error(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")
                return False
                
        except Exception as e:
            self.logger.error(f"Update verification failed: {e}")
            return False
    
    def _apply_update(self, update_file, version_info):
        """Apply the downloaded update"""
        try:
            self.logger.info("Applying update...")
            
            # Extract update if it's a zip file
            if update_file.suffix.lower() == '.zip':
                extract_dir = self.temp_dir / "extracted"
                extract_dir.mkdir(exist_ok=True)
                
                with zipfile.ZipFile(update_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Find the new executable or files
                update_files = list(extract_dir.rglob("*"))
                
            else:
                # Single file update (e.g., new executable)
                update_files = [update_file]
            
            # Apply the update
            for file_path in update_files:
                if file_path.is_file():
                    target_path = self.app_dir / file_path.name
                    
                    # Replace the file
                    if target_path.exists():
                        # On Windows, rename current file first
                        if sys.platform == 'win32':
                            backup_temp = target_path.with_suffix('.old')
                            target_path.rename(backup_temp)
                    
                    shutil.copy2(file_path, target_path)
                    
                    # Make executable if needed
                    if sys.platform != 'win32' and file_path.suffix in ['.exe', '']:
                        os.chmod(target_path, 0o755)
            
            # Update version info
            self._update_version_info(version_info['latest_version'])
            
            self.logger.info("Update applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Update application failed: {e}")
            return False
    
    def _update_version_info(self, new_version):
        """Update version information"""
        try:
            self.current_version = new_version
            
            # Save version info to file
            version_file = self.app_dir / "version.json"
            version_data = {
                'version': new_version,
                'updated_at': datetime.now().isoformat(),
                'channel': self.update_channel
            }
            
            with open(version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update version info: {e}")
    
    def _restore_backup(self):
        """Restore from most recent backup"""
        try:
            self.logger.info("Restoring from backup...")
            
            # Find most recent backup
            backups = sorted(self.backup_dir.glob("backup_*"), key=os.path.getmtime, reverse=True)
            
            if not backups:
                self.logger.error("No backups available for restore")
                return False
            
            latest_backup = backups[0]
            
            if latest_backup.is_file():
                # Single file backup (executable)
                target = Path(sys.executable)
                shutil.copy2(latest_backup, target)
            else:
                # Directory backup
                # Copy files back (excluding certain directories)
                for item in latest_backup.rglob("*"):
                    if item.is_file():
                        relative_path = item.relative_to(latest_backup)
                        target_path = self.app_dir / relative_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_path)
            
            self.logger.info("Backup restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            return False
    
    def _schedule_restart(self):
        """Schedule application restart"""
        def restart_app():
            try:
                self.logger.info("Restarting application for update...")
                
                if getattr(sys, 'frozen', False):
                    # Restart executable
                    subprocess.Popen([sys.executable] + sys.argv[1:])
                else:
                    # Restart Python script
                    subprocess.Popen([sys.executable] + sys.argv)
                
                # Exit current process
                time.sleep(2)
                os._exit(0)
                
            except Exception as e:
                self.logger.error(f"Restart failed: {e}")
        
        # Schedule restart in 3 seconds
        threading.Timer(3.0, restart_app).start()
    
    def add_update_callback(self, event, callback):
        """Add callback for update events"""
        if event in self.update_callbacks:
            self.update_callbacks[event].append(callback)
    
    def _notify_callbacks(self, event, data):
        """Notify registered callbacks"""
        for callback in self.update_callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Callback error for {event}: {e}")
    
    def get_update_status(self):
        """Get current update status"""
        return {
            'current_version': self.current_version,
            'checking_updates': self.checking_updates,
            'installing_update': self.installing_update,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'available_updates': len(self.available_updates),
            'auto_check': self.auto_check,
            'auto_install': self.auto_install,
            'update_channel': self.update_channel
        }
    
    def set_update_settings(self, auto_check=None, auto_install=None, 
                           check_interval=None, update_channel=None):
        """Update auto-updater settings"""
        if auto_check is not None:
            self.auto_check = auto_check
        
        if auto_install is not None:
            self.auto_install = auto_install
        
        if check_interval is not None:
            self.check_interval = check_interval
        
        if update_channel is not None:
            self.update_channel = update_channel
        
        self.logger.info("Update settings changed")


class UpdateServer:
    """Simple update server for testing"""
    
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.versions = {
            'stable': {
                'latest_version': '3.1.0',
                'download_url': f'http://{host}:{port}/downloads/update_3.1.0.zip',
                'filename': 'update_3.1.0.zip',
                'sha256_hash': 'dummy_hash_for_testing',
                'requires_restart': True,
                'release_notes': 'Bug fixes and performance improvements'
            }
        }
    
    def start_server(self):
        """Start simple HTTP server for testing"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse
        
        class UpdateHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/api/version'):
                    # Parse query parameters
                    url_parts = urllib.parse.urlparse(self.path)
                    params = urllib.parse.parse_qs(url_parts.query)
                    
                    channel = params.get('channel', ['stable'])[0]
                    version_info = self.server.update_server.versions.get(channel, {})
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(version_info).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        server = HTTPServer((self.host, self.port), UpdateHandler)
        server.update_server = self
        
        self.logger = logging.getLogger('UpdateServer')
        self.logger.info(f"Update server starting on {self.host}:{self.port}")
        
        server.serve_forever()


def setup_auto_updater(current_version="3.0.0", update_server=None):
    """Setup and return auto-updater instance"""
    return AutoUpdater(current_version, update_server)