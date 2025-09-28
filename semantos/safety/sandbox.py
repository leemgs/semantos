import os, time
from typing import Dict, Any, List

class SandboxSysctl:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                f.write("# SemantOS sandbox sysctl state\n")

    def apply(self, recommendations: List[Dict[str, Any]]) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.path, "a") as f:
            f.write(f"\n# --- APPLY @ {ts} ---\n")
            for rec in recommendations:
                f.write(f"{rec['param']} = {rec['target']}\n")
