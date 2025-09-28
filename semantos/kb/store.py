import json, os
from typing import Any, Dict, List

class KBStore:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(self.path, exist_ok=True)

    def put_experience(self, name: str, record: Dict[str, Any]) -> None:
        with open(os.path.join(self.path, f"{name}.json"), "w") as f:
            json.dump(record, f, indent=2)

    def get_all(self) -> List[Dict[str, Any]]:
        out = []
        for fn in os.listdir(self.path):
            if fn.endswith(".json"):
                with open(os.path.join(self.path, fn)) as f:
                    out.append(json.load(f))
        return out
