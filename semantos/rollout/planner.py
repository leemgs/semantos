from typing import Dict, Any, List

def staggered_batches(recommendations: List[Dict[str, Any]], batch_size: int = 3) -> List[List[Dict[str, Any]]]:
    return [recommendations[i:i+batch_size] for i in range(0, len(recommendations), batch_size)]
