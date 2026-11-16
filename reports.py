"""
reports.py - System Integration & Performance Report Generator
Smart Linux Resource Manager (SLRM)

Integrates Python with the `system_info.sh` Bash script via `subprocess`
and aggregates data from CPU, RAM, Disk, Process Manager, and Alerts modules
to generate Text (.txt) and JSON (.json) performance reports.

Author: Member 5 (Linux Integration, Alerts & Reports)
"""

from datetime import datetime
import getpass
import json
import os
import platform
import shutil
import socket
import subprocess

from alerts import check_all_alerts
from cpu_monitor import get_cpu_stats
from disk_monitor import get_disk_partitions, get_disk_stats
from process_manager import ProcessManager
from ram_monitor import get_ram_stats

DEFAULT_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "system_info.sh"
)


def _fallback_system_info():
    """Fallback system information using Python stdlib when Bash is unavailable."""
    try:
        user = getpass.getuser()
    except Exception:
        user = "Unknown"

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "os_name": f"{platform.system()} {platform.release()}",
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "uptime": "N/A",
        "cpu_model": platform.processor() or "Generic Processor",
        "cpu_cores": str(os.cpu_count() or 1),
        "load_average": "N/A",
        "total_ram": f"{get_ram_stats()['total_gb']} GB",
        "root_disk": f"{get_disk_stats()['used_gb']}G / {get_disk_stats()['total_gb']}G",
        "logged_in_user": user,
        "active_users": "1",
        "ip_address": "127.0.0.1",
    }


def get_system_info(script_path=None, timeout_sec=5):
    """Execute `system_info.sh` via subprocess and return parsed system details.

    Falls back gracefully to Python's `platform` module if `bash` or the script
    cannot be executed.
    """
    target_script = script_path or DEFAULT_SCRIPT_PATH
    info = _fallback_system_info()

    bash_bin = shutil.which("bash")
    if not bash_bin or not os.path.isfile(target_script):
        return info

    try:
        completed = subprocess.run(
            [bash_bin, target_script, "--kv"],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        if completed.returncode != 0 or not completed.stdout:
            return info

        key_map = {
            "TIMESTAMP": "timestamp",
            "HOSTNAME": "hostname",
            "OS_NAME": "os_name",
            "KERNEL": "kernel",
            "ARCHITECTURE": "architecture",
            "UPTIME": "uptime",
            "CPU_MODEL": "cpu_model",
            "CPU_CORES": "cpu_cores",
            "LOAD_AVERAGE": "load_average",
            "TOTAL_RAM": "total_ram",
            "ROOT_DISK": "root_disk",
            "LOGGED_IN_USER": "logged_in_user",
            "ACTIVE_USERS": "active_users",
            "IP_ADDRESS": "ip_address",
        }

        for raw_line in completed.stdout.splitlines():
            line = raw_line.strip()
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            if key in key_map and val:
                info[key_map[key]] = val

    except (subprocess.TimeoutExpired, OSError):
        return info

    return info


def collect_performance_snapshot(top_n_processes=10, script_path=None):
    """Collect a comprehensive snapshot across all SLRM monitoring modules."""
    if (
        isinstance(top_n_processes, bool)
        or not isinstance(top_n_processes, int)
        or top_n_processes < 1
    ):
        raise ValueError("top_n_processes must be a positive integer.")

    sys_info = get_system_info(script_path=script_path)
    cpu_stats = get_cpu_stats()
    ram_stats = get_ram_stats()
    disk_stats = get_disk_stats()
    partitions = get_disk_partitions()

    pm = ProcessManager()
    top_processes = pm.get_processes(sort_by="cpu", limit=top_n_processes)
    heavy_processes = pm.get_heavy_processes(cpu_threshold=50.0, memory_threshold=10.0)

    alert_summary = check_all_alerts(
        cpu_usage=cpu_stats["usage"],
        ram_usage=ram_stats["usage"],
        disk_usage=disk_stats["usage"],
    )

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system_info": sys_info,
        "cpu": cpu_stats,
        "ram": ram_stats,
        "disk": disk_stats,
        "partitions": partitions,
        "alerts": alert_summary,
        "top_processes": top_processes,
        "heavy_processes": heavy_processes,
    }


def format_text_report(snapshot=None):
    """Format a performance snapshot into a structured human-readable text report."""
    if snapshot is None:
        snapshot = collect_performance_snapshot()

    sys_info = snapshot.get("system_info", {})
    cpu = snapshot.get("cpu", {})
    ram = snapshot.get("ram", {})
    disk = snapshot.get("disk", {})
    partitions = snapshot.get("partitions", [])
    alert_data = snapshot.get("alerts", {})
    top_procs = snapshot.get("top_processes", [])
    heavy_procs = snapshot.get("heavy_processes", [])

    lines = [
        "=" * 72,
        "         SMART LINUX RESOURCE MANAGER (SLRM) - PERFORMANCE REPORT",
        "=" * 72,
        f"Generated At     : {snapshot.get('generated_at', 'N/A')}",
        "",
        "------------------------------------------------------------------------",
        "1. LINUX SYSTEM INFORMATION (via system_info.sh)",
        "------------------------------------------------------------------------",
        f"  Hostname       : {sys_info.get('hostname', 'N/A')}",
        f"  OS / Distro    : {sys_info.get('os_name', 'N/A')}",
        f"  Kernel Version : {sys_info.get('kernel', 'N/A')}",
        f"  Architecture   : {sys_info.get('architecture', 'N/A')}",
        f"  System Uptime  : {sys_info.get('uptime', 'N/A')}",
        f"  CPU Model      : {sys_info.get('cpu_model', 'N/A')}",
        f"  Logical Cores  : {sys_info.get('cpu_cores', 'N/A')}",
        f"  Load Average   : {sys_info.get('load_average', 'N/A')}",
        f"  Current User   : {sys_info.get('logged_in_user', 'N/A')} "
        f"(Active sessions: {sys_info.get('active_users', '1')})",
        f"  IP Address     : {sys_info.get('ip_address', 'N/A')}",
        "",
        "------------------------------------------------------------------------",
        "2. CPU PERFORMANCE SUMMARY",
        "------------------------------------------------------------------------",
        f"  CPU Usage      : {cpu.get('usage', 0.0):.1f}%",
        f"  Physical Cores : {cpu.get('physical_cores', 'N/A')}",
        f"  Total Threads  : {cpu.get('total_threads', 'N/A')}",
        f"  Current Freq   : {cpu.get('current_freq', 0.0):.0f} MHz",
        f"  Max Freq       : {cpu.get('max_freq', 0.0):.0f} MHz",
        f"  Status         : {alert_data.get('statuses', {}).get('cpu', 'N/A')}",
        "",
        "------------------------------------------------------------------------",
        "3. RAM PERFORMANCE SUMMARY",
        "------------------------------------------------------------------------",
        f"  RAM Usage      : {ram.get('usage', 0.0):.1f}%",
        f"  Total RAM      : {ram.get('total_gb', 0.0):.2f} GB",
        f"  Used RAM       : {ram.get('used_gb', 0.0):.2f} GB",
        f"  Available RAM  : {ram.get('available_gb', 0.0):.2f} GB",
        f"  Status         : {alert_data.get('statuses', {}).get('ram', 'N/A')}",
        "",
        "------------------------------------------------------------------------",
        "4. DISK STORAGE & PARTITIONS",
        "------------------------------------------------------------------------",
        f"  Root Path      : {disk.get('path', '/')}",
        f"  Disk Usage     : {disk.get('usage', 0.0):.1f}%",
        f"  Total Storage  : {disk.get('total_gb', 0.0):.2f} GB",
        f"  Used Storage   : {disk.get('used_gb', 0.0):.2f} GB",
        f"  Free Storage   : {disk.get('free_gb', 0.0):.2f} GB",
        f"  Status         : {alert_data.get('statuses', {}).get('disk', 'N/A')}",
    ]

    if partitions:
        lines.append("")
        lines.append("  Active Partitions:")
        lines.append(
            f"    {'Device':<18} {'Mount':<16} {'FS':<10} "
            f"{'Total(GB)':>10} {'Used(GB)':>10} {'Usage':>8}"
        )
        lines.append("    " + "-" * 64)
        for part in partitions:
            lines.append(
                f"    {str(part.get('device', ''))[:17]:<18} "
                f"{str(part.get('mountpoint', ''))[:15]:<16} "
                f"{str(part.get('fstype', ''))[:9]:<10} "
                f"{part.get('total_gb', 0.0):>10.2f} "
                f"{part.get('used_gb', 0.0):>10.2f} "
                f"{part.get('usage', 0.0):>7.1f}%"
            )

    lines.extend([
        "",
        "------------------------------------------------------------------------",
        "5. ACTIVE ALERTS",
        "------------------------------------------------------------------------",
    ])
    active_alerts = alert_data.get("alerts", [])
    if active_alerts:
        for item in active_alerts:
            lines.append(
                f"  * [{item.get('severity', 'WARNING')}] "
                f"{item.get('resource', 'Resource')}: {item.get('message', '')}"
            )
    else:
        lines.append("  No active resource alerts. All metrics are within normal limits.")

    lines.extend([
        "",
        "------------------------------------------------------------------------",
        f"6. TOP {len(top_procs)} PROCESSES (BY CPU & MEMORY)",
        "------------------------------------------------------------------------",
        f"  {'PID':<8} {'Name':<24} {'User':<14} {'CPU %':>8} {'RAM %':>8} {'RAM (MB)':>10}",
        "  " + "-" * 68,
    ])
    for proc in top_procs:
        lines.append(
            f"  {proc.get('pid', 0):<8} "
            f"{str(proc.get('name', 'Unknown'))[:23]:<24} "
            f"{str(proc.get('username') or 'N/A')[:13]:<14} "
            f"{proc.get('cpu_percent', 0.0):>7.1f}% "
            f"{proc.get('memory_percent', 0.0):>7.1f}% "
            f"{proc.get('memory_rss_mb', 0.0):>10.1f}"
        )

    lines.append("")
    lines.append(f"  Heavy Processes Count (CPU >= 50% or RAM >= 10%): {len(heavy_procs)}")
    lines.append("=" * 72)

    return "\n".join(lines) + "\n"


def save_text_report(filepath=None, snapshot=None, output_dir="reports"):
    """Generate and save a plain-text (.txt) performance report.

    Returns the absolute path to the saved report file.
    """
    if snapshot is None:
        snapshot = collect_performance_snapshot()

    if filepath is None:
        os.makedirs(output_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"slrm_report_{stamp}.txt")
    else:
        parent = os.path.dirname(os.path.abspath(filepath))
        if parent:
            os.makedirs(parent, exist_ok=True)

    report_text = format_text_report(snapshot)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_text)

    return os.path.abspath(filepath)


def save_json_report(filepath=None, snapshot=None, output_dir="reports"):
    """Generate and save a JSON (.json) performance report.

    Returns the absolute path to the saved report file.
    """
    if snapshot is None:
        snapshot = collect_performance_snapshot()

    if filepath is None:
        os.makedirs(output_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"slrm_report_{stamp}.json")
    else:
        parent = os.path.dirname(os.path.abspath(filepath))
        if parent:
            os.makedirs(parent, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    return os.path.abspath(filepath)


if __name__ == "__main__":
    print("=== MEMBER 5: LINUX INTEGRATION & PERFORMANCE REPORTS MODULE ===")
    snap = collect_performance_snapshot(top_n_processes=10)
    print(format_text_report(snap))

    txt_path = save_text_report(snapshot=snap)
    json_path = save_json_report(snapshot=snap)
    print(f"[SAVED] Text report : {txt_path}")
    print(f"[SAVED] JSON report : {json_path}")

