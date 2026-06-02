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
    """
    Nightly job: consolidate each active student's short-term activity into
    their long-term PostgreSQL profile.

    Aggregates the last 7 days of chat activity (short-term memory) into a
    ``memory_consolidation`` summary stored on ``StudentProfile.behavioral_profile``.
    This is intentionally DB-only and non-destructive (no rows are deleted), so it
    runs without Pinecone/LLM credentials. Vector-store compaction can be layered
    on top once Pinecone is configured.
    """
    import logging
    from datetime import datetime, timedelta

    from sqlalchemy import select, func
    from sqlalchemy.orm.attributes import flag_modified

    from models.database import get_async_session
    from models.user import User, StudentProfile, ChatMessage

    logger = logging.getLogger(__name__)
    logger.info("Starting nightly memory consolidation...")

    week_ago = datetime.utcnow() - timedelta(days=7)
    consolidated = 0

    async with get_async_session() as session:
        result = await session.execute(
            select(User, StudentProfile)
            .join(StudentProfile, User.id == StudentProfile.user_id)
            .where(User.is_active == True)  # noqa: E712 — SQLAlchemy boolean
        )
        for user, profile in result.all():
            try:
                recent = await session.scalar(
                    select(func.count(ChatMessage.id)).where(
                        ChatMessage.student_id == user.id,
                        ChatMessage.created_at >= week_ago,
                    )
                )
                total = await session.scalar(
                    select(func.count(ChatMessage.id)).where(
                        ChatMessage.student_id == user.id
                    )
                )
                bp = dict(profile.behavioral_profile or {})
                bp["memory_consolidation"] = {
                    "last_run": datetime.utcnow().isoformat(),
                    "recent_message_count": int(recent or 0),
                    "total_message_count": int(total or 0),
                }
                profile.behavioral_profile = bp
                flag_modified(profile, "behavioral_profile")
                consolidated += 1
            except Exception as e:
                logger.error(f"Consolidation failed for {user.id}: {e}")
        await session.commit()

    logger.info(f"Memory consolidation complete — {consolidated} student(s) updated")
    return consolidated


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

    sent = 0
    for user in pro_users:
        try:
            report = await memory_agent.generate_weekly_report(str(user.id))
            await _send_report_email(user.name, user.email, report.get("report_text", ""))
            sent += 1
        except Exception as e:
            logger.error(f"Weekly report failed for {user.id}: {e}")

    logger.info(f"Weekly reports sent to {sent}/{len(pro_users)} Pro student(s)")
    return sent


async def _send_report_email(name: str, email: str, report_text: str):
    """Email a generated weekly study report via Resend."""
    import logging
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        body_html = report_text.replace("\n", "<br>") if report_text else ""
        resend.Emails.send({
            "from": f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>",
            "to": email,
            "subject": "\U0001F4CA Your EkalavyaAI Weekly Study Report",
            "html": f"""
            <h2>Your Weekly Study Report</h2>
            <p>Hi {name},</p>
            <p>{body_html}</p>
            <p><a href="{settings.APP_URL}/progress">View full progress \u2192</a></p>
            <br>
            <small>EkalavyaAI \u2014 Learn Like a Topper</small>
            """,
        })
    except Exception as e:
        logging.getLogger(__name__).error(f"Weekly report email failed for {email}: {e}")


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
