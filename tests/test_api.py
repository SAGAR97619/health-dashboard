"""
tests/test_api.py
Tests for all REST API endpoints exposed under /api.
"""

import pytest


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/system",
        "/api/cpu",
        "/api/memory",
        "/api/disk",
        "/api/network",
        "/api/docker",
        "/api/processes",
        "/api/load",
        "/api/summary",
    ],
)
def test_endpoint_returns_json_200(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    assert isinstance(response.get_json(), dict)


def test_system_info_has_expected_keys(client):
    data = client.get("/api/system").get_json()
    for key in ("hostname", "os", "uptime", "python_version"):
        assert key in data


def test_cpu_info_has_expected_keys(client):
    data = client.get("/api/cpu").get_json()
    for key in ("usage_percent", "per_core", "core_count_logical", "status"):
        assert key in data


def test_memory_info_has_expected_keys(client):
    data = client.get("/api/memory").get_json()
    for key in ("total", "used", "percent", "status", "swap"):
        assert key in data


def test_disk_info_has_expected_keys(client):
    data = client.get("/api/disk").get_json()
    for key in ("total", "used", "free", "percent", "partitions"):
        assert key in data


def test_processes_endpoint_returns_list(client):
    data = client.get("/api/processes").get_json()
    assert "processes" in data
    assert isinstance(data["processes"], list)
    assert len(data["processes"]) <= 10


def test_processes_search_filters_results(client):
    data = client.get("/api/processes?search=zzz_no_such_process_zzz").get_json()
    assert data["processes"] == []


def test_summary_has_overall_status(client):
    data = client.get("/api/summary").get_json()
    assert data.get("overall_status") in {"healthy", "warning", "critical"}


def test_unknown_api_route_returns_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404


def test_pdf_report_downloads(client):
    response = client.get("/api/report/pdf")
    assert response.status_code == 200
    assert response.content_type == "application/pdf"
