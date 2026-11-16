import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from alerts import (
    AlertManager,
    check_all_alerts,
    send_desktop_notification,
)


class TestAlertsModule(unittest.TestCase):

    def test_check_all_alerts_normal_usage(self):
        result = check_all_alerts(
            cpu_usage=35.0,
            ram_usage=45.0,
            disk_usage=50.0,
        )
        self.assertFalse(result["has_alerts"])
        self.assertEqual(len(result["alerts"]), 0)
        self.assertTrue(result["statuses"]["cpu"].startswith("[STATUS]"))
        self.assertTrue(result["statuses"]["ram"].startswith("[STATUS]"))
        self.assertTrue(result["statuses"]["disk"].startswith("[STATUS]"))

    def test_check_all_alerts_high_cpu(self):
        result = check_all_alerts(
            cpu_usage=90.0,
            ram_usage=40.0,
            disk_usage=50.0,
        )
        self.assertTrue(result["has_alerts"])
        self.assertEqual(len(result["alerts"]), 1)
        self.assertEqual(result["alerts"][0]["resource"], "CPU")
        self.assertEqual(result["alerts"][0]["severity"], "WARNING")
        self.assertTrue(result["statuses"]["cpu"].startswith("[ALERT]"))

    def test_check_all_alerts_critical_severity(self):
        result = check_all_alerts(
            cpu_usage=96.5,
            ram_usage=97.0,
            disk_usage=95.5,
        )
        self.assertTrue(result["has_alerts"])
        self.assertEqual(len(result["alerts"]), 3)
        for alert in result["alerts"]:
            self.assertEqual(alert["severity"], "CRITICAL")

    def test_check_all_alerts_live_metrics(self):
        result = check_all_alerts()
        self.assertIn("timestamp", result)
        self.assertIn("has_alerts", result)
        self.assertIn("alerts", result)
        self.assertIn("metrics", result)
        self.assertGreaterEqual(result["metrics"]["cpu_usage"], 0.0)
        self.assertLessEqual(result["metrics"]["cpu_usage"], 100.0)

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            check_all_alerts(cpu_usage=50.0, cpu_threshold=105.0)
        with self.assertRaises(ValueError):
            check_all_alerts(cpu_usage=50.0, ram_threshold=-5.0)
        with self.assertRaises(ValueError):
            check_all_alerts(cpu_usage=50.0, disk_threshold=float("nan"))
        with self.assertRaises(ValueError):
            check_all_alerts(cpu_usage=True)

    @patch("alerts.shutil.which", return_value="/usr/bin/notify-send")
    @patch("alerts.subprocess.run")
    def test_send_desktop_notification_notify_send_success(self, mock_run, _mock_which):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        res = send_desktop_notification("Test Title", "Test Message", urgency="critical")
        self.assertTrue(res["sent"])
        self.assertEqual(res["method"], "notify-send")
        mock_run.assert_called_once()

    @patch("alerts.shutil.which", return_value=None)
    def test_send_desktop_notification_fallback(self, _mock_which):
        res = send_desktop_notification("Test Title", "Test Message", urgency="normal")
        self.assertFalse(res["sent"])
        self.assertEqual(res["method"], "fallback")
        self.assertIn("Test Title", res["message"])

    def test_send_desktop_notification_invalid_args(self):
        with self.assertRaises(ValueError):
            send_desktop_notification("", "Message")
        with self.assertRaises(ValueError):
            send_desktop_notification("Title", "")
        with self.assertRaises(ValueError):
            send_desktop_notification("Title", "Message", urgency="invalid_urgency")

    def test_alert_manager_history_and_cooldown(self):
        manager = AlertManager(cooldown_seconds=60.0)
        res1 = manager.evaluate(cpu_usage=91.0, ram_usage=30.0, disk_usage=40.0)
        self.assertTrue(res1["has_alerts"])
        self.assertEqual(len(manager.get_history()), 1)

        # Second evaluation within cooldown should not duplicate history entry
        manager.evaluate(cpu_usage=92.0, ram_usage=30.0, disk_usage=40.0)
        self.assertEqual(len(manager.get_history()), 1)

        # Clear history resets cooldown
        manager.clear_history()
        self.assertEqual(len(manager.get_history()), 0)

    def test_alert_manager_log_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_alerts.log")
            manager = AlertManager(cooldown_seconds=0.0, log_filepath=log_file)
            manager.evaluate(
                cpu_usage=90.0,
                ram_usage=20.0,
                disk_usage=30.0,
                log_to_file=True,
            )
            self.assertTrue(os.path.isfile(log_file))
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("CPU", content)
            self.assertIn("[ALERT]", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)

