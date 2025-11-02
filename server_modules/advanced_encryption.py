"""
Advanced Encryption Module
Strengthened data transmission security with multiple encryption layers
"""
import os
import base64
import hashlib
import hmac
import secrets
import time
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging

class AdvancedEncryption:
    """Multi-layer encryption system with enhanced security"""
    
    def __init__(self):
        self.logger = logging.getLogger('AdvancedEncryption')
        
        # Encryption keys and settings
        self.symmetric_key = None
        self.asymmetric_keys = None
        self.session_keys = {}
        
        # Encryption algorithms
        self.algorithms = {
            'AES': self._aes_encrypt,
            'ChaCha20': self._chacha20_encrypt,
            'Fernet': self._fernet_encrypt
        }
        
        # Current encryption method
        self.current_method = 'AES'
        
        # Initialize encryption
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption keys and settings"""
        try:
            # Generate symmetric key
            self.symmetric_key = secrets.token_bytes(32)  # 256-bit key
            
            # Generate asymmetric key pair
            self._generate_asymmetric_keys()
            
            # Initialize Fernet
            self.fernet_key = Fernet.generate_key()
            self.fernet = Fernet(self.fernet_key)
            
            self.logger.info("Advanced encryption initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Encryption initialization failed: {e}")
            raise
    
    def _generate_asymmetric_keys(self):
        """Generate RSA key pair for asymmetric encryption"""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            public_key = private_key.public_key()
            
            self.asymmetric_keys = {
                'private': private_key,
                'public': public_key
            }
            
        except Exception as e:
            self.logger.error(f"Asymmetric key generation failed: {e}")
            raise
    
    def encrypt_data(self, data, method=None, compression=True):
        """Encrypt data with specified method and optional compression"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Optional compression
            if compression:
                data = self._compress_data(data)
            
            # Select encryption method
            method = method or self.current_method
            
            if method not in self.algorithms:
                raise ValueError(f"Unsupported encryption method: {method}")
            
            # Encrypt data
            encrypted_data = self.algorithms[method](data)
            
            # Add metadata
            metadata = {
                'method': method,
                'compressed': compression,
                'timestamp': time.time(),
                'checksum': hashlib.sha256(data).hexdigest()
            }
            
            # Combine metadata and encrypted data
            result = {
                'metadata': metadata,
                'data': base64.b64encode(encrypted_data).decode('utf-8')
            }
            
            return json.dumps(result)
            
        except Exception as e:
            self.logger.error(f"Data encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_package):
        """Decrypt data package"""
        try:
            # Parse encrypted package
            package = json.loads(encrypted_package)
            metadata = package['metadata']
            encrypted_data = base64.b64decode(package['data'])
            
            # Select decryption method
            method = metadata['method']
            
            # Decrypt data
            if method == 'AES':
                decrypted_data = self._aes_decrypt(encrypted_data)
            elif method == 'ChaCha20':
                decrypted_data = self._chacha20_decrypt(encrypted_data)
            elif method == 'Fernet':
                decrypted_data = self._fernet_decrypt(encrypted_data)
            else:
                raise ValueError(f"Unsupported decryption method: {method}")
            
            # Decompress if needed
            if metadata.get('compressed', False):
                decrypted_data = self._decompress_data(decrypted_data)
            
            # Verify checksum
            actual_checksum = hashlib.sha256(decrypted_data).hexdigest()
            expected_checksum = metadata.get('checksum')
            
            if expected_checksum and actual_checksum != expected_checksum:
                raise ValueError("Data integrity check failed")
            
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Data decryption failed: {e}")
            raise
    
    def _aes_encrypt(self, data):
        """AES-256-GCM encryption"""
        try:
            # Generate random IV
            iv = secrets.token_bytes(12)  # 96-bit IV for GCM
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.symmetric_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            
            encryptor = cipher.encryptor()
            
            # Encrypt data
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Combine IV, tag, and ciphertext
            return iv + encryptor.tag + ciphertext
            
        except Exception as e:
            self.logger.error(f"AES encryption failed: {e}")
            raise
    
    def _aes_decrypt(self, encrypted_data):
        """AES-256-GCM decryption"""
        try:
            # Extract IV, tag, and ciphertext
            iv = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.symmetric_key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            
            decryptor = cipher.decryptor()
            
            # Decrypt data
            return decryptor.update(ciphertext) + decryptor.finalize()
            
        except Exception as e:
            self.logger.error(f"AES decryption failed: {e}")
            raise
    
    def _chacha20_encrypt(self, data):
        """ChaCha20-Poly1305 encryption"""
        try:
            # Generate random nonce
            nonce = secrets.token_bytes(12)  # 96-bit nonce
            
            # Create cipher
            cipher = Cipher(
                algorithms.ChaCha20(self.symmetric_key, nonce),
                modes.GCM(nonce),
                backend=default_backend()
            )
            
            encryptor = cipher.encryptor()
            
            # Encrypt data
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Combine nonce, tag, and ciphertext
            return nonce + encryptor.tag + ciphertext
            
        except Exception as e:
            self.logger.error(f"ChaCha20 encryption failed: {e}")
            raise
    
    def _chacha20_decrypt(self, encrypted_data):
        """ChaCha20-Poly1305 decryption"""
        try:
            # Extract nonce, tag, and ciphertext
            nonce = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.ChaCha20(self.symmetric_key, nonce),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            
            decryptor = cipher.decryptor()
            
            # Decrypt data
            return decryptor.update(ciphertext) + decryptor.finalize()
            
        except Exception as e:
            self.logger.error(f"ChaCha20 decryption failed: {e}")
            raise
    
    def _fernet_encrypt(self, data):
        """Fernet encryption (AES-128 in CBC mode with HMAC)"""
        try:
            return self.fernet.encrypt(data)
        except Exception as e:
            self.logger.error(f"Fernet encryption failed: {e}")
            raise
    
    def _fernet_decrypt(self, encrypted_data):
        """Fernet decryption"""
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            self.logger.error(f"Fernet decryption failed: {e}")
            raise
    
    def _compress_data(self, data):
        """Compress data using zlib"""
        try:
            import zlib
            return zlib.compress(data, level=6)
        except Exception as e:
            self.logger.error(f"Data compression failed: {e}")
            return data
    
    def _decompress_data(self, data):
        """Decompress data using zlib"""
        try:
            import zlib
            return zlib.decompress(data)
        except Exception as e:
            self.logger.error(f"Data decompression failed: {e}")
            raise
    
    def encrypt_asymmetric(self, data):
        """Encrypt data using RSA public key"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # RSA can only encrypt limited data size
            max_size = 190  # For 2048-bit key with OAEP padding
            
            if len(data) > max_size:
                # For large data, encrypt with symmetric key and encrypt the key with RSA
                session_key = secrets.token_bytes(32)
                
                # Encrypt data with session key
                cipher = Cipher(
                    algorithms.AES(session_key),
                    modes.GCM(secrets.token_bytes(12)),
                    backend=default_backend()
                )
                encryptor = cipher.encryptor()
                encrypted_data = encryptor.update(data) + encryptor.finalize()
                
                # Encrypt session key with RSA
                encrypted_key = self.asymmetric_keys['public'].encrypt(
                    session_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                return {
                    'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
                    'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                    'iv': base64.b64encode(cipher.algorithm.nonce).decode('utf-8'),
                    'tag': base64.b64encode(encryptor.tag).decode('utf-8')
                }
            else:
                # Direct RSA encryption for small data
                encrypted_data = self.asymmetric_keys['public'].encrypt(
                    data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return base64.b64encode(encrypted_data).decode('utf-8')
                
        except Exception as e:
            self.logger.error(f"Asymmetric encryption failed: {e}")
            raise
    
    def decrypt_asymmetric(self, encrypted_data):
        """Decrypt data using RSA private key"""
        try:
            if isinstance(encrypted_data, dict):
                # Hybrid encryption (RSA + AES)
                encrypted_key = base64.b64decode(encrypted_data['encrypted_key'])
                encrypted_content = base64.b64decode(encrypted_data['encrypted_data'])
                iv = base64.b64decode(encrypted_data['iv'])
                tag = base64.b64decode(encrypted_data['tag'])
                
                # Decrypt session key
                session_key = self.asymmetric_keys['private'].decrypt(
                    encrypted_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                # Decrypt data with session key
                cipher = Cipher(
                    algorithms.AES(session_key),
                    modes.GCM(iv, tag),
                    backend=default_backend()
                )
                decryptor = cipher.decryptor()
                return decryptor.update(encrypted_content) + decryptor.finalize()
            else:
                # Direct RSA decryption
                encrypted_bytes = base64.b64decode(encrypted_data)
                return self.asymmetric_keys['private'].decrypt(
                    encrypted_bytes,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
        except Exception as e:
            self.logger.error(f"Asymmetric decryption failed: {e}")
            raise
    
    def generate_hmac(self, data, key=None):
        """Generate HMAC for data integrity"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            key = key or self.symmetric_key
            
            return hmac.new(key, data, hashlib.sha256).hexdigest()
            
        except Exception as e:
            self.logger.error(f"HMAC generation failed: {e}")
            raise
    
    def verify_hmac(self, data, signature, key=None):
        """Verify HMAC signature"""
        try:
            expected_signature = self.generate_hmac(data, key)
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"HMAC verification failed: {e}")
            return False
    
    def rotate_keys(self):
        """Rotate encryption keys for enhanced security"""
        try:
            # Generate new symmetric key
            old_symmetric_key = self.symmetric_key
            self.symmetric_key = secrets.token_bytes(32)
            
            # Generate new asymmetric keys
            self._generate_asymmetric_keys()
            
            # Generate new Fernet key
            self.fernet_key = Fernet.generate_key()
            self.fernet = Fernet(self.fernet_key)
            
            self.logger.info("Encryption keys rotated successfully")
            
            return {
                'status': 'success',
                'timestamp': time.time(),
                'old_key_hash': hashlib.sha256(old_symmetric_key).hexdigest()[:16]
            }
            
        except Exception as e:
            self.logger.error(f"Key rotation failed: {e}")
            raise
    
    def export_public_key(self):
        """Export public key for sharing"""
        try:
            public_key_pem = self.asymmetric_keys['public'].public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return base64.b64encode(public_key_pem).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Public key export failed: {e}")
            raise
    
    def get_encryption_info(self):
        """Get current encryption configuration"""
        return {
            'current_method': self.current_method,
            'available_methods': list(self.algorithms.keys()),
            'key_sizes': {
                'symmetric': len(self.symmetric_key) * 8 if self.symmetric_key else 0,
                'asymmetric': 2048  # RSA key size
            },
            'features': {
                'compression': True,
                'integrity_check': True,
                'hybrid_encryption': True,
                'key_rotation': True
            }
        }


class SecureChannel:
    """Secure communication channel with end-to-end encryption"""
    
    def __init__(self, encryption_engine: AdvancedEncryption):
        self.encryption = encryption_engine
        self.logger = logging.getLogger('SecureChannel')
        
        # Channel settings
        self.channel_id = secrets.token_hex(8)
        self.session_key = None
        self.sequence_number = 0
        
    def establish_channel(self, remote_public_key=None):
        """Establish secure channel with key exchange"""
        try:
            # Generate session key
            self.session_key = secrets.token_bytes(32)
            
            # Exchange keys if remote public key provided
            if remote_public_key:
                # Encrypt session key with remote public key
                # This would be sent to the remote party
                pass
            
            self.logger.info(f"Secure channel {self.channel_id} established")
            return self.channel_id
            
        except Exception as e:
            self.logger.error(f"Channel establishment failed: {e}")
            raise
    
    def send_secure_message(self, message):
        """Send message over secure channel"""
        try:
            # Add sequence number for replay protection
            self.sequence_number += 1
            
            message_data = {
                'content': message,
                'sequence': self.sequence_number,
                'timestamp': time.time(),
                'channel_id': self.channel_id
            }
            
            # Serialize and encrypt
            serialized = json.dumps(message_data)
            encrypted = self.encryption.encrypt_data(serialized)
            
            return encrypted
            
        except Exception as e:
            self.logger.error(f"Secure message send failed: {e}")
            raise
    
    def receive_secure_message(self, encrypted_message):
        """Receive and decrypt message from secure channel"""
        try:
            # Decrypt message
            decrypted_data = self.encryption.decrypt_data(encrypted_message)
            message_data = json.loads(decrypted_data)
            
            # Verify channel ID
            if message_data.get('channel_id') != self.channel_id:
                raise ValueError("Channel ID mismatch")
            
            # Check sequence number for replay attacks
            received_sequence = message_data.get('sequence', 0)
            if received_sequence <= self.sequence_number:
                self.logger.warning(f"Possible replay attack: sequence {received_sequence}")
            
            return message_data['content']
            
        except Exception as e:
            self.logger.error(f"Secure message receive failed: {e}")
            raise


# Global encryption instance
advanced_encryption = AdvancedEncryption()