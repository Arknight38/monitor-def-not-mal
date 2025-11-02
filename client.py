import tkinter as tk
from tkinter import messagebox
import sys
import traceback

# Enhanced GUI import with fallback
try:
    from client_modules.enhanced_gui import create_enhanced_gui
    ENHANCED_GUI_AVAILABLE = True
    print("✓ Enhanced GUI available")
except ImportError as e:
    ENHANCED_GUI_AVAILABLE = False
    print(f"[!] Enhanced GUI not available: {e}")
    # Fallback to standard GUI
    from client_modules.gui_auto import PCMonitorAutoClient

def main():
    """Main entry point for enhanced auto-callback client"""
    try:
        if ENHANCED_GUI_AVAILABLE:
            print("🚀 Starting Enhanced Monitor Client v3.0...")
            print("✨ Modern GUI with real-time monitoring")
            print("🔒 Advanced security features")
            print("⚡ Optimized performance")
            
            # Create and run enhanced GUI
            app = create_enhanced_gui()
            app.run()
        else:
            print("Starting Standard Monitor Client...")
            print("⚠️ Enhanced features not available")
            
            # Create and run standard application
            app = PCMonitorAutoClient()
            app.mainloop()
            
    except KeyboardInterrupt:
        print("\n\nClient stopped by user")
        sys.exit(0)
    except Exception as e:
        error_msg = f"Fatal error starting client:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        # Try to show GUI error if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Fatal Error", f"Failed to start client:\n\n{str(e)}")
            root.destroy()
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()