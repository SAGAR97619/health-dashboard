"""
tests/test_views.py
Tests for the dashboard page and health-check endpoint.
"""


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"DevOps" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
