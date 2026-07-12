"""
services/cpu_service.py
Collects CPU usage, per-core usage, frequency and core count.
"""

from typing import Any, Dict, List

import psutil

from config import get_config
from utils.formatters import get_status_level, safe_round
from utils.logger import logger

cfg = get_config()


class CpuService:
    """Provides CPU-related metrics."""

    def get_cpu_info(self) -> Dict[str, Any]:
        try:
            usage_percent = psutil.cpu_percent(interval=0.3)
            per_core: List[float] = psutil.cpu_percent(interval=0.1, percpu=True)
            freq = psutil.cpu_freq()

            return {
                "usage_percent": safe_round(usage_percent),
                "per_core": [safe_round(c) for c in per_core],
                "core_count_logical": psutil.cpu_count(logical=True),
                "core_count_physical": psutil.cpu_count(logical=False),
                "frequency_current_mhz": safe_round(freq.current) if freq else None,
                "frequency_min_mhz": safe_round(freq.min) if freq else None,
                "frequency_max_mhz": safe_round(freq.max) if freq else None,
                "status": get_status_level(
                    usage_percent, cfg.CPU_WARNING_THRESHOLD, cfg.CPU_CRITICAL_THRESHOLD
                ),
            }
        except Exception as exc:
            logger.error("Failed to collect CPU info: %s", exc)
            return {"error": str(exc)}

    def get_system_load(self) -> Dict[str, Any]:
        """Return system load averages (1, 5, 15 min) where supported."""
        try:
            load1, load5, load15 = psutil.getloadavg()
            return {
                "load_1min": safe_round(load1),
                "load_5min": safe_round(load5),
                "load_15min": safe_round(load15),
            }
        except (AttributeError, OSError):
            # getloadavg() is not available on some platforms (e.g. Windows)
            return {"load_1min": None, "load_5min": None, "load_15min": None}

    def get_cpu_temperature(self) -> Dict[str, Any]:
        """Return CPU temperature if the platform exposes sensors."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return {"available": False, "temperature_c": None}
            for entries in temps.values():
                if entries:
                    return {"available": True, "temperature_c": safe_round(entries[0].current)}
            return {"available": False, "temperature_c": None}
        except AttributeError:
            return {"available": False, "temperature_c": None}


cpu_service = CpuService()
