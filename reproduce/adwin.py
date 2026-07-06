"""
adwin.py — ADWIN (ADaptive WINdowing) drift detector.

Used by the Knowledge Base update step (Algorithm 1, line 14) and the Safety
Runtime to detect workload/score drift and trigger sliding-window
recalibration.  Lightweight, dependency-free implementation of the standard
ADWIN test: maintain a window of recent values and, whenever a split of the
window into two sub-windows shows means that differ by more than a Hoeffding
bound, drop the older sub-window and declare drift.
"""

from __future__ import annotations
import math
from collections import deque


class ADWIN:
    def __init__(self, delta: float = 0.002, max_buckets: int = 500):
        self.delta = delta
        self.max_buckets = max_buckets
        self.window: deque[float] = deque(maxlen=max_buckets)
        self.total = 0.0
        self.drift_detected = False

    @property
    def width(self) -> int:
        return len(self.window)

    @property
    def mean(self) -> float:
        return self.total / self.width if self.width else 0.0

    def _hoeffding_cut(self, n0: int, n1: int, var: float) -> float:
        if n0 == 0 or n1 == 0:
            return math.inf
        m = 1.0 / n0 + 1.0 / n1                    # harmonic size
        dd = math.log(2.0 * math.log(max(2, self.width)) / self.delta)
        return math.sqrt(2.0 * m * var * dd) + 2.0 / 3.0 * m * dd

    def update(self, value: float) -> bool:
        """Add a value; return True if drift was detected on this step.

        O(n) per call: a single prefix-sum pass lets every candidate split be
        scored in O(1), instead of recomputing sub-window sums each time.
        """
        self.window.append(value)
        self.total += value
        self.drift_detected = False
        n = self.width
        if n < 8:
            return False
        vals = list(self.window)
        overall_mean = self.total / n
        var = 0.0
        for v in vals:
            d = v - overall_mean
            var += d * d
        var /= n
        # prefix[i] = sum(vals[:i]); left sum = prefix[i], right sum = total-prefix[i]
        prefix = 0.0
        total = self.total
        for i in range(1, n):
            prefix += vals[i - 1]
            n0 = i
            n1 = n - i
            m0 = prefix / n0
            m1 = (total - prefix) / n1
            if abs(m0 - m1) > self._hoeffding_cut(n0, n1, var):
                # drift: forget the older sub-window
                for _ in range(n0):
                    self.total -= self.window.popleft()
                self.drift_detected = True
                return True
        return False
