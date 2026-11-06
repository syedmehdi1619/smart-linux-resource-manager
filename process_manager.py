import math
import psutil


class ProcessManager:
    """Collects and manages information about system processes."""

    def get_processes(self, sort_by="cpu", limit=None):
        """
        Return running processes with CPU and memory information.

        sort_by: 'cpu', 'memory', 'name', or 'pid'
        limit: Maximum number of processes to return.
        """

        valid_sort_options = ("cpu", "memory", "name", "pid")

        if sort_by not in valid_sort_options:
            raise ValueError(
                f"Invalid sort option. Choose from {valid_sort_options}"
            )

        if limit is not None:
            if (
                isinstance(limit, bool)
                or not isinstance(limit, int)
                or limit < 1
            ):
                raise ValueError("Limit must be a positive integer.")

        process_list = []

        for process in psutil.process_iter(
            attrs=[
                "pid",
                "name",
                "username",
                "status",
                "memory_info",
                "create_time"
            ]
        ):
            try:
                info = process.info
                memory_info = info.get("memory_info")

                process_data = {
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "username": info["username"],
                    "status": info["status"],
                    "cpu_percent": process.cpu_percent(interval=None),
                    "memory_percent": process.memory_percent(),
                    "memory_rss_mb": (
                        round(memory_info.rss / (1024 * 1024), 2)
                        if memory_info else 0.0
                    ),
                    "memory_vms_mb": (
                        round(memory_info.vms / (1024 * 1024), 2)
                        if memory_info else 0.0
                    ),
                    "create_time": info["create_time"]
                }

                process_list.append(process_data)

            except psutil.ZombieProcess:
                continue

            except psutil.NoSuchProcess:
                continue

            except psutil.AccessDenied:
                continue

        if sort_by == "cpu":
            process_list.sort(
                key=lambda p: p["cpu_percent"],
                reverse=True
            )

        elif sort_by == "memory":
            process_list.sort(
                key=lambda p: p["memory_percent"],
                reverse=True
            )

        elif sort_by == "name":
            process_list.sort(
                key=lambda p: p["name"].lower()
            )

        elif sort_by == "pid":
            process_list.sort(
                key=lambda p: p["pid"]
            )

        if limit is not None:
            process_list = process_list[:limit]

        return process_list

    def get_heavy_processes(
        self,
        cpu_threshold=50.0,
        memory_threshold=10.0
    ):
        """
        Identify processes exceeding CPU or RAM thresholds.
        """

        for threshold, name in (
            (cpu_threshold, "CPU"),
            (memory_threshold, "Memory")
        ):
            if (
                isinstance(threshold, bool)
                or not isinstance(threshold, (int, float))
                or not math.isfinite(threshold)
                or not 0 <= threshold <= 100
            ):
                raise ValueError(
                    f"{name} threshold must be between 0 and 100."
                )

        processes = self.get_processes(sort_by="cpu")

        heavy_processes = []

        for process in processes:
            high_cpu = (
                process["cpu_percent"] >= cpu_threshold
            )

            high_memory = (
                process["memory_percent"] >= memory_threshold
            )

            if high_cpu or high_memory:
                process["high_cpu"] = high_cpu
                process["high_memory"] = high_memory
                heavy_processes.append(process)

        return heavy_processes

    def terminate_process(
        self,
        pid,
        expected_create_time,
        timeout=3
    ):
        """
        Safely request process termination.

        Verify process identity before termination to protect
        against accidental termination caused by PID reuse.
        """

        if (
            isinstance(pid, bool)
            or not isinstance(pid, int)
            or pid <= 0
        ):
            raise ValueError("PID must be a positive integer.")

        if (
            isinstance(expected_create_time, bool)
            or not isinstance(expected_create_time, (int, float))
            or not math.isfinite(expected_create_time)
            or expected_create_time <= 0
        ):
            raise ValueError(
                "A valid process creation time is required."
            )

        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ValueError("Timeout must be a positive number.")

        try:
            process = psutil.Process(pid)

            actual_create_time = process.create_time()

            if not math.isclose(
                actual_create_time,
                expected_create_time,
                abs_tol=0.01
            ):
                return {
                    "success": False,
                    "message": "Process identity mismatch."
                }

            process.terminate()

            try:
                process.wait(timeout=timeout)

                return {
                    "success": True,
                    "message": "Process terminated successfully."
                }

            except psutil.TimeoutExpired:
                return {
                    "success": False,
                    "message": (
                        "Process did not terminate within timeout."
                    )
                }

        except psutil.ZombieProcess:
            return {
                "success": False,
                "message": "Process is already a zombie."
            }

        except psutil.NoSuchProcess:
            return {
                "success": False,
                "message": "Process no longer exists."
            }

        except psutil.AccessDenied:
            return {
                "success": False,
                "message": (
                    "Permission denied. Cannot terminate process."
                )
            }

