"""
services/system_service.py
Collects general system/host information: hostname, IPs, OS, uptime, users, etc.
"""

import getpass
import platform
import socket
import sys
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Dict, List

import psutil

from utils.formatters import format_uptime
from utils.logger import logger


class SystemService:
    """Provides host-level system information."""

    @staticmethod
    def get_local_ip() -> str:
        """Best-effort local IP discovery without needing external connectivity."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.5)
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except socket.gaierror:
                return "N/A"

    @staticmethod
    def get_public_ip() -> str:
        """Best-effort public IP discovery via an external service (fails gracefully)."""
        try:
            with urllib.request.urlopen("https://api.ipify.org", timeout=1.5) as resp:
                return resp.read().decode("utf-8").strip()
        except (urllib.error.URLError, OSError, TimeoutError):
            return "Unavailable"

    @staticmethod
    def get_logged_in_users() -> List[Dict[str, Any]]:
        """Return a list of currently logged-in users."""
        users = []
        try:
            for u in psutil.users():
                users.append({
                    "name": u.name,
                    "terminal": u.terminal or "N/A",
                    "host": u.host or "local",
                    "started": datetime.fromtimestamp(u.started).strftime("%Y-%m-%d %H:%M:%S"),
                })
        except Exception as exc:  # pragma: no cover - platform dependent
            logger.warning("Could not read logged-in users: %s", exc)
        return users

    def get_system_info(self) -> Dict[str, Any]:
        """Aggregate all system/host information into a single dict."""
        try:
            boot_timestamp = psutil.boot_time()
            info = {
                "hostname": socket.gethostname(),
                "local_ip": self.get_local_ip(),
                "public_ip": self.get_public_ip(),
                "os": f"{platform.system()} {platform.release()}",
                "os_version": platform.version(),
                "kernel_version": platform.release(),
                "architecture": platform.machine(),
                "processor": platform.processor() or "N/A",
                "logged_in_user": getpass.getuser(),
                "logged_in_users": self.get_logged_in_users(),
                "uptime": format_uptime(boot_timestamp),
                "boot_time": datetime.fromtimestamp(boot_timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "python_version": sys.version.split()[0],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            return info
        except Exception as exc:
            logger.error("Failed to collect system info: %s", exc)
            return {"error": str(exc)}


system_service = SystemService()
