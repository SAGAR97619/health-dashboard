"""
tests/test_services.py
Unit tests for individual service-layer classes, independent of Flask routes.
"""

from services.cpu_service import cpu_service
from services.disk_service import disk_service
from services.health_service import health_service
from services.memory_service import memory_service
from services.process_service import process_service
from services.system_service import system_service
from utils.formatters import format_bytes, get_status_level, safe_round


def test_format_bytes_human_readable():
    assert format_bytes(0) == "0.00 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1024 * 1024) == "1.00 MB"


def test_get_status_level_thresholds():
    assert get_status_level(50, warning=75, critical=90) == "healthy"
    assert get_status_level(80, warning=75, critical=90) == "warning"
    assert get_status_level(95, warning=75, critical=90) == "critical"


def test_safe_round_handles_invalid_input():
    assert safe_round(None) == 0.0
    assert safe_round("not-a-number") == 0.0
    assert safe_round(3.14159, 2) == 3.14


def test_cpu_service_returns_valid_range():
    info = cpu_service.get_cpu_info()
    assert 0 <= info["usage_percent"] <= 100
    assert info["core_count_logical"] >= 1


def test_memory_service_percent_in_range():
    info = memory_service.get_memory_info()
    assert 0 <= info["percent"] <= 100


def test_disk_service_percent_in_range():
    info = disk_service.get_disk_info()
    assert 0 <= info["percent"] <= 100


def test_system_service_hostname_not_empty():
    info = system_service.get_system_info()
    assert info["hostname"]


def test_process_service_respects_limit():
    processes = process_service.get_top_processes(limit=5)
    assert len(processes) <= 5


def test_health_service_overall_status_valid():
    summary = health_service.get_summary()
    assert summary["overall_status"] in {"healthy", "warning", "critical"}
