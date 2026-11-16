import json
import os
import subprocess
import tempfile
import unittest

from reports import (
    DEFAULT_SCRIPT_PATH,
    collect_performance_snapshot,
    format_text_report,
    get_system_info,
    save_json_report,
    save_text_report,
)


class TestReportsAndLinuxIntegration(unittest.TestCase):

    def test_bash_script_exists_and_executes(self):
        self.assertTrue(
            os.path.isfile(DEFAULT_SCRIPT_PATH),
            f"Expected system_info.sh at {DEFAULT_SCRIPT_PATH}",
        )
        completed = subprocess.run(
            ["bash", DEFAULT_SCRIPT_PATH, "--kv"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("HOSTNAME=", completed.stdout)
        self.assertIn("OS_NAME=", completed.stdout)
        self.assertIn("KERNEL=", completed.stdout)

    def test_bash_script_json_mode(self):
        completed = subprocess.run(
            ["bash", DEFAULT_SCRIPT_PATH, "--json"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        parsed = json.loads(completed.stdout)
        self.assertIn("hostname", parsed)
        self.assertIn("os_name", parsed)
        self.assertIn("kernel", parsed)

    def test_get_system_info_returns_required_keys(self):
        info = get_system_info()
        self.assertIsInstance(info, dict)
        expected_keys = {
            "timestamp",
            "hostname",
            "os_name",
            "kernel",
            "architecture",
            "uptime",
            "cpu_model",
            "cpu_cores",
            "load_average",
            "total_ram",
            "root_disk",
            "logged_in_user",
            "active_users",
            "ip_address",
        }
        self.assertEqual(set(info.keys()), expected_keys)
        for key in expected_keys:
            self.assertIsInstance(info[key], str)
            self.assertGreater(len(info[key]), 0)

    def test_get_system_info_fallback_on_missing_script(self):
        info = get_system_info(script_path="/nonexistent/system_info.sh")
        self.assertIsInstance(info, dict)
        self.assertIn("hostname", info)
        self.assertTrue(len(info["hostname"]) > 0)

    def test_collect_performance_snapshot_structure(self):
        snapshot = collect_performance_snapshot(top_n_processes=5)
        self.assertIsInstance(snapshot, dict)
        for section in (
            "generated_at",
            "system_info",
            "cpu",
            "ram",
            "disk",
            "partitions",
            "alerts",
            "top_processes",
            "heavy_processes",
        ):
            self.assertIn(section, snapshot)
        self.assertLessEqual(len(snapshot["top_processes"]), 5)

    def test_collect_performance_snapshot_invalid_top_n(self):
        with self.assertRaises(ValueError):
            collect_performance_snapshot(top_n_processes=0)
        with self.assertRaises(ValueError):
            collect_performance_snapshot(top_n_processes=True)

    def test_format_text_report_contains_sections(self):
        snapshot = collect_performance_snapshot(top_n_processes=3)
        text = format_text_report(snapshot)
        self.assertIn("SMART LINUX RESOURCE MANAGER (SLRM) - PERFORMANCE REPORT", text)
        self.assertIn("1. LINUX SYSTEM INFORMATION", text)
        self.assertIn("2. CPU PERFORMANCE SUMMARY", text)
        self.assertIn("3. RAM PERFORMANCE SUMMARY", text)
        self.assertIn("4. DISK STORAGE & PARTITIONS", text)
        self.assertIn("5. ACTIVE ALERTS", text)
        self.assertIn("6. TOP", text)

    def test_save_text_and_json_reports(self):
        snapshot = collect_performance_snapshot(top_n_processes=3)
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = save_text_report(snapshot=snapshot, output_dir=tmpdir)
            json_path = save_json_report(snapshot=snapshot, output_dir=tmpdir)

            self.assertTrue(os.path.isfile(txt_path))
            self.assertTrue(os.path.isfile(json_path))

            with open(txt_path, "r", encoding="utf-8") as f:
                txt_content = f.read()
            self.assertIn("PERFORMANCE REPORT", txt_content)

            with open(json_path, "r", encoding="utf-8") as f:
                json_content = json.load(f)
            self.assertEqual(
                json_content["system_info"]["hostname"],
                snapshot["system_info"]["hostname"],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

