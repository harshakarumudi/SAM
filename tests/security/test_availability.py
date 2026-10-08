

def test_health_check_endpoint(client):
    """Verifies health check readiness for Kubernetes probes"""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] == "connected"


def test_malformed_json_availability_resilience(client):
    """
    Availability resilience:
    Sending corrupted or malformed payloads must be safely handled without crashing the server.
    """
    resp = client.post(
        "/api/sensors/reading",
        content="NOT_VALID_JSON{{{}}}",
        headers={"Content-Type": "application/json"}
    )
    # Must fail gracefully with 422 or 400, never 500 or crashing
    assert resp.status_code in [400, 422]


def test_rate_limiting_protection(client):
    """
    DEMO 9: Availability protection via rate limiting.
    Excessive rapid requests trigger rate limiting (HTTP 429).
    """
    # The login endpoint is limited to 10/minute
    triggered_limit = False
    for _ in range(15):
        resp = client.post(
            "/api/auth/login",
            json={"username": "bad_user", "password": "WrongPassword123!"}
        )
        if resp.status_code == 429:
            triggered_limit = True
            break

    assert triggered_limit is True
