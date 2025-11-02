"""Server modules - Unified Version"""
__version__ = "4.0.0"

# Import from unified server core module
from .server_core import (
    ConfigManager,
    NetworkUtils,
    ClipboardManager,
    SimpleEncryption,
    SystemUtils,
    clipboard_manager,
    network_utils,
    encryption,
    system_utils,
    config,
    pc_id,
    API_KEY,
    # Legacy compatibility functions
    get_local_ip,
    get_all_local_ips,
    load_config,
    load_callback_config,
    ensure_directories,
    get_clipboard_text,
    set_clipboard_text,
    start_clipboard_monitoring,
    stop_clipboard_monitoring,
    get_clipboard_history,
    clear_clipboard_history
)

__all__ = [
    'ConfigManager',
    'NetworkUtils', 
    'ClipboardManager',
    'SimpleEncryption',
    'SystemUtils',
    'clipboard_manager',
    'network_utils',
    'encryption',
    'system_utils',
    'config',
    'pc_id',
    'API_KEY',
    'get_local_ip',
    'get_all_local_ips',
    'load_config',
    'load_callback_config',
    'ensure_directories',
    'get_clipboard_text',
    'set_clipboard_text',
    'start_clipboard_monitoring',
    'stop_clipboard_monitoring',
    'get_clipboard_history',
    'clear_clipboard_history'
]