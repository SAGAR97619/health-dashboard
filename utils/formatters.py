"""
utils/formatters.py
Shared helper functions for formatting raw metric values into human-readable
strings (bytes -> KB/MB/GB, seconds -> uptime string, etc.).
"""

from datetime import datetime, timedelta
from typing import Union


def format_bytes(num_bytes: Union[int, float]) -> str:
    """Convert a byte count into a human-readable string (e.g. '1.23 GB')."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024.0:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} EB"


def format_uptime(boot_timestamp: float) -> str:
    """Return a human-readable uptime string given a boot timestamp (epoch seconds)."""
    delta = datetime.now() - datetime.fromtimestamp(boot_timestamp)
    return format_timedelta(delta)


def format_timedelta(delta: timedelta) -> str:
    """Format a timedelta as 'Xd Xh Xm Xs'."""
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def get_status_level(value: float, warning: float, critical: float) -> str:
    """Classify a percentage value into 'critical', 'warning', or 'healthy'."""
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "healthy"


def safe_round(value: Union[int, float, None], digits: int = 2) -> float:
    """Round a numeric value, returning 0.0 for None/invalid input."""
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0
