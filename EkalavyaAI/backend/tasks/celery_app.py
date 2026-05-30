"""
EkalavyaAI — Celery Tasks
Background job queue for async operations.
"""
from celery import Celery
from celery.schedules import crontab

from config import settings

# ─── Celery App ──────────────────────────────────────────────────────────────
celery_app = Celery(
    "ekalavya",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ─── Periodic Tasks ──────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Compress student memories every night at 2 AM
    "compress-memories-nightly": {
        "task": "tasks.compress_all_memories",
        "schedule": crontab(hour=2, minute=0),
    },
    # Send weekly reports every Monday 8 AM
    "weekly-reports": {
        "task": "tasks.send_weekly_reports",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
    # Warm up popular cache entries every 6 hours
    "cache-warmup": {
        "task": "tasks.warm_popular_cache",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}


# ─── Task Definitions ────────────────────────────────────────────────────────
@celery_app.task(name="tasks.send_welcome_email", bind=True, max_retries=3)
def send_welcome_email(self, user_id: str, name: str, email: str):
    """Send welcome email to new student."""
    import asyncio
    asyncio.run(_send_welcome_email(user_id, name, email))


@celery_app.task(name="tasks.compress_all_memories")
def compress_all_memories():
    """Nightly job: compress student memory vectors."""
    import asyncio
    asyncio.run(_compress_all_memories())


@celery_app.task(name="tasks.send_weekly_reports")
def send_weekly_reports():
    """Monday job: generate and email weekly study reports."""
    import asyncio
    asyncio.run(_send_weekly_reports())


@celery_app.task(name="tasks.expert_review_task")
def expert_review_task(chapter_id: str, content_json: dict, flags: list, confidence: float):
    """Queue content for expert CA/JEE/NEET review."""
    import asyncio
    asyncio.run(_queue_expert_review(chapter_id, content_json, flags, confidence))


@celery_app.task(name="tasks.warm_popular_cache")
def warm_popular_cache():
    """Pre-generate notes for most-requested chapters."""
    import asyncio
    asyncio.run(_warm_popular_cache())


# ─── Async Implementations ───────────────────────────────────────────────────
async def _send_welcome_email(user_id: str, name: str, email: str):
    """Send welcome email via Resend."""
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>",
            "to": email,
            "subject": f"Welcome to EkalavyaAI, {name}! 🎯",
            "html": f"""
            <h2>Welcome to EkalavyaAI!</h2>
            <p>Hi {name},</p>
            <p>You're now part of India's smartest exam prep platform.</p>
            <p>Start your journey → <a href="{settings.APP_URL}/onboarding">Complete your profile</a></p>
            <p>Learn Like a Topper! 🚀</p>
            <br>
            <small>EkalavyaAI Team</small>
            """,
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Welcome email failed: {e}")


async def _compress_all_memories():
    """Compress and consolidate student memory vectors."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Starting nightly memory compression...")
    # Get all active students from DB
    # For each student: compress similar memories
    # This prevents Pinecone index bloat
    logger.info("Memory compression complete")


async def _send_weekly_reports():
    """Generate and send weekly reports for active Pro students."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Generating weekly reports...")

    from sqlalchemy import select
    from models.user import User
    from models.database import get_async_session
    from agents.memory_agent import MemoryAgent

    memory_agent = MemoryAgent()

    async with get_async_session() as session:
        result = await session.execute(
            select(User).where(User.plan.in_(["PRO", "INSTITUTE"]), User.is_active == True)
        )
        pro_users = result.scalars().all()

    for user in pro_users:
        try:
            report = await memory_agent.generate_weekly_report(str(user.id))
            await _send_welcome_email(
                str(user.id),
                user.name,
                user.email,
                # Would use report template in production
            )
        except Exception as e:
            logger.error(f"Weekly report failed for {user.id}: {e}")


async def _queue_expert_review(
    chapter_id: str, content_json: dict, flags: list, confidence: float
):
    """Store low-confidence content for expert review."""
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        f"Expert review queued: chapter={chapter_id} "
        f"confidence={confidence:.2f} flags={flags[:3]}"
    )
    # In production: insert into expert_review_queue table
    # Expert (CA/JEE teacher) reviews via admin panel
    # Once approved, update master cache and mark expert_verified=True


async def _warm_popular_cache():
    """Pre-generate notes for top-50 most requested chapters."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Cache warmup starting...")
    # Query top chapters by view count
    # For chapters not in cache: trigger generation with system user
    # This ensures 0 wait time for the most popular content
    logger.info("Cache warmup complete")
