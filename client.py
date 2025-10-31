"""
PC Monitor Client - Main Entry Point
Refactored modular architecture
"""

import tkinter as tk
from tkinter import messagebox
import sys
import traceback

# Import modular components
from client_modules.gui import PCMonitorClient

def main():
    """Main entry point for client application"""
    try:
        # Create and run the application
        app = PCMonitorClient()
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