"""
services/health_service.py
Aggregates individual metrics into an overall dashboard summary, and
provides battery status where available.
"""

from typing import Any, Dict

import psutil

from services.cpu_service import cpu_service
from services.disk_service import disk_service
from services.docker_service import docker_service
from services.memory_service import memory_service
from services.system_service import system_service
from utils.formatters import safe_round
from utils.logger import logger


class HealthService:
    """Aggregates metrics for the summary endpoint and overall health badge."""

    @staticmethod
    def get_battery_info() -> Dict[str, Any]:
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {"available": False}
            return {
                "available": True,
                "percent": safe_round(battery.percent),
                "plugged_in": battery.power_plugged,
                "secs_left": battery.secsleft if isinstance(battery.secsleft, int) else None,
            }
        except AttributeError:
            return {"available": False}

    def get_summary(self) -> Dict[str, Any]:
        try:
            cpu = cpu_service.get_cpu_info()
            memory = memory_service.get_memory_info()
            disk = disk_service.get_disk_info()
            docker_info = docker_service.get_docker_info()
            system = system_service.get_system_info()

            statuses = [cpu.get("status"), memory.get("status"), disk.get("status")]
            if "critical" in statuses:
                overall_status = "critical"
            elif "warning" in statuses:
                overall_status = "warning"
            else:
                overall_status = "healthy"

            return {
                "overall_status": overall_status,
                "hostname": system.get("hostname"),
                "uptime": system.get("uptime"),
                "cpu_percent": cpu.get("usage_percent"),
                "cpu_status": cpu.get("status"),
                "memory_percent": memory.get("percent"),
                "memory_status": memory.get("status"),
                "disk_percent": disk.get("percent"),
                "disk_status": disk.get("status"),
                "docker_running_containers": docker_info.get("running_containers", 0),
                "docker_available": docker_info.get("available", False),
                "battery": self.get_battery_info(),
                "timestamp": system.get("timestamp"),
            }
        except Exception as exc:
            logger.error("Failed to build summary: %s", exc)
            return {"error": str(exc)}


health_service = HealthService()
