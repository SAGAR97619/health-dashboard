"""
services/process_service.py
Collects the top N processes by CPU usage, with optional name search.
"""

from typing import Any, Dict, List, Optional

import psutil

from config import get_config
from utils.formatters import safe_round
from utils.logger import logger

cfg = get_config()


class ProcessService:
    """Provides process listing and search."""

    def get_top_processes(self, limit: int = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        limit = limit or cfg.TOP_PROCESS_LIMIT
        processes = []
        try:
            for proc in psutil.process_iter(
                ["pid", "name", "username", "cpu_percent", "memory_percent", "status"]
            ):
                try:
                    info = proc.info
                    if search and search.lower() not in (info.get("name") or "").lower():
                        continue
                    processes.append({
                        "pid": info["pid"],
                        "name": info.get("name") or "N/A",
                        "username": info.get("username") or "N/A",
                        "cpu_percent": safe_round(info.get("cpu_percent")),
                        "memory_percent": safe_round(info.get("memory_percent")),
                        "status": info.get("status") or "N/A",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            processes.sort(key=lambda p: p["cpu_percent"], reverse=True)
            return processes[:limit]
        except Exception as exc:
            logger.error("Failed to collect process list: %s", exc)
            return []


process_service = ProcessService()
