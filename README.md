# ⚡ Smart Linux Resource Manager (SLRM)

A comprehensive system resource monitoring dashboard built with **Python 3**, **Tkinter**, **Matplotlib**, and **psutil**.

> **Semester 4 Final Project – Operating Systems**

---

## 📁 Project Structure

```
SLRM/
├── main.py               # Application entry point
├── dashboard.py           # GUI & Dashboard module (Member 4)
├── cpu_monitor.py         # CPU Monitoring module (Member 1)
├── process_manager.py     # Process Management module (Member 3)
├── ram_monitor.py         # RAM Monitoring (Member 2 – upcoming)
├── disk_monitor.py        # Disk Monitoring (Member 2 – upcoming)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🚀 How to Run

### Prerequisites

- **Python 3.8+** installed
- **Tkinter** (included with most Python installations)

### On Ubuntu Linux (Target OS)

```bash
# 1. Install Tkinter if not already available
sudo apt update
sudo apt install python3-tk

# 2. Navigate to the project directory
cd /path/to/SLRM

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Run the application
python3 main.py
```

### On Windows (Development / Testing)

```powershell
# 1. Navigate to the project directory
cd C:\path\to\SLRM

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the application
python main.py
```

> **Note:** Tkinter comes bundled with the official Python installer on Windows.

---

## 📊 Features

### Dashboard
- Live CPU usage percentage card
- Running process count card
- RAM & Disk placeholder cards (awaiting integration)
- Real-time CPU usage history graph (last 60 seconds)
- Quick navigation to all sections

### CPU Monitoring
- Real-time CPU usage percentage
- Physical core count
- Logical thread count
- Current and maximum CPU frequency
- Live CPU usage history graph
- High CPU usage alert (> 85% threshold)

### Process Manager
- Full process listing with sortable columns (CPU, Memory, Name, PID)
- Process details: Name, PID, Username, Status, CPU %, RAM %, RAM (MB)
- Heavy-process filter (CPU ≥ 50% or RAM ≥ 10%)
- Safe process termination with confirmation dialog
- Auto-refresh every 3 seconds

### RAM & Disk Monitoring
- Placeholder pages ready for future module integration

---

## 🔧 Integration Architecture

### How cpu_monitor.py Is Integrated

The dashboard imports two functions from `cpu_monitor.py`:

```python
from cpu_monitor import get_cpu_stats, check_cpu_alert
```

- **`get_cpu_stats()`** – Called every ~1 second via `Tkinter.after()` to retrieve live CPU statistics (usage, cores, threads, frequency). Values are displayed on both the Dashboard and CPU Monitoring pages.
- **`check_cpu_alert(cpu_usage)`** – Called after each reading to check if CPU usage exceeds 85%. The alert/status message is displayed on screen.
- **`plot_live_cpu_history()`** – Intentionally **not** called from the GUI because it opens a separate Matplotlib window and runs a blocking 60-second loop. Instead, the dashboard maintains its own `collections.deque` of the last 60 readings and renders an embedded Matplotlib graph inside the Tkinter window using `FigureCanvasTkAgg`.

### How process_manager.py Is Integrated

The dashboard imports the `ProcessManager` class:

```python
from process_manager import ProcessManager
```

An instance is created once:

```python
self.process_manager = ProcessManager()
```

- **`get_processes(sort_by, limit)`** – Called to populate the Treeview table. The `sort_by` parameter is driven by radio buttons in the toolbar.
- **`get_heavy_processes(cpu_threshold, memory_threshold)`** – Called when the "Heavy Processes Only" checkbox is enabled.
- **`terminate_process(pid, expected_create_time)`** – Called when the user selects a process and clicks "Terminate". A confirmation dialog is shown first, and the process `create_time` is verified to prevent accidental termination due to PID reuse.

### CPU Priming

`psutil.cpu_percent(interval=None)` returns `0.0` on its very first call because no prior sample exists. The application handles this by:

1. Calling `psutil.cpu_percent(interval=None)` in `main.py` before the GUI starts.
2. Calling it again in `dashboard.py.__init__()` via `_prime_cpu()`.
3. By the time the first periodic update fires (~1 second later), meaningful readings are available.

---

## 🔌 How to Integrate RAM & Disk Modules Later

When Member 2 completes `ram_monitor.py` and `disk_monitor.py`, follow these steps:

### 1. Add the Module Files

Place `ram_monitor.py` and `disk_monitor.py` in the project root alongside the existing modules.

### 2. Import in dashboard.py

Add imports at the top of `dashboard.py`:

```python
from ram_monitor import get_ram_stats  # (or whatever the function names are)
from disk_monitor import get_disk_stats
```

### 3. Update the RAM Page

In the `_build_ram_page()` method:
- Replace the placeholder content with stat labels (similar to the CPU page)
- Add a Matplotlib graph for RAM usage history
- Create a `_schedule_ram_update()` method similar to `_schedule_cpu_update()`

### 4. Update the Disk Page

In the `_build_disk_page()` method:
- Replace the placeholder content with partition info and usage bars
- Create a `_schedule_disk_update()` method if live updates are needed

### 5. Update Dashboard Cards

In `_schedule_cpu_update()` or a new update method:
- Update `self.dash_ram_card` with live RAM percentage
- Update `self.dash_disk_card` with live disk usage percentage

The GUI is designed to be modular – each page is an independent frame, and new update loops can be added without affecting existing ones.

---

## 🎨 Design

- **Dark charcoal theme** inspired by modern system monitors
- **Catppuccin-style color palette** for readability
- **Responsive layout** that scales with window resizing
- **Embedded Matplotlib graphs** using `FigureCanvasTkAgg`
- **Professional typography** and consistent spacing

---

## 👥 Team

| Member   | Responsibility              |
|----------|-----------------------------|
| Member 1 | CPU Monitoring Module       |
| Member 2 | RAM & Disk Monitoring       |
| Member 3 | Process Management Module   |
| Member 4 | GUI & Dashboard Integration |

---

## 📦 Dependencies

| Package    | Purpose                        |
|------------|--------------------------------|
| psutil     | System and process monitoring  |
| matplotlib | CPU usage graphs               |
| tkinter    | GUI framework (built-in)       |

