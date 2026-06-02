"""Smoke tests: app boots, health works, all expected routes are registered."""
import pytest

# Routes that must be present in the OpenAPI schema. Includes the STEP-1 spec
# aliases (/chat/stream, /practice/pyq) alongside the canonical paths.
EXPECTED_ROUTES = [
    "/api/v1/auth/signup",
    "/api/v1/auth/login",
    "/api/v1/chat/message",
    "/api/v1/chat/stream",       # alias
    "/api/v1/notes/generate",
    "/api/v1/practice/questions",
    "/api/v1/practice/pyq",      # alias
    "/api/v1/student/onboarding",
    "/api/v1/student/profile",
    "/api/v1/student/referral",
]


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["app"]


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "version" in resp.json()


def test_expected_routes_registered(app_instance):
    paths = set(app_instance.openapi()["paths"].keys())
    missing = [r for r in EXPECTED_ROUTES if r not in paths]
    assert not missing, f"Missing routes in OpenAPI schema: {missing}"


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client):
    """Profile endpoint must reject unauthenticated requests."""
    resp = await client.get("/api/v1/student/profile")
    assert resp.status_code in (401, 403)
