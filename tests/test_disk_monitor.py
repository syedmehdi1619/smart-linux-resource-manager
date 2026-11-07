import unittest

from disk_monitor import get_disk_stats, check_disk_alert, get_disk_partitions


class TestDiskMonitor(unittest.TestCase):

    # ---- get_disk_stats tests ----

    def test_get_disk_stats_returns_dict(self):
        stats = get_disk_stats()
        self.assertIsInstance(stats, dict)

    def test_get_disk_stats_has_required_keys(self):
        stats = get_disk_stats()
        expected_keys = {"path", "usage", "total_gb", "used_gb", "free_gb"}
        self.assertEqual(set(stats.keys()), expected_keys)

    def test_usage_in_valid_range(self):
        stats = get_disk_stats()
        self.assertGreaterEqual(stats["usage"], 0.0)
        self.assertLessEqual(stats["usage"], 100.0)

    def test_total_gb_positive(self):
        stats = get_disk_stats()
        self.assertGreater(stats["total_gb"], 0.0)

    def test_used_gb_not_exceeds_total(self):
        stats = get_disk_stats()
        self.assertLessEqual(stats["used_gb"], stats["total_gb"])

    def test_free_gb_not_exceeds_total(self):
        stats = get_disk_stats()
        self.assertLessEqual(stats["free_gb"], stats["total_gb"])

    def test_used_gb_non_negative(self):
        stats = get_disk_stats()
        self.assertGreaterEqual(stats["used_gb"], 0.0)

    def test_free_gb_non_negative(self):
        stats = get_disk_stats()
        self.assertGreaterEqual(stats["free_gb"], 0.0)

    def test_path_is_string(self):
        stats = get_disk_stats()
        self.assertIsInstance(stats["path"], str)

    def test_values_are_floats(self):
        stats = get_disk_stats()
        for key in ("usage", "total_gb", "used_gb", "free_gb"):
            self.assertIsInstance(
                stats[key], float,
                f"{key} should be float, got {type(stats[key])}"
            )

    def test_invalid_path_returns_zeroes(self):
        stats = get_disk_stats(path="/nonexistent/path/xyz_test_12345")
        self.assertEqual(stats["usage"], 0.0)
        self.assertEqual(stats["total_gb"], 0.0)

    def test_explicit_root_path(self):
        import os
        root = os.path.abspath(os.sep)
        stats = get_disk_stats(path=root)
        self.assertGreater(stats["total_gb"], 0.0)
        self.assertEqual(stats["path"], root)

    # ---- check_disk_alert tests ----

    def test_alert_high_usage(self):
        result = check_disk_alert(95.0)
        self.assertTrue(result.startswith("[ALERT]"))
        self.assertIn("Low storage", result)

    def test_alert_at_threshold(self):
        result = check_disk_alert(90.0)
        self.assertTrue(result.startswith("[STATUS]"))

    def test_alert_above_threshold(self):
        result = check_disk_alert(90.1)
        self.assertTrue(result.startswith("[ALERT]"))

    def test_status_normal_usage(self):
        result = check_disk_alert(50.0)
        self.assertTrue(result.startswith("[STATUS]"))
        self.assertIn("sufficient", result)

    def test_status_zero_usage(self):
        result = check_disk_alert(0.0)
        self.assertTrue(result.startswith("[STATUS]"))

    def test_alert_full_usage(self):
        result = check_disk_alert(100.0)
        self.assertTrue(result.startswith("[ALERT]"))

    # ---- get_disk_partitions tests ----

    def test_get_disk_partitions_returns_list(self):
        partitions = get_disk_partitions()
        self.assertIsInstance(partitions, list)

    def test_partition_has_required_keys(self):
        partitions = get_disk_partitions()
        expected_keys = {"device", "mountpoint", "fstype",
                         "total_gb", "used_gb", "free_gb", "usage"}
        if len(partitions) > 0:
            self.assertEqual(set(partitions[0].keys()), expected_keys)

    def test_partition_usage_in_valid_range(self):
        partitions = get_disk_partitions()
        for p in partitions:
            self.assertGreaterEqual(p["usage"], 0.0)
            self.assertLessEqual(p["usage"], 100.0)

    def test_partition_total_positive(self):
        partitions = get_disk_partitions()
        for p in partitions:
            self.assertGreater(p["total_gb"], 0.0)

    def test_partition_used_not_exceeds_total(self):
        partitions = get_disk_partitions()
        for p in partitions:
            self.assertLessEqual(p["used_gb"], p["total_gb"])

    def test_at_least_one_partition(self):
        partitions = get_disk_partitions()
        self.assertGreater(len(partitions), 0,
                           "Expected at least one real partition")


if __name__ == "__main__":
    unittest.main(verbosity=2)

