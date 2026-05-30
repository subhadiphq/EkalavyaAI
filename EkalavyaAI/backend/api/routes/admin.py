"""
EkalavyaAI — Admin API Routes
Cache management, PDF ingestion trigger, platform analytics, expert review.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api.dependencies import get_current_user, require_admin
from services.cache_service import CacheService

logger = logging.getLogger(__name__)
router = APIRouter()
cache_service = CacheService()


class IngestRequest(BaseModel):
    directory: str
    exam: str
    subject: str


class VerifyNotesRequest(BaseModel):
    cache_key: str
    verified: bool
    expert_notes: Optional[str] = None


@router.get("/cache")
async def get_cache_stats(_=Depends(require_admin)):
    """Get master notes cache statistics."""
    stats = await cache_service.get_cache_stats()
    return stats


@router.delete("/cache/{cache_key}")
async def invalidate_cache(cache_key: str, _=Depends(require_admin)):
    """Invalidate a specific cache entry."""
    await cache_service.invalidate(cache_key)
    return {"message": f"Cache invalidated: {cache_key}"}


@router.post("/ingest")
async def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    _=Depends(require_admin),
):
    """Trigger PDF ingestion pipeline (runs in background)."""
    from rag.ingestion import PDFIngestionPipeline

    async def run_ingestion():
        pipeline = PDFIngestionPipeline()
        await pipeline.ingest_directory(request.directory, request.exam, request.subject)
        logger.info(f"Ingestion complete: {request.directory}")

    background_tasks.add_task(run_ingestion)
    return {
        "message": f"Ingestion started for {request.exam}/{request.subject}",
        "directory": request.directory,
    }


@router.get("/analytics")
async def get_platform_analytics(_=Depends(require_admin)):
    """Platform-level analytics dashboard data."""
    from sqlalchemy import select, func
    from models.user import User, Note, QuestionAttempt, Subscription
    from models.database import get_async_session
    from datetime import datetime, timedelta

    try:
        async with get_async_session() as session:
            # Total users
            total_users = await session.scalar(select(func.count(User.id)))

            # Active last 7 days
            cutoff = datetime.utcnow() - timedelta(days=7)
            active_users = await session.scalar(
                select(func.count(User.id)).where(User.last_login >= cutoff)
            )

            # Plan breakdown
            plan_counts = {}
            for plan in ["FREE", "BASIC", "PRO", "INSTITUTE"]:
                count = await session.scalar(
                    select(func.count(User.id)).where(User.plan == plan)
                )
                plan_counts[plan] = count or 0

            # Notes generated
            total_notes = await session.scalar(select(func.count(Note.id)))

            # PYQ attempts
            total_attempts = await session.scalar(select(func.count(QuestionAttempt.id)))

            # Paid subscribers
            paid_subs = await session.scalar(
                select(func.count(Subscription.id)).where(
                    Subscription.status == "ACTIVE"
                )
            )

            return {
                "users": {
                    "total": total_users,
                    "active_7d": active_users,
                    "by_plan": plan_counts,
                    "paid": paid_subs,
                },
                "content": {
                    "notes_generated": total_notes,
                    "pyq_attempts": total_attempts,
                },
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-notes")
async def verify_notes(
    request: VerifyNotesRequest,
    _=Depends(require_admin),
):
    """Expert CA/JEE/NEET teacher verifies notes quality."""
    from sqlalchemy import select
    from models.user import MasterNotesCache
    from models.database import get_async_session

    async with get_async_session() as session:
        result = await session.execute(
            select(MasterNotesCache).where(
                MasterNotesCache.cache_key == request.cache_key
            )
        )
        cache_entry = result.scalar_one_or_none()
        if not cache_entry:
            raise HTTPException(status_code=404, detail="Cache entry not found")

        cache_entry.expert_verified = request.verified
        await session.commit()

        if not request.verified:
            # Invalidate and regenerate
            await cache_service.invalidate(request.cache_key)

        return {
            "message": f"Notes {'verified' if request.verified else 'rejected'}",
            "cache_key": request.cache_key,
        }
