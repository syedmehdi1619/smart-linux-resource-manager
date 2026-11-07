"""
dashboard.py - Smart Linux Resource Manager (SLRM) Dashboard GUI

This module provides the complete Tkinter-based GUI for the SLRM project.
It integrates existing cpu_monitor and process_manager modules, and provides
placeholder pages for RAM and Disk monitoring (to be integrated later).

Author: Member 4 (GUI & Dashboard)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

import matplotlib
matplotlib.use("TkAgg")  # Must be set before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ---------------------------------------------------------------------------
# Import existing project modules
# ---------------------------------------------------------------------------
from cpu_monitor import get_cpu_stats, check_cpu_alert
from process_manager import ProcessManager
from ram_monitor import get_ram_stats, check_ram_alert
from disk_monitor import get_disk_stats, check_disk_alert, get_disk_partitions

# ---------------------------------------------------------------------------
# Color Palette – Dark Theme
# ---------------------------------------------------------------------------
COLORS = {
    "bg_dark":       "#1e1e2e",   # Main background
    "bg_sidebar":    "#181825",   # Sidebar background
    "bg_card":       "#313244",   # Card / panel background
    "bg_card_hover": "#45475a",   # Card hover
    "bg_entry":      "#45475a",   # Entry / input field
    "text_primary":  "#cdd6f4",   # Primary text
    "text_secondary":"#a6adc8",   # Secondary / muted text
    "accent_blue":   "#89b4fa",   # Blue accent
    "accent_green":  "#a6e3a1",   # Green accent
    "accent_teal":   "#94e2d5",   # Teal accent
    "accent_peach":  "#fab387",   # Peach / orange accent
    "accent_red":    "#f38ba8",   # Red / warning accent
    "accent_mauve":  "#cba6f7",   # Purple accent
    "sidebar_active":"#313244",   # Active sidebar button
    "border":        "#585b70",   # Border color
    "graph_bg":      "#1e1e2e",   # Graph background
    "graph_line":    "#89b4fa",   # Graph line color
    "graph_fill":    "#89b4fa",   # Graph fill (with alpha)
}

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _round_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
    """Draw a rounded rectangle on a Tkinter Canvas."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SLRMDashboard – Main Application Class                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class SLRMDashboard:
    """Main application window for the Smart Linux Resource Manager."""

    # History length for CPU graph (last 60 readings ≈ 60 s)
    CPU_HISTORY_LEN = 60
    RAM_HISTORY_LEN = 60
    DISK_HISTORY_LEN = 60
    # Refresh interval in milliseconds
    CPU_REFRESH_MS = 1000
    RAM_REFRESH_MS = 1000
    DISK_REFRESH_MS = 5000
    PROCESS_REFRESH_MS = 3000

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart Linux Resource Manager (SLRM)")
        self.root.geometry("1280x760")
        self.root.minsize(1020, 620)
        self.root.configure(bg=COLORS["bg_dark"])

        # Try to remove window decoration for a cleaner look (optional)
        try:
            self.root.iconbitmap("")  # suppress default icon error
        except Exception:
            pass

        # ---- Data stores -------------------------------------------------
        self.cpu_history = deque([0.0] * self.CPU_HISTORY_LEN,
                                maxlen=self.CPU_HISTORY_LEN)
        self.ram_history = deque([0.0] * self.RAM_HISTORY_LEN,
                                maxlen=self.RAM_HISTORY_LEN)
        self.disk_history = deque([0.0] * self.DISK_HISTORY_LEN,
                                 maxlen=self.DISK_HISTORY_LEN)
        self.cpu_primed = False  # Track whether first CPU reading is primed
        self.process_manager = ProcessManager()
        self.current_sort = "cpu"
        self.process_data_cache = []  # list of process dicts
        self.show_heavy_only = False

        # ---- Build GUI ---------------------------------------------------
        self._build_sidebar()
        self._build_main_area()

        # ---- Prime CPU reading (first call returns 0.0) ------------------
        self._prime_cpu()

        # ---- Start periodic updates -------------------------------------
        self._schedule_cpu_update()
        self._schedule_ram_update()
        self._schedule_disk_update()
        self._schedule_process_update()

    # ------------------------------------------------------------------
    # Prime CPU measurement
    # ------------------------------------------------------------------
    def _prime_cpu(self):
        """Call cpu_percent once so subsequent calls return real data."""
        try:
            import psutil
            psutil.cpu_percent(interval=None)
            self.cpu_primed = True
        except Exception:
            self.cpu_primed = False

    # ══════════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ══════════════════════════════════════════════════════════════════
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=COLORS["bg_sidebar"], width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # App title
        title_frame = tk.Frame(self.sidebar, bg=COLORS["bg_sidebar"])
        title_frame.pack(fill=tk.X, pady=(24, 30), padx=16)
        tk.Label(title_frame, text="⚡ SLRM", font=("Segoe UI", 20, "bold"),
                 fg=COLORS["accent_blue"], bg=COLORS["bg_sidebar"]).pack(anchor="w")
        tk.Label(title_frame, text="Resource Manager",
                 font=("Segoe UI", 10), fg=COLORS["text_secondary"],
                 bg=COLORS["bg_sidebar"]).pack(anchor="w")

        # Navigation buttons
        self.nav_buttons = {}  # str -> tk.Button
        nav_items = [
            ("Dashboard",      "📊"),
            ("CPU Monitoring",  "🖥"),
            ("RAM Monitoring",  "💾"),
            ("Disk Monitoring", "💿"),
            ("Process Manager", "⚙"),
            ("About",           "ℹ"),
        ]

        for label, icon in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}  {label}",
                font=("Segoe UI", 11),
                fg=COLORS["text_primary"],
                bg=COLORS["bg_sidebar"],
                activeforeground=COLORS["text_primary"],
                activebackground=COLORS["sidebar_active"],
                bd=0, relief=tk.FLAT, anchor="w",
                padx=20, pady=10,
                cursor="hand2",
                command=lambda l=label: self._navigate(l),
            )
            btn.pack(fill=tk.X)
            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["sidebar_active"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(
                bg=COLORS["sidebar_active"] if b == self._active_btn else COLORS["bg_sidebar"]))
            self.nav_buttons[label] = btn

        # Version label at bottom
        tk.Label(self.sidebar, text="v1.0.0  •  Semester 4 Project",
                 font=("Segoe UI", 8), fg=COLORS["text_secondary"],
                 bg=COLORS["bg_sidebar"]).pack(side=tk.BOTTOM, pady=12)

    # ══════════════════════════════════════════════════════════════════
    #  MAIN CONTENT AREA
    # ══════════════════════════════════════════════════════════════════
    def _build_main_area(self):
        self.main_area = tk.Frame(self.root, bg=COLORS["bg_dark"])
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Container dict – each page is built once and packed/unpacked
        self.pages = {}  # str -> tk.Frame
        self._active_btn = None  # tk.Button or None

        self._build_dashboard_page()
        self._build_cpu_page()
        self._build_ram_page()
        self._build_disk_page()
        self._build_process_page()
        self._build_about_page()

        # Show Dashboard by default
        self._navigate("Dashboard")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _navigate(self, page_name: str):
        # Hide all pages
        for p in self.pages.values():
            p.pack_forget()
        # Show selected
        if page_name in self.pages:
            self.pages[page_name].pack(fill=tk.BOTH, expand=True)
        # Update sidebar highlight
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.config(bg=COLORS["sidebar_active"])
                self._active_btn = btn
            else:
                btn.config(bg=COLORS["bg_sidebar"])

    # ==================================================================
    #  PAGE: Dashboard
    # ==================================================================
    def _build_dashboard_page(self):
        page = tk.Frame(self.main_area, bg=COLORS["bg_dark"])
        self.pages["Dashboard"] = page

        # Header
        header = tk.Frame(page, bg=COLORS["bg_dark"])
        header.pack(fill=tk.X, padx=28, pady=(22, 6))
        tk.Label(header, text="Dashboard", font=("Segoe UI", 22, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(side=tk.LEFT)
        tk.Label(header, text="System overview at a glance",
                 font=("Segoe UI", 11), fg=COLORS["text_secondary"],
                 bg=COLORS["bg_dark"]).pack(side=tk.LEFT, padx=16, pady=6)

        # ---- Cards row ---------------------------------------------------
        cards_frame = tk.Frame(page, bg=COLORS["bg_dark"])
        cards_frame.pack(fill=tk.X, padx=24, pady=10)
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1, uniform="card")

        # CPU card
        self.dash_cpu_card = self._make_card(
            cards_frame, "CPU Usage", "—", "🖥", COLORS["accent_blue"],
            row=0, col=0, command=lambda: self._navigate("CPU Monitoring"))

        # RAM card (placeholder)
        self.dash_ram_card = self._make_card(
            cards_frame, "RAM Usage", "Pending", "💾", COLORS["accent_green"],
            row=0, col=1, command=lambda: self._navigate("RAM Monitoring"))

        # Disk card (placeholder)
        self.dash_disk_card = self._make_card(
            cards_frame, "Disk Usage", "Pending", "💿", COLORS["accent_peach"],
            row=0, col=2, command=lambda: self._navigate("Disk Monitoring"))

        # Process count card
        self.dash_proc_card = self._make_card(
            cards_frame, "Processes", "—", "⚙", COLORS["accent_mauve"],
            row=0, col=3, command=lambda: self._navigate("Process Manager"))

        # ---- CPU graph on dashboard --------------------------------------
        graph_frame = tk.Frame(page, bg=COLORS["bg_card"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=(10, 24))

        tk.Label(graph_frame, text="  📈  CPU Usage History (last 60 s)",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_card"],
                 anchor="w").pack(fill=tk.X, padx=16, pady=(12, 0))

        self.dash_fig = Figure(figsize=(8, 2.6), dpi=100,
                               facecolor=COLORS["graph_bg"])
        self.dash_ax = self.dash_fig.add_subplot(111)
        self._style_axis(self.dash_ax)
        self.dash_canvas = FigureCanvasTkAgg(self.dash_fig, master=graph_frame)
        self.dash_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True,
                                              padx=12, pady=(4, 12))

        # CPU alert label
        self.dash_alert_label = tk.Label(
            graph_frame, text="", font=("Segoe UI", 10, "bold"),
            fg=COLORS["accent_green"], bg=COLORS["bg_card"])
        self.dash_alert_label.pack(anchor="w", padx=20, pady=(0, 8))

    # ------------------------------------------------------------------
    # Card builder helper
    # ------------------------------------------------------------------
    def _make_card(self, parent, title, value, icon, accent,
                   row=0, col=0, command=None):
        """Create a dashboard info card. Returns the value label for updates."""
        card = tk.Frame(parent, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1, cursor="hand2")
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        if command:
            card.bind("<Button-1>", lambda e: command())
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e: command())

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)

        top = tk.Frame(inner, bg=COLORS["bg_card"])
        top.pack(fill=tk.X)
        tk.Label(top, text=icon, font=("Segoe UI", 22),
                 fg=accent, bg=COLORS["bg_card"]).pack(side=tk.LEFT)
        tk.Label(top, text=title, font=("Segoe UI", 11),
                 fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack(
            side=tk.LEFT, padx=8)

        val_label = tk.Label(inner, text=value, font=("Segoe UI", 26, "bold"),
                             fg=accent, bg=COLORS["bg_card"])
        val_label.pack(anchor="w", pady=(8, 0))

        # Make all children clickable
        if command:
            for w in (card, inner, top, val_label):
                w.bind("<Button-1>", lambda e: command())
            for w in top.winfo_children():
                w.bind("<Button-1>", lambda e: command())

        return val_label

    # ==================================================================
    #  PAGE: CPU Monitoring
    # ==================================================================
    def _build_cpu_page(self):
        page = tk.Frame(self.main_area, bg=COLORS["bg_dark"])
        self.pages["CPU Monitoring"] = page

        # Header
        hdr = tk.Frame(page, bg=COLORS["bg_dark"])
        hdr.pack(fill=tk.X, padx=28, pady=(22, 6))
        tk.Label(hdr, text="🖥  CPU Monitoring", font=("Segoe UI", 22, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(side=tk.LEFT)

        # Alert label
        self.cpu_alert_label = tk.Label(
            hdr, text="", font=("Segoe UI", 11, "bold"),
            fg=COLORS["accent_green"], bg=COLORS["bg_dark"])
        self.cpu_alert_label.pack(side=tk.RIGHT, padx=12)

        # Stats cards row
        stats_frame = tk.Frame(page, bg=COLORS["bg_dark"])
        stats_frame.pack(fill=tk.X, padx=24, pady=6)
        for i in range(5):
            stats_frame.columnconfigure(i, weight=1, uniform="cpustat")

        self.cpu_labels = {}
        stat_defs = [
            ("Usage", "—",   COLORS["accent_blue"]),
            ("Cores", "—",   COLORS["accent_green"]),
            ("Threads", "—", COLORS["accent_teal"]),
            ("Freq", "—",    COLORS["accent_peach"]),
            ("Max Freq", "—",COLORS["accent_mauve"]),
        ]
        for i, (name, default, color) in enumerate(stat_defs):
            frame = tk.Frame(stats_frame, bg=COLORS["bg_card"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
            frame.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
            tk.Label(frame, text=name, font=("Segoe UI", 10),
                     fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack(
                pady=(12, 2))
            lbl = tk.Label(frame, text=default, font=("Segoe UI", 20, "bold"),
                           fg=color, bg=COLORS["bg_card"])
            lbl.pack(pady=(0, 12))
            self.cpu_labels[name] = lbl

        # CPU History Graph
        graph_frame = tk.Frame(page, bg=COLORS["bg_card"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=(10, 24))

        tk.Label(graph_frame, text="  📈  Live CPU Usage History",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_card"],
                 anchor="w").pack(fill=tk.X, padx=16, pady=(12, 0))

        self.cpu_fig = Figure(figsize=(8, 3), dpi=100,
                              facecolor=COLORS["graph_bg"])
        self.cpu_ax = self.cpu_fig.add_subplot(111)
        self._style_axis(self.cpu_ax)
        self.cpu_canvas = FigureCanvasTkAgg(self.cpu_fig, master=graph_frame)
        self.cpu_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True,
                                             padx=12, pady=(4, 12))

    # ==================================================================
    #  PAGE: RAM Monitoring
    # ==================================================================
    def _build_ram_page(self):
        page = tk.Frame(self.main_area, bg=COLORS["bg_dark"])
        self.pages["RAM Monitoring"] = page

        # Header
        hdr = tk.Frame(page, bg=COLORS["bg_dark"])
        hdr.pack(fill=tk.X, padx=28, pady=(22, 6))
        tk.Label(hdr, text="💾  RAM Monitoring", font=("Segoe UI", 22, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(side=tk.LEFT)

        # Alert label
        self.ram_alert_label = tk.Label(
            hdr, text="", font=("Segoe UI", 11, "bold"),
            fg=COLORS["accent_green"], bg=COLORS["bg_dark"])
        self.ram_alert_label.pack(side=tk.RIGHT, padx=12)

        # Stats cards row
        stats_frame = tk.Frame(page, bg=COLORS["bg_dark"])
        stats_frame.pack(fill=tk.X, padx=24, pady=6)
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1, uniform="ramstat")

        self.ram_labels = {}
        stat_defs = [
            ("Usage",     "—", COLORS["accent_green"]),
            ("Total",     "—", COLORS["accent_blue"]),
            ("Used",      "—", COLORS["accent_peach"]),
            ("Available", "—", COLORS["accent_teal"]),
        ]
        for i, (name, default, color) in enumerate(stat_defs):
            frame = tk.Frame(stats_frame, bg=COLORS["bg_card"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
            frame.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
            tk.Label(frame, text=name, font=("Segoe UI", 10),
                     fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack(
                pady=(12, 2))
            lbl = tk.Label(frame, text=default, font=("Segoe UI", 20, "bold"),
                           fg=color, bg=COLORS["bg_card"])
            lbl.pack(pady=(0, 12))
            self.ram_labels[name] = lbl

        # RAM History Graph
        graph_frame = tk.Frame(page, bg=COLORS["bg_card"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=(10, 24))

        tk.Label(graph_frame, text="  📈  Live RAM Usage History",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_card"],
                 anchor="w").pack(fill=tk.X, padx=16, pady=(12, 0))

        self.ram_fig = Figure(figsize=(8, 3), dpi=100,
                              facecolor=COLORS["graph_bg"])
        self.ram_ax = self.ram_fig.add_subplot(111)
        self._style_axis(self.ram_ax, ylabel="RAM %")
        self.ram_canvas = FigureCanvasTkAgg(self.ram_fig, master=graph_frame)
        self.ram_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True,
                                             padx=12, pady=(4, 12))

    # ==================================================================
    #  PAGE: Disk Monitoring (placeholder)
    # ==================================================================
    def _build_disk_page(self):
        page = tk.Frame(self.main_area, bg=COLORS["bg_dark"])
        self.pages["Disk Monitoring"] = page

        hdr = tk.Frame(page, bg=COLORS["bg_dark"])
        hdr.pack(fill=tk.X, padx=28, pady=(22, 6))
        tk.Label(hdr, text="💿  Disk Monitoring", font=("Segoe UI", 22, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(side=tk.LEFT)

        placeholder = tk.Frame(page, bg=COLORS["bg_card"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1)
        placeholder.pack(expand=True, padx=80, pady=60)

        tk.Label(placeholder, text="🔧", font=("Segoe UI", 48),
                 fg=COLORS["accent_peach"], bg=COLORS["bg_card"]).pack(pady=(40, 10))
        tk.Label(placeholder, text="Disk Monitoring Module",
                 font=("Segoe UI", 18, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_card"]).pack()
        tk.Label(placeholder,
                 text="Disk monitoring module will be integrated soon.\n\n"
                      "Once Member 2 completes disk_monitor.py, its functions\n"
                      "will be imported here to display disk partitions,\n"
                      "usage statistics, and I/O counters.",
                 font=("Segoe UI", 11), fg=COLORS["text_secondary"],
                 bg=COLORS["bg_card"], justify="center").pack(padx=40, pady=(10, 40))

    # ==================================================================
    #  PAGE: Process Manager
    # ==================================================================
    def _build_process_page(self):
        page = tk.Frame(self.main_area, bg=COLORS["bg_dark"])
        self.pages["Process Manager"] = page

        # Header
        hdr = tk.Frame(page, bg=COLORS["bg_dark"])
        hdr.pack(fill=tk.X, padx=28, pady=(22, 6))
        tk.Label(hdr, text="⚙  Process Manager",
                 font=("Segoe UI", 22, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(side=tk.LEFT)

        # Toolbar
        toolbar = tk.Frame(page, bg=COLORS["bg_dark"])
        toolbar.pack(fill=tk.X, padx=28, pady=(4, 8))

        # Sort option
        tk.Label(toolbar, text="Sort by:", font=("Segoe UI", 10),
                 fg=COLORS["text_secondary"], bg=COLORS["bg_dark"]).pack(side=tk.LEFT)
        self.sort_var = tk.StringVar(value="cpu")
        sort_options = [("CPU", "cpu"), ("Memory", "memory"),
                        ("Name", "name"), ("PID", "pid")]
        for text, val in sort_options:
            rb = tk.Radiobutton(
                toolbar, text=text, variable=self.sort_var, value=val,
                font=("Segoe UI", 10), fg=COLORS["text_primary"],
                bg=COLORS["bg_dark"], selectcolor=COLORS["bg_card"],
                activeforeground=COLORS["text_primary"],
                activebackground=COLORS["bg_dark"],
                command=self._on_sort_change)
            rb.pack(side=tk.LEFT, padx=4)

        # Spacer
        tk.Frame(toolbar, bg=COLORS["bg_dark"], width=20).pack(side=tk.LEFT)

        # Heavy-process toggle
        self.heavy_var = tk.BooleanVar(value=False)
        self.heavy_check = tk.Checkbutton(
            toolbar, text="Heavy Processes Only", variable=self.heavy_var,
            font=("Segoe UI", 10), fg=COLORS["accent_red"],
            bg=COLORS["bg_dark"], selectcolor=COLORS["bg_card"],
            activeforeground=COLORS["accent_red"],
            activebackground=COLORS["bg_dark"],
            command=self._on_heavy_toggle)
        self.heavy_check.pack(side=tk.LEFT, padx=8)

        # Refresh button
        ref_btn = tk.Button(
            toolbar, text="🔄 Refresh", font=("Segoe UI", 10),
            fg=COLORS["text_primary"], bg=COLORS["accent_blue"],
            activeforeground=COLORS["text_primary"],
            activebackground=COLORS["accent_teal"],
            bd=0, padx=14, pady=4, cursor="hand2",
            command=self._refresh_processes)
        ref_btn.pack(side=tk.LEFT, padx=8)

        # Terminate button
        term_btn = tk.Button(
            toolbar, text="❌ Terminate", font=("Segoe UI", 10),
            fg=COLORS["text_primary"], bg=COLORS["accent_red"],
            activeforeground=COLORS["text_primary"],
            activebackground="#e06080",
            bd=0, padx=14, pady=4, cursor="hand2",
            command=self._terminate_selected)
        term_btn.pack(side=tk.LEFT, padx=4)

        # Process count label
        self.proc_count_label = tk.Label(
            toolbar, text="", font=("Segoe UI", 10),
            fg=COLORS["text_secondary"], bg=COLORS["bg_dark"])
        self.proc_count_label.pack(side=tk.RIGHT, padx=8)

        # ---- Treeview ----------------------------------------------------
        tree_frame = tk.Frame(page, bg=COLORS["bg_dark"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 20))

        columns = ("name", "pid", "username", "status",
                   "cpu_percent", "memory_percent", "memory_rss_mb")
        col_headings = {
            "name":           "Process Name",
            "pid":            "PID",
            "username":       "Username",
            "status":         "Status",
            "cpu_percent":    "CPU %",
            "memory_percent": "RAM %",
            "memory_rss_mb":  "RAM (MB)",
        }
        col_widths = {
            "name": 200, "pid": 70, "username": 120, "status": 90,
            "cpu_percent": 80, "memory_percent": 80, "memory_rss_mb": 100,
        }

        # Style the Treeview for dark theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["bg_card"],
                         font=("Segoe UI", 10),
                         rowheight=26)
        style.configure("Dark.Treeview.Heading",
                         background=COLORS["bg_sidebar"],
                         foreground=COLORS["accent_blue"],
                         font=("Segoe UI", 10, "bold"))
        style.map("Dark.Treeview",
                   background=[("selected", COLORS["accent_blue"])],
                   foreground=[("selected", COLORS["bg_dark"])])

        self.proc_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            style="Dark.Treeview", selectmode="browse")

        for col in columns:
            self.proc_tree.heading(col, text=col_headings[col])
            anchor = "w" if col in ("name", "username", "status") else "center"
            self.proc_tree.column(col, width=col_widths[col],
                                  anchor=anchor, minwidth=60)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                  command=self.proc_tree.yview)
        self.proc_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.proc_tree.pack(fill=tk.BOTH, expand=True)

        # Tag for highlighting heavy processes
        self.proc_tree.tag_configure("heavy",
                                     background="#4a2030",
                                     foreground=COLORS["accent_red"])

    # ==================================================================
    #  PAGE: About
    # ==================================================================
    def _build_about_page(self):
        page = tk.Frame(self.main_area, bg=COLORS["bg_dark"])
        self.pages["About"] = page

        hdr = tk.Frame(page, bg=COLORS["bg_dark"])
        hdr.pack(fill=tk.X, padx=28, pady=(22, 6))
        tk.Label(hdr, text="ℹ  About", font=("Segoe UI", 22, "bold"),
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(side=tk.LEFT)

        card = tk.Frame(page, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(padx=60, pady=30, fill=tk.BOTH, expand=True)

        tk.Label(card, text="⚡ Smart Linux Resource Manager",
                 font=("Segoe UI", 20, "bold"),
                 fg=COLORS["accent_blue"], bg=COLORS["bg_card"]).pack(pady=(30, 4))
        tk.Label(card, text="SLRM  •  Version 1.0.0",
                 font=("Segoe UI", 12),
                 fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack()

        info_text = (
            "\n"
            "A comprehensive system resource monitoring dashboard\n"
            "built with Python, Tkinter, and Matplotlib.\n\n"
            "Semester 4 Final Project  –  Operating Systems\n\n"
            "──────────────────────────────────────\n\n"
            "Team Contributions:\n\n"
            "   Member 1  –  CPU Monitoring Module\n"
            "   Member 2  –  RAM & Disk Monitoring (Upcoming)\n"
            "   Member 3  –  Process Management Module\n"
            "   Member 4  –  GUI & Dashboard Integration\n\n"
            "──────────────────────────────────────\n\n"
            "Technologies:  Python 3 · Tkinter · Matplotlib · psutil\n"
            "Target OS:     Ubuntu Linux\n"
        )
        tk.Label(card, text=info_text, font=("Segoe UI", 11),
                 fg=COLORS["text_secondary"], bg=COLORS["bg_card"],
                 justify="center").pack(padx=40, pady=(0, 30))

    # ══════════════════════════════════════════════════════════════════
    #  GRAPH STYLING HELPER
    # ══════════════════════════════════════════════════════════════════
    def _style_axis(self, ax):
        """Apply dark-themed styling to a Matplotlib axis."""
        ax.set_facecolor(COLORS["graph_bg"])
        ax.set_xlim(0, self.CPU_HISTORY_LEN)
        ax.set_ylim(0, 100)
        ax.set_ylabel("CPU %", color=COLORS["text_secondary"], fontsize=9)
        ax.set_xlabel("Time (seconds ago)", color=COLORS["text_secondary"],
                      fontsize=9)
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(COLORS["border"])
        ax.grid(True, color=COLORS["border"], alpha=0.3, linestyle="--")

    def _update_graph(self, ax, canvas, fig):
        """Redraw a CPU history graph on the given axis."""
        ax.clear()
        self._style_axis(ax)
        data = list(self.cpu_history)
        x = list(range(len(data)))
        ax.fill_between(x, data, color=COLORS["graph_fill"], alpha=0.15)
        ax.plot(x, data, color=COLORS["graph_line"], linewidth=1.5)
        fig.tight_layout(pad=1.5)
        canvas.draw_idle()

    # ══════════════════════════════════════════════════════════════════
    #  PERIODIC CPU UPDATE
    # ══════════════════════════════════════════════════════════════════
    def _schedule_cpu_update(self):
        """Fetch CPU stats and update all relevant widgets every second."""
        try:
            stats = get_cpu_stats()
            usage = stats["usage"]
            self.cpu_history.append(usage)

            # ---- Update dashboard cards ----------------------------------
            self.dash_cpu_card.config(text=f"{usage:.1f}%")

            # ---- Update CPU page labels ----------------------------------
            self.cpu_labels["Usage"].config(text=f"{usage:.1f}%")
            self.cpu_labels["Cores"].config(text=str(stats["physical_cores"]))
            self.cpu_labels["Threads"].config(text=str(stats["total_threads"]))
            self.cpu_labels["Freq"].config(
                text=f"{stats['current_freq']:.0f} MHz")
            self.cpu_labels["Max Freq"].config(
                text=f"{stats['max_freq']:.0f} MHz")

            # ---- Alert check using existing function ---------------------
            alert_msg = check_cpu_alert(usage)
            if "ALERT" in alert_msg:
                color = COLORS["accent_red"]
            else:
                color = COLORS["accent_green"]
            self.cpu_alert_label.config(text=alert_msg, fg=color)
            self.dash_alert_label.config(text=alert_msg, fg=color)

            # ---- Redraw graphs -------------------------------------------
            self._update_graph(self.dash_ax, self.dash_canvas, self.dash_fig)
            self._update_graph(self.cpu_ax, self.cpu_canvas, self.cpu_fig)

        except Exception as e:
            # Silently handle errors to keep the GUI alive
            print(f"[CPU Update Error] {e}")

        # Schedule next update
        self.root.after(self.CPU_REFRESH_MS, self._schedule_cpu_update)

    # ══════════════════════════════════════════════════════════════════
    #  PERIODIC PROCESS UPDATE
    # ══════════════════════════════════════════════════════════════════
    def _schedule_process_update(self):
        """Refresh process list periodically."""
        self._refresh_processes()
        self.root.after(self.PROCESS_REFRESH_MS, self._schedule_process_update)

    def _on_sort_change(self):
        self.current_sort = self.sort_var.get()
        self._refresh_processes()

    def _on_heavy_toggle(self):
        self.show_heavy_only = self.heavy_var.get()
        self._refresh_processes()

    def _refresh_processes(self):
        """Fetch process data and repopulate the Treeview."""
        try:
            if self.show_heavy_only:
                processes = self.process_manager.get_heavy_processes(
                    cpu_threshold=50.0, memory_threshold=10.0)
                # get_heavy_processes already sorts by CPU;
                # re-sort if user chose a different sort
                if self.current_sort != "cpu":
                    sort_key_map = {
                        "memory": ("memory_percent", True),
                        "name":   ("name",           False),
                        "pid":    ("pid",            False),
                    }
                    key, rev = sort_key_map.get(self.current_sort,
                                                ("cpu_percent", True))
                    if key == "name":
                        processes.sort(key=lambda p: p[key].lower(),
                                       reverse=rev)
                    else:
                        processes.sort(key=lambda p: p[key], reverse=rev)
            else:
                processes = self.process_manager.get_processes(
                    sort_by=self.current_sort)

            self.process_data_cache = processes

            # ---- Populate Treeview ---------------------------------------
            self.proc_tree.delete(*self.proc_tree.get_children())
            for proc in processes:
                values = (
                    proc["name"],
                    proc["pid"],
                    proc.get("username") or "N/A",
                    proc["status"],
                    f'{proc["cpu_percent"]:.1f}',
                    f'{proc["memory_percent"]:.1f}',
                    f'{proc["memory_rss_mb"]:.1f}',
                )
                tag = ()
                if (proc["cpu_percent"] >= 50.0 or
                        proc["memory_percent"] >= 10.0):
                    tag = ("heavy",)
                self.proc_tree.insert("", tk.END, values=values, tags=tag)

            # Update count labels
            count = len(processes)
            label_text = f"{count} process{'es' if count != 1 else ''}"
            if self.show_heavy_only:
                label_text += " (heavy only)"
            self.proc_count_label.config(text=label_text)
            self.dash_proc_card.config(
                text=str(len(self.process_data_cache))
                if self.show_heavy_only
                else str(count))

        except Exception as e:
            print(f"[Process Refresh Error] {e}")

    # ══════════════════════════════════════════════════════════════════
    #  PROCESS TERMINATION
    # ══════════════════════════════════════════════════════════════════
    def _terminate_selected(self):
        """Terminate the process selected in the Treeview, with confirmation."""
        selected = self.proc_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection",
                                   "Please select a process to terminate.")
            return

        item = self.proc_tree.item(selected[0])
        values = item["values"]
        proc_name = values[0]
        proc_pid = int(values[1])

        # Look up create_time from cache
        create_time = None
        for p in self.process_data_cache:
            if p["pid"] == proc_pid:
                create_time = p.get("create_time")
                break

        if create_time is None:
            messagebox.showerror("Error",
                                 "Could not retrieve process creation time.\n"
                                 "The process may have already exited.\n"
                                 "Please refresh and try again.")
            return

        # Confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Termination",
            f"Are you sure you want to terminate this process?\n\n"
            f"  Name:  {proc_name}\n"
            f"  PID:    {proc_pid}\n\n"
            f"This action cannot be undone.",
            icon="warning")

        if not confirm:
            return

        # Call existing terminate_process method
        try:
            result = self.process_manager.terminate_process(
                pid=proc_pid,
                expected_create_time=create_time)
            if result["success"]:
                messagebox.showinfo("Success", result["message"])
            else:
                messagebox.showwarning("Termination Failed", result["message"])
        except ValueError as ve:
            messagebox.showerror("Invalid Operation", str(ve))
        except Exception as e:
            messagebox.showerror("Error",
                                 f"An unexpected error occurred:\n{e}")

        # Refresh process list
        self._refresh_processes()
