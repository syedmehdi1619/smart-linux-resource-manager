import os
import sys

import psutil
import matplotlib.pyplot as plt


def get_disk_stats(path=None):
    """Returns current disk usage statistics dictionary for the given path.

    If path is None, uses the system root: '/' on Linux, or the system
    drive root on Windows (derived dynamically, not hard-coded).
    """
    if path is None:
        # Derive system root in a cross-platform way
        path = os.path.abspath(os.sep)

    try:
        usage = psutil.disk_usage(path)
    except PermissionError:
        print(f"[ERROR] Permission denied when accessing: {path}")
        return {
            "path": path,
            "usage": 0.0,
            "total_gb": 0.0,
            "used_gb": 0.0,
            "free_gb": 0.0,
        }
    except FileNotFoundError:
        print(f"[ERROR] Path not found: {path}")
        return {
            "path": path,
            "usage": 0.0,
            "total_gb": 0.0,
            "used_gb": 0.0,
            "free_gb": 0.0,
        }
    except OSError as e:
        print(f"[ERROR] OS error accessing {path}: {e}")
        return {
            "path": path,
            "usage": 0.0,
            "total_gb": 0.0,
            "used_gb": 0.0,
            "free_gb": 0.0,
        }

    # Using 1024**3 (GiB) for GB conversion
    stats = {
        "path": path,
        "usage": usage.percent,
        "total_gb": round(usage.total / (1024 ** 3), 2),
        "used_gb": round(usage.used / (1024 ** 3), 2),
        "free_gb": round(usage.free / (1024 ** 3), 2),
    }
    return stats


def check_disk_alert(disk_usage):
    """Checks for low disk space and returns alert status."""
    if disk_usage > 90.0:
        return "[ALERT] Warning: Low storage! Free disk space is running out."
    return "[STATUS] Disk space is sufficient."


def get_disk_partitions():
    """Returns a list of dicts for real disk partitions.

    Each dict contains: device, mountpoint, fstype, total_gb, used_gb,
    free_gb, usage.

    On Linux, pseudo-filesystems (tmpfs, devtmpfs, squashfs, etc.) and
    snap/loop mounts are skipped to keep the list clean on Ubuntu.
    Inaccessible partitions are silently skipped.
    """
    pseudo_fstypes = {"tmpfs", "devtmpfs", "squashfs", "overlay", "devpts",
                      "sysfs", "proc", "cgroup", "cgroup2", "pstore",
                      "debugfs", "securityfs", "hugetlbfs", "mqueue",
                      "fusectl", "configfs", "binfmt_misc", "autofs",
                      "efivarfs", "tracefs", "bpf", "nsfs", "ramfs"}

    partitions = []
    for part in psutil.disk_partitions(all=False):
        # Skip pseudo-filesystems on Linux
        if part.fstype in pseudo_fstypes:
            continue

        # Skip snap/loop mounts on Linux
        if part.device.startswith("/dev/loop") or "/snap/" in part.mountpoint:
            continue

        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue

        # Using 1024**3 (GiB) for GB conversion
        partitions.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total_gb": round(usage.total / (1024 ** 3), 2),
            "used_gb": round(usage.used / (1024 ** 3), 2),
            "free_gb": round(usage.free / (1024 ** 3), 2),
            "usage": usage.percent,
        })

    return partitions


def plot_disk_usage():
    """Standalone Matplotlib chart showing used vs free disk space.

    For standalone testing only; the GUI must never call this because
    it opens a separate Matplotlib window.
    """
    stats = get_disk_stats()

    labels = ["Used", "Free"]
    sizes = [stats["used_gb"], stats["free_gb"]]
    colors = ["#f38ba8", "#a6e3a1"]
    explode = (0.05, 0)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct="%1.1f%%", shadow=True, startangle=140,
           textprops={"fontsize": 12})
    ax.set_title(f"Disk Usage – {stats['path']}\n"
                 f"Total: {stats['total_gb']} GB", fontsize=14)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print("=== MEMBER 2: DISK MONITORING MODULE ===")

    # 1. Print current stats and alerts
    stats = get_disk_stats()
    print(f"Path: {stats['path']}")
    print(f"Current Disk Usage: {stats['usage']}%")
    print(f"Total Disk: {stats['total_gb']} GB")
    print(f"Used Disk: {stats['used_gb']} GB")
    print(f"Free Disk: {stats['free_gb']} GB")
    print(check_disk_alert(stats['usage']))

    print("-" * 40)

    # 2. List disk partitions
    print("\nDisk Partitions:")
    partitions = get_disk_partitions()
    for p in partitions:
        print(f"  {p['device']}  ->  {p['mountpoint']}  "
              f"({p['fstype']})  "
              f"Total: {p['total_gb']} GB  "
              f"Used: {p['used_gb']} GB  "
              f"Free: {p['free_gb']} GB  "
              f"Usage: {p['usage']}%")

    print("-" * 40)

    # 3. Show Disk Usage Chart
    plot_disk_usage()

