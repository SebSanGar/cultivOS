"""Basic smoke tests for cultivOS."""


def test_health_endpoint(client):
    """Health check returns 200."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
