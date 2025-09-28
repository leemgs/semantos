from typing import Dict, Any, List, Callable

def apply_batches(batches: List[List[Dict[str, Any]]], apply_fn: Callable[[List[Dict[str, Any]]], None]) -> None:
    for b in batches:
        apply_fn(b)
