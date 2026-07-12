"""
services/disk_service.py
Collects disk usage for the root partition and all mounted partitions.
"""

from typing import Any, Dict, List

import psutil

from config import get_config
from utils.formatters import format_bytes, get_status_level, safe_round
from utils.logger import logger

cfg = get_config()


class DiskService:
    """Provides disk usage metrics."""

    def get_partitions(self) -> List[Dict[str, Any]]:
        partitions = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total": format_bytes(usage.total),
                    "used": format_bytes(usage.used),
                    "free": format_bytes(usage.free),
                    "percent": safe_round(usage.percent),
                })
            except PermissionError:
                continue
        return partitions

    def get_disk_info(self) -> Dict[str, Any]:
        try:
            root_usage = psutil.disk_usage("/")
            partitions = self.get_partitions()

            return {
                "total": format_bytes(root_usage.total),
                "used": format_bytes(root_usage.used),
                "free": format_bytes(root_usage.free),
                "percent": safe_round(root_usage.percent),
                "status": get_status_level(
                    root_usage.percent, cfg.DISK_WARNING_THRESHOLD, cfg.DISK_CRITICAL_THRESHOLD
                ),
                "partitions": partitions,
            }
        except Exception as exc:
            logger.error("Failed to collect disk info: %s", exc)
            return {"error": str(exc)}


disk_service = DiskService()
