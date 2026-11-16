"""
alerts.py - High Resource Usage Alert & Notification Module
Smart Linux Resource Manager (SLRM)

Provides centralized resource threshold evaluation, alert history tracking,
alert file logging, and Ubuntu desktop notifications via subprocess (`notify-send`).

Author: Member 5 (Linux Integration, Alerts & Reports)
"""

from collections import deque
from datetime import datetime
import math
import os
import shutil
import subprocess
import time

from cpu_monitor import get_cpu_stats, check_cpu_alert
from ram_monitor import get_ram_stats, check_ram_alert
from disk_monitor import get_disk_stats, check_disk_alert

DEFAULT_CPU_THRESHOLD = 85.0
DEFAULT_RAM_THRESHOLD = 85.0
DEFAULT_DISK_THRESHOLD = 90.0
DEFAULT_COOLDOWN_SECONDS = 30.0


def _validate_percentage(value, name="Threshold"):
    """Validate that a percentage/threshold is a finite number in [0, 100]."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not (0.0 <= float(value) <= 100.0)
    ):
        raise ValueError(f"{name} must be a finite number between 0 and 100.")
    return float(value)


def send_desktop_notification(title, message, urgency="critical", timeout_sec=3):
    """Send a desktop notification on Ubuntu Linux using `notify-send` via subprocess.

    Falls back gracefully when `notify-send` is unavailable (e.g. headless server,
    Windows, or macOS test environments).

    Returns a dictionary:
        {
            "sent": bool,
            "method": "notify-send" | "fallback",
            "message": str
        }
    """
    if not title or not isinstance(title, str):
        raise ValueError("Notification title must be a non-empty string.")
    if not message or not isinstance(message, str):
        raise ValueError("Notification message must be a non-empty string.")

    valid_urgencies = ("low", "normal", "critical")
    if urgency not in valid_urgencies:
        raise ValueError(f"Invalid urgency. Choose from {valid_urgencies}")

    notify_bin = shutil.which("notify-send")
    if notify_bin:
        try:
            result = subprocess.run(
                [notify_bin, "-u", urgency, "-a", "SLRM", title, message],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            if result.returncode == 0:
                return {
                    "sent": True,
                    "method": "notify-send",
                    "message": "Desktop notification delivered via notify-send.",
                }
            err_detail = (result.stderr or "").strip() or f"exit code {result.returncode}"
            return {
                "sent": False,
                "method": "notify-send",
                "message": f"notify-send failed: {err_detail}",
            }
        except subprocess.TimeoutExpired:
            return {
                "sent": False,
                "method": "notify-send",
                "message": "notify-send timed out.",
            }
        except OSError as exc:
            return {
                "sent": False,
                "method": "notify-send",
                "message": f"OS error invoking notify-send: {exc}",
            }

    return {
        "sent": False,
        "method": "fallback",
        "message": f"[NOTIFICATION] {title}: {message}",
    }


def check_all_alerts(
    cpu_usage=None,
    ram_usage=None,
    disk_usage=None,
    cpu_threshold=DEFAULT_CPU_THRESHOLD,
    ram_threshold=DEFAULT_RAM_THRESHOLD,
    disk_threshold=DEFAULT_DISK_THRESHOLD,
):
    """Evaluate CPU, RAM, and Disk usage against thresholds.

    If any usage value is None, live statistics are fetched from the respective
    monitoring module.

    Returns a dictionary with keys:
        - timestamp (str)
        - has_alerts (bool)
        - alerts (list of alert dicts)
        - statuses (dict with 'cpu', 'ram', 'disk' status strings)
        - metrics (dict with 'cpu_usage', 'ram_usage', 'disk_usage')
    """
    cpu_threshold = _validate_percentage(cpu_threshold, "CPU threshold")
    ram_threshold = _validate_percentage(ram_threshold, "RAM threshold")
    disk_threshold = _validate_percentage(disk_threshold, "Disk threshold")

    if cpu_usage is None:
        cpu_usage = float(get_cpu_stats()["usage"])
    else:
        cpu_usage = _validate_percentage(cpu_usage, "CPU usage")

    if ram_usage is None:
        ram_usage = float(get_ram_stats()["usage"])
    else:
        ram_usage = _validate_percentage(ram_usage, "RAM usage")

    if disk_usage is None:
        disk_usage = float(get_disk_stats()["usage"])
    else:
        disk_usage = _validate_percentage(disk_usage, "Disk usage")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts = []

    # Evaluate CPU
    if cpu_usage > cpu_threshold:
        base_msg = check_cpu_alert(max(cpu_usage, 85.1))
        severity = "CRITICAL" if cpu_usage >= 95.0 else "WARNING"
        alerts.append({
            "resource": "CPU",
            "usage": round(cpu_usage, 2),
            "threshold": cpu_threshold,
            "severity": severity,
            "message": f"{base_msg} ({cpu_usage:.1f}% > {cpu_threshold:.1f}%)",
            "timestamp": now_str,
        })
        cpu_status = f"[ALERT] Warning: High CPU usage detected! ({cpu_usage:.1f}%)"
    else:
        cpu_status = "[STATUS] CPU usage is normal."

    # Evaluate RAM
    if ram_usage > ram_threshold:
        base_msg = check_ram_alert(max(ram_usage, 85.1))
        severity = "CRITICAL" if ram_usage >= 95.0 else "WARNING"
        alerts.append({
            "resource": "RAM",
            "usage": round(ram_usage, 2),
            "threshold": ram_threshold,
            "severity": severity,
            "message": f"{base_msg} ({ram_usage:.1f}% > {ram_threshold:.1f}%)",
            "timestamp": now_str,
        })
        ram_status = f"[ALERT] Warning: High RAM usage detected! ({ram_usage:.1f}%)"
    else:
        ram_status = "[STATUS] RAM usage is normal."

    # Evaluate Disk
    if disk_usage > disk_threshold:
        base_msg = check_disk_alert(max(disk_usage, 90.1))
        severity = "CRITICAL" if disk_usage >= 95.0 else "WARNING"
        alerts.append({
            "resource": "Disk",
            "usage": round(disk_usage, 2),
            "threshold": disk_threshold,
            "severity": severity,
            "message": f"{base_msg} ({disk_usage:.1f}% > {disk_threshold:.1f}%)",
            "timestamp": now_str,
        })
        disk_status = (
            f"[ALERT] Warning: Low storage! Free disk space is running out. ({disk_usage:.1f}%)"
        )
    else:
        disk_status = "[STATUS] Disk space is sufficient."

    return {
        "timestamp": now_str,
        "has_alerts": len(alerts) > 0,
        "alerts": alerts,
        "statuses": {
            "cpu": cpu_status,
            "ram": ram_status,
            "disk": disk_status,
        },
        "metrics": {
            "cpu_usage": round(cpu_usage, 2),
            "ram_usage": round(ram_usage, 2),
            "disk_usage": round(disk_usage, 2),
        },
    }


class AlertManager:
    """Manages resource alerts, cooldown-throttled notifications, and alert history."""

    def __init__(
        self,
        cpu_threshold=DEFAULT_CPU_THRESHOLD,
        ram_threshold=DEFAULT_RAM_THRESHOLD,
        disk_threshold=DEFAULT_DISK_THRESHOLD,
        cooldown_seconds=DEFAULT_COOLDOWN_SECONDS,
        max_history=100,
        log_filepath=None,
    ):
        self.cpu_threshold = _validate_percentage(cpu_threshold, "CPU threshold")
        self.ram_threshold = _validate_percentage(ram_threshold, "RAM threshold")
        self.disk_threshold = _validate_percentage(disk_threshold, "Disk threshold")

        if (
            isinstance(cooldown_seconds, bool)
            or not isinstance(cooldown_seconds, (int, float))
            or not math.isfinite(cooldown_seconds)
            or cooldown_seconds < 0
        ):
            raise ValueError("Cooldown seconds must be a non-negative number.")

        if (
            isinstance(max_history, bool)
            or not isinstance(max_history, int)
            or max_history < 1
        ):
            raise ValueError("max_history must be a positive integer.")

        self.cooldown_seconds = float(cooldown_seconds)
        self.history = deque(maxlen=max_history)
        self._last_alert_time = {}
        self.log_filepath = log_filepath

    def evaluate(
        self,
        cpu_usage=None,
        ram_usage=None,
        disk_usage=None,
        notify_desktop=False,
        log_to_file=False,
    ):
        """Check system metrics, record new alerts (respecting cooldown), and optionally notify."""
        result = check_all_alerts(
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            disk_usage=disk_usage,
            cpu_threshold=self.cpu_threshold,
            ram_threshold=self.ram_threshold,
            disk_threshold=self.disk_threshold,
        )

        now_mono = time.monotonic()
        triggered_notifications = []

        for alert in result["alerts"]:
            resource = alert["resource"]
            last_time = self._last_alert_time.get(resource)

            if last_time is None or (now_mono - last_time) >= self.cooldown_seconds:
                self._last_alert_time[resource] = now_mono
                self.history.appendleft(alert)

                if log_to_file and self.log_filepath:
                    self.log_alert_to_file(alert, self.log_filepath)

                if notify_desktop:
                    urgency = "critical" if alert["severity"] == "CRITICAL" else "normal"
                    notif = send_desktop_notification(
                        title=f"SLRM {alert['severity']}: High {resource} Usage",
                        message=f"{resource} usage is at {alert['usage']:.1f}% (Threshold: {alert['threshold']:.1f}%)",
                        urgency=urgency,
                    )
                    triggered_notifications.append(notif)

        result["notifications"] = triggered_notifications
        return result

    def log_alert_to_file(self, alert, filepath=None):
        """Append a single alert entry to a log file."""
        target_path = filepath or self.log_filepath or "alerts.log"
        parent_dir = os.path.dirname(os.path.abspath(target_path))
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        line = (
            f"[{alert.get('timestamp', '')}] "
            f"[{alert.get('severity', 'WARNING')}] "
            f"{alert.get('resource', 'System')}: "
            f"{alert.get('message', '')}\n"
        )
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(line)
        return os.path.abspath(target_path)

    def get_history(self):
        """Return alert history as a list (newest first)."""
        return list(self.history)

    def clear_history(self):
        """Clear stored alert history and reset cooldown timers."""
        self.history.clear()
        self._last_alert_time.clear()


if __name__ == "__main__":
    print("=== MEMBER 5: HIGH RESOURCE USAGE ALERTS MODULE ===")
    manager = AlertManager()
    evaluation = manager.evaluate(notify_desktop=True)

    metrics = evaluation["metrics"]
    print(f"Timestamp  : {evaluation['timestamp']}")
    print(f"CPU Usage  : {metrics['cpu_usage']:.1f}%  ->  {evaluation['statuses']['cpu']}")
    print(f"RAM Usage  : {metrics['ram_usage']:.1f}%  ->  {evaluation['statuses']['ram']}")
    print(f"Disk Usage : {metrics['disk_usage']:.1f}%  ->  {evaluation['statuses']['disk']}")
    print("-" * 55)

    if evaluation["has_alerts"]:
        print(f"Active Alerts ({len(evaluation['alerts'])}):")
        for item in evaluation["alerts"]:
            print(f"  - [{item['severity']}] {item['resource']}: {item['message']}")
    else:
        print("All system resources are operating within normal thresholds.")

