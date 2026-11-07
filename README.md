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
├── ram_monitor.py         # RAM Monitoring module (Member 2)
├── disk_monitor.py        # Disk Monitoring module (Member 2)
├── requirements.txt       # Python dependencies (merged)
├── requirementsdashboard.txt # Legacy dashboard dependencies (redundant)
├── README.md              # Project documentation
└── tests/                 # Unit tests
    ├── test_process_manager.py
    ├── test_ram_monitor.py
    └── test_disk_monitor.py
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
- Live RAM & Disk usage percentage cards with warning alerts
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
- **RAM Monitoring**: Real-time RAM usage percentage, total, used, and available space in GB, live 60-second RAM usage history graph, and high RAM usage warning alerts (> 85%).
- **Disk Monitoring**: System root storage statistics (total, used, free space in GB and usage %), low disk space alert (> 90%), and real-time partition table showing device, mountpoint, filesystem, and capacity breakdown.

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

## 🔌 Integration Architecture for RAM & Disk Modules

The RAM and Disk modules developed by Member 2 are fully integrated into the SLRM dashboard:

### 1. Module Functions
```python
from ram_monitor import get_ram_stats, check_ram_alert
from disk_monitor import get_disk_stats, check_disk_alert, get_disk_partitions
```

- **`get_ram_stats()`**: Returns a dictionary with `usage`, `total_gb`, `used_gb`, and `available_gb` (calculated with `1024**3`). Polled every 1 second by `_schedule_ram_update()`.
- **`check_ram_alert(usage)`**: Returns a status or alert string depending on whether RAM usage exceeds the 85.0% threshold.
- **`get_disk_stats()`**: Returns a dictionary with `path`, `usage`, `total_gb`, `used_gb`, and `free_gb`. Polled every 5 seconds by `_schedule_disk_update()`.
- **`check_disk_alert(usage)`**: Returns a status or alert string depending on whether disk usage exceeds the 90.0% threshold.
- **`get_disk_partitions()`**: Returns active, non-pseudo partitions (filtering out tmpfs, squashfs, snap, and loop mounts on Linux) to populate the partitions table in the Disk Monitoring view.

### 2. Standalone Plotting Functions
- `plot_live_ram_history()` in `ram_monitor.py` and `plot_disk_usage()` in `disk_monitor.py` are standalone CLI/testing tools and are intentionally **not** invoked in the GUI thread to ensure non-blocking UI responsiveness. Instead, Tkinter's `FigureCanvasTkAgg` and non-blocking `root.after()` loops render the embedded graphs.

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

