"""
main.py - Smart Linux Resource Manager (SLRM) Entry Point

Launches the Tkinter-based dashboard application.
Run this file to start the SLRM GUI:

    python main.py

Author: Member 4 (GUI & Dashboard)
"""

import sys
import tkinter as tk

# ---------------------------------------------------------------------------
# Pre-flight: prime psutil CPU measurement before importing the dashboard.
# The very first call to psutil.cpu_percent(interval=None) returns 0.0
# because there is no prior sample. We prime it here so that by the time
# the dashboard polls its first reading (~1 s later) the value is meaningful.
# ---------------------------------------------------------------------------
try:
    import psutil
    psutil.cpu_percent(interval=None)  # prime – result discarded
except ImportError:
    print("[ERROR] psutil is not installed. Install with:  pip install psutil")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Import the dashboard GUI
# ---------------------------------------------------------------------------
from dashboard import SLRMDashboard


def main():
    """Create the Tk root window and launch the SLRM dashboard."""
    root = tk.Tk()

    # ---- Window configuration -------------------------------------------
    root.title("Smart Linux Resource Manager (SLRM)")

    # Set a dark title-bar hint (works on some Linux WMs and Windows 11)
    try:
        root.tk.call("tk", "scaling", 1.25)  # Slight DPI scaling
    except Exception:
        pass

    # Centre the window on screen
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w, win_h = 1280, 760
    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # ---- Launch the dashboard -------------------------------------------
    app = SLRMDashboard(root)

    # ---- Handle graceful close ------------------------------------------
    def on_close():
        """Clean shutdown – stop any pending after() callbacks."""
        try:
            root.destroy()
        except Exception:
            pass

    root.protocol("WM_DELETE_WINDOW", on_close)

    # ---- Start the Tkinter main loop ------------------------------------
    root.mainloop()


if __name__ == "__main__":
    main()

