"""
SemantOS (Reproduction Kit)
A lightweight, runnable reference that mirrors the paper's pipeline:
Telemetry -> KB -> Reasoning -> Safety -> Rollout -> Monitoring -> Evaluation.

This package avoids privileged operations. It *never* touches real /proc or /sys.
All config "applications" are written to a sandbox file for inspection.
"""
__version__ = "0.1.0"
