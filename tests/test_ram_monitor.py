import unittest

from ram_monitor import get_ram_stats, check_ram_alert


class TestRAMMonitor(unittest.TestCase):

    def test_get_ram_stats_returns_dict(self):
        stats = get_ram_stats()
        self.assertIsInstance(stats, dict)

    def test_get_ram_stats_has_required_keys(self):
        stats = get_ram_stats()
        expected_keys = {"usage", "total_gb", "used_gb", "available_gb"}
        self.assertEqual(set(stats.keys()), expected_keys)

    def test_usage_in_valid_range(self):
        stats = get_ram_stats()
        self.assertGreaterEqual(stats["usage"], 0.0)
        self.assertLessEqual(stats["usage"], 100.0)

    def test_total_gb_positive(self):
        stats = get_ram_stats()
        self.assertGreater(stats["total_gb"], 0.0)

    def test_used_gb_not_exceeds_total(self):
        stats = get_ram_stats()
        self.assertLessEqual(stats["used_gb"], stats["total_gb"])

    def test_available_gb_not_exceeds_total(self):
        stats = get_ram_stats()
        self.assertLessEqual(stats["available_gb"], stats["total_gb"])

    def test_used_gb_non_negative(self):
        stats = get_ram_stats()
        self.assertGreaterEqual(stats["used_gb"], 0.0)

    def test_available_gb_non_negative(self):
        stats = get_ram_stats()
        self.assertGreaterEqual(stats["available_gb"], 0.0)

    def test_values_are_floats(self):
        stats = get_ram_stats()
        for key in ("usage", "total_gb", "used_gb", "available_gb"):
            self.assertIsInstance(
                stats[key], float,
                f"{key} should be float, got {type(stats[key])}"
            )

    # ---- Alert function tests ----

    def test_alert_high_usage(self):
        result = check_ram_alert(90.0)
        self.assertTrue(result.startswith("[ALERT]"))
        self.assertIn("High RAM usage", result)

    def test_alert_at_threshold(self):
        result = check_ram_alert(85.0)
        self.assertTrue(result.startswith("[STATUS]"))

    def test_alert_above_threshold(self):
        result = check_ram_alert(85.1)
        self.assertTrue(result.startswith("[ALERT]"))

    def test_status_normal_usage(self):
        result = check_ram_alert(50.0)
        self.assertTrue(result.startswith("[STATUS]"))
        self.assertIn("normal", result)

    def test_status_zero_usage(self):
        result = check_ram_alert(0.0)
        self.assertTrue(result.startswith("[STATUS]"))

    def test_alert_full_usage(self):
        result = check_ram_alert(100.0)
        self.assertTrue(result.startswith("[ALERT]"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

