"""
services/memory_service.py
Collects virtual memory (RAM) and swap memory metrics.
"""

from typing import Any, Dict

import psutil

from config import get_config
from utils.formatters import format_bytes, get_status_level, safe_round
from utils.logger import logger

cfg = get_config()


class MemoryService:
    """Provides RAM and swap memory metrics."""

    def get_memory_info(self) -> Dict[str, Any]:
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "total": format_bytes(vm.total),
                "used": format_bytes(vm.used),
                "available": format_bytes(vm.available),
                "free": format_bytes(vm.free),
                "percent": safe_round(vm.percent),
                "total_bytes": vm.total,
                "used_bytes": vm.used,
                "status": get_status_level(
                    vm.percent, cfg.RAM_WARNING_THRESHOLD, cfg.RAM_CRITICAL_THRESHOLD
                ),
                "swap": {
                    "total": format_bytes(swap.total),
                    "used": format_bytes(swap.used),
                    "free": format_bytes(swap.free),
                    "percent": safe_round(swap.percent),
                },
            }
        except Exception as exc:
            logger.error("Failed to collect memory info: %s", exc)
            return {"error": str(exc)}


memory_service = MemoryService()
