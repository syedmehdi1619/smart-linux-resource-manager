import unittest
import subprocess
import sys

import psutil

from unittest.mock import patch

from process_manager import ProcessManager


class TestProcessManager(unittest.TestCase):

    def setUp(self):
        self.manager = ProcessManager()

    def test_get_processes_returns_list(self):
        processes = self.manager.get_processes(limit=10)

        self.assertIsInstance(processes, list)
        self.assertLessEqual(len(processes), 10)

    def test_memory_sorting(self):
        processes = self.manager.get_processes(
            sort_by="memory",
            limit=10
        )

        memory_values = [
            process["memory_percent"]
            for process in processes
        ]

        self.assertEqual(
            memory_values,
            sorted(memory_values, reverse=True)
        )

    def test_invalid_sort_option(self):
        with self.assertRaises(ValueError):
            self.manager.get_processes(sort_by="invalid")

    def test_invalid_pid(self):
        with self.assertRaises(ValueError):
            self.manager.terminate_process(
                pid=0,
                expected_create_time=1.0
            )

    def test_invalid_cpu_threshold(self):
        with self.assertRaises(ValueError):
            self.manager.get_heavy_processes(
                cpu_threshold=101
            )

    def test_invalid_memory_threshold(self):
        with self.assertRaises(ValueError):
            self.manager.get_heavy_processes(
                memory_threshold=-1
            )

    @patch.object(ProcessManager, "get_processes")
    def test_high_cpu_process_detection(self, mock_processes):

        mock_processes.return_value = [
            {
                "pid": 1001,
                "name": "test_cpu",
                "cpu_percent": 75.0,
                "memory_percent": 2.0
            }
        ]

        heavy = self.manager.get_heavy_processes(
            cpu_threshold=50,
            memory_threshold=10
        )

        self.assertEqual(len(heavy), 1)
        self.assertTrue(heavy[0]["high_cpu"])
        self.assertFalse(heavy[0]["high_memory"])

    @patch.object(ProcessManager, "get_processes")
    def test_high_memory_process_detection(self, mock_processes):

        mock_processes.return_value = [
            {
                "pid": 1002,
                "name": "test_memory",
                "cpu_percent": 5.0,
                "memory_percent": 15.0
            }
        ]

        heavy = self.manager.get_heavy_processes(
            cpu_threshold=50,
            memory_threshold=10
        )

        self.assertEqual(len(heavy), 1)
        self.assertFalse(heavy[0]["high_cpu"])
        self.assertTrue(heavy[0]["high_memory"])

    @patch.object(ProcessManager, "get_processes")
    def test_normal_process_not_detected(self, mock_processes):

        mock_processes.return_value = [
            {
                "pid": 1003,
                "name": "normal_process",
                "cpu_percent": 5.0,
                "memory_percent": 2.0
            }
        ]

        heavy = self.manager.get_heavy_processes(
            cpu_threshold=50,
            memory_threshold=10
        )

        self.assertEqual(len(heavy), 0)

    def test_pid_identity_mismatch(self):
        child = subprocess.Popen([
            sys.executable,
            "-c",
            "import time; time.sleep(60)"
        ])

        try:
            process = psutil.Process(child.pid)
            wrong_creation_time = process.create_time() + 1000

            result = self.manager.terminate_process(
                pid=child.pid,
                expected_create_time=wrong_creation_time
            )

            self.assertFalse(result["success"])
            self.assertEqual(
                result["message"],
                "Process identity mismatch."
            )
            self.assertIsNone(child.poll())

        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=3)

    def test_successful_termination(self):
        child = subprocess.Popen([
            sys.executable,
            "-c",
            "import time; time.sleep(60)"
        ])

        try:
            process = psutil.Process(child.pid)
            creation_time = process.create_time()

            result = self.manager.terminate_process(
                pid=child.pid,
                expected_create_time=creation_time
            )

            self.assertTrue(result["success"])
            child.wait(timeout=3)

        finally:
            if child.poll() is None:
                child.kill()
                child.wait()

    def test_name_sorting(self):
        processes = self.manager.get_processes(
            sort_by="name",
            limit=20
        )

        names = [process["name"].lower() for process in processes]

        self.assertEqual(names, sorted(names))

    def test_pid_sorting(self):
        processes = self.manager.get_processes(
            sort_by="pid",
            limit=20
        )

        pids = [process["pid"] for process in processes]

        self.assertEqual(pids, sorted(pids))

    def test_nan_cpu_threshold_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.get_heavy_processes(
                cpu_threshold=float("nan")
            )

    def test_infinite_memory_threshold_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.get_heavy_processes(
                memory_threshold=float("inf")
            )

    def test_infinite_cpu_threshold_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.get_heavy_processes(
                cpu_threshold=float("inf")
            )
if __name__ == "__main__":
    unittest.main(verbosity=2)
