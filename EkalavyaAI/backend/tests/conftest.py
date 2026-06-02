"""
Shared pytest fixtures for EkalavyaAI backend smoke tests.

These tests are hermetic: they set placeholder credentials for the two required
settings (OPENROUTER_API_KEY, GROQ_API_KEY) *before* importing the app so the
suite runs with no real keys, no network, and (for most tests) no database.
"""
import os
import sys

# Required settings must exist before `config`/`main` import. Set placeholders.
os.environ.setdefault("OPENROUTER_API_KEY", "test_openrouter_key")
os.environ.setdefault("GROQ_API_KEY", "test_groq_key")
os.environ.setdefault("ENVIRONMENT", "test")

# Ensure the backend root is importable when pytest is invoked from elsewhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    """Async HTTP client bound to the ASGI app (lifespan not triggered)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def app_instance():
    return app
