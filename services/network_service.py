"""
services/network_service.py
Collects network I/O counters and computes live upload/download speed by
comparing successive samples against a stored previous reading.
"""

import time
from threading import Lock
from typing import Any, Dict

import psutil

from utils.formatters import format_bytes, safe_round
from utils.logger import logger


class NetworkService:
    """Provides network throughput and interface metrics.

    Speed is computed as a delta between the current call and the previous
    call, divided by the elapsed time. Thread-safe via a lock since the Flask
    dev/gunicorn workers may serve concurrent requests.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        counters = psutil.net_io_counters()
        self._last_bytes_sent = counters.bytes_sent
        self._last_bytes_recv = counters.bytes_recv
        self._last_time = time.time()

    def get_network_info(self) -> Dict[str, Any]:
        try:
            with self._lock:
                counters = psutil.net_io_counters()
                now = time.time()
                elapsed = max(now - self._last_time, 1e-6)

                upload_speed_bps = max(
                    (counters.bytes_sent - self._last_bytes_sent) / elapsed, 0
                )
                download_speed_bps = max(
                    (counters.bytes_recv - self._last_bytes_recv) / elapsed, 0
                )

                self._last_bytes_sent = counters.bytes_sent
                self._last_bytes_recv = counters.bytes_recv
                self._last_time = now

            interfaces = []
            stats = psutil.net_if_stats()
            for name, addrs in psutil.net_if_addrs().items():
                ipv4 = next((a.address for a in addrs if a.family.name == "AF_INET"), "N/A")
                is_up = stats[name].isup if name in stats else False
                interfaces.append({"name": name, "ip": ipv4, "is_up": is_up})

            return {
                "upload_speed": f"{format_bytes(upload_speed_bps)}/s",
                "download_speed": f"{format_bytes(download_speed_bps)}/s",
                "upload_speed_bps": safe_round(upload_speed_bps),
                "download_speed_bps": safe_round(download_speed_bps),
                "bytes_sent": format_bytes(counters.bytes_sent),
                "bytes_received": format_bytes(counters.bytes_recv),
                "packets_sent": counters.packets_sent,
                "packets_received": counters.packets_recv,
                "interfaces": interfaces,
            }
        except Exception as exc:
            logger.error("Failed to collect network info: %s", exc)
            return {"error": str(exc)}


network_service = NetworkService()
