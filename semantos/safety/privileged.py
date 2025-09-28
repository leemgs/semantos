import os, json
from typing import List, Dict, Any, Tuple

# Supported keys -> /proc/sys paths (dot->slash mapping covers most, but we keep an explicit whitelist)
WHITELIST = {
    "vm.dirty_background_ratio": "/proc/sys/vm/dirty_background_ratio",
    "vm.dirty_ratio": "/proc/sys/vm/dirty_ratio",
    "vm.swappiness": "/proc/sys/vm/swappiness",
    "net.core.somaxconn": "/proc/sys/net/core/somaxconn",
    "net.core.netdev_max_backlog": "/proc/sys/net/core/netdev_max_backlog",
    "kernel.sched_latency_ns": "/proc/sys/kernel/sched_latency_ns",
    "kernel.sched_min_granularity_ns": "/proc/sys/kernel/sched_min_granularity_ns",
    "kernel.numa_balancing": "/proc/sys/kernel/numa_balancing",
}

class SysctlApplier:
    """
    Applies sysctl-like settings directly to /proc/sys/* files.
    - **Dry-run by default** (set apply=False)
    - Requires root when apply=True
    - Creates a JSON backup for rollback
    """
    def __init__(self, backup_path: str = "experiments/backup/sysctl_backup.json"):
        self.backup_path = backup_path
        os.makedirs(os.path.dirname(self.backup_path), exist_ok=True)

    def _read_current(self, path: str) -> str:
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "<missing>"
        except PermissionError as e:
            return f"<perm:{e}>"

    def _write_value(self, path: str, value: str) -> None:
        with open(path, "w") as f:
            f.write(str(value))

    def _collect_backup(self, recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        backup = {}
        for rec in recs:
            key = rec["param"]
            path = WHITELIST.get(key)
            if not path:
                continue
            backup[key] = {"path": path, "value": self._read_current(path)}
        return backup

    def apply(self, recommendations: List[Dict[str, Any]], apply: bool = False) -> List[Tuple[str, str, str]]:
        """
        Returns a list of (key, old, new). If apply=False, only simulates.
        """
        if not recommendations:
            return []

        # Only allow changes to whitelisted keys
        recs = [r for r in recommendations if r.get("param") in WHITELIST]
        if not recs:
            return []

        # Prepare backup
        backup = self._collect_backup(recs)
        with open(self.backup_path, "w") as f:
            json.dump(backup, f, indent=2)

        results = []
        for rec in recs:
            key, val = rec["param"], rec["target"]
            path = WHITELIST[key]
            old = self._read_current(path)
            results.append((key, old, str(val)))
            if apply:
                # Permission check
                if os.geteuid() != 0:
                    raise PermissionError("Must be root to write /proc/sys values (re-run with sudo).")
                # Write
                self._write_value(path, str(val))
        return results

    def rollback(self) -> List[Tuple[str, str, str]]:
        """
        Restores values from the JSON backup file.
        Returns a list of (key, from_backup, after_write).
        """
        if not os.path.exists(self.backup_path):
            raise FileNotFoundError(f"No backup file at {self.backup_path}")
        with open(self.backup_path) as f:
            backup = json.load(f)

        results = []
        for key, meta in backup.items():
            path = meta["path"]
            prev = meta["value"]
            # Write back (requires root)
            if os.geteuid() != 0:
                raise PermissionError("Must be root to rollback /proc/sys values (re-run with sudo).")
            self._write_value(path, str(prev))
            after = self._read_current(path)
            results.append((key, str(prev), after))
        return results
