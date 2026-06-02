"""
Tests for Celery background-job implementations.

The memory-consolidation test needs a reachable PostgreSQL; it self-skips when
the database is unavailable so the suite still passes in a DB-less environment.
"""
import pytest

import tasks.celery_app as celery_app


async def _db_available() -> bool:
    try:
        from sqlalchemy import text
        from models.database import get_async_session
        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def test_report_email_helper_exists():
    """Weekly-report sender must be a dedicated function (not the welcome email)."""
    assert hasattr(celery_app, "_send_report_email")
    assert hasattr(celery_app, "_send_weekly_reports")


@pytest.mark.asyncio
async def test_memory_consolidation_runs():
    if not await _db_available():
        pytest.skip("PostgreSQL not available")
    updated = await celery_app._compress_all_memories()
    assert isinstance(updated, int)
    assert updated >= 0
