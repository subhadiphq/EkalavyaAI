"""
EkalavyaAI — Master Notes Cache Service
Shared cache: first student pays API cost, everyone else gets it free.
90% cost reduction strategy.
"""
import json
import logging
from typing import Optional

import redis.asyncio as redis

from config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Master Notes Cache — the cost-saving core of EkalavyaAI.

    When Student A generates notes for "CA Foundation: Partnership Accounts":
    - Agents run → Claude generates → PDF created → saved to master cache
    - Students B, C, D, ... get same notes instantly from cache
    - API cost paid only ONCE per chapter per language
    """

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    def _get_redis(self) -> redis.Redis:
        if not self._redis:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def build_key(
        self, exam: str, subject: str, chapter_id: str, language: str
    ) -> str:
        """Build deterministic cache key."""
        safe_subject = subject.replace(" ", "_").replace("/", "-")[:30]
        return f"{settings.MASTER_CACHE_PREFIX}{exam}:{safe_subject}:{chapter_id}:{language}"

    async def get_master_cache(self, cache_key: str) -> Optional[dict]:
        """
        Check master cache for pre-generated notes.
        Returns cached data or None if not found.
        """
        try:
            r = self._get_redis()
            cached = await r.get(cache_key)

            if cached:
                data = json.loads(cached)
                # Increment view count (async, fire-and-forget)
                await self._increment_views(cache_key)
                logger.debug(f"[Cache] HIT: {cache_key}")
                return data

            logger.debug(f"[Cache] MISS: {cache_key}")
            return None

        except Exception as e:
            logger.warning(f"[Cache] Redis error on GET: {e}")
            return None

    async def set_master_cache(
        self,
        exam: str,
        subject: str,
        chapter_id: str,
        language: str,
        content_json: dict,
        pdf_url: str,
        quality_score: float = 0.8,
    ) -> bool:
        """
        Save generated notes to master cache.
        Also persists to PostgreSQL for durability.
        """
        cache_key = self.build_key(exam, subject, chapter_id, language)

        cache_data = {
            "cache_key": cache_key,
            "chapter_id": chapter_id,
            "exam": exam,
            "subject": subject,
            "language": language,
            "content_json": content_json,
            "pdf_url": pdf_url,
            "quality_score": quality_score,
            "expert_verified": False,
            "view_count": 1,
        }

        try:
            r = self._get_redis()
            await r.setex(
                cache_key,
                settings.NOTES_CACHE_TTL_SECONDS,
                json.dumps(cache_data),
            )
            logger.info(f"[Cache] SET: {cache_key}")

            # Persist to PostgreSQL
            await self._persist_to_db(cache_data)
            return True

        except Exception as e:
            logger.error(f"[Cache] Redis SET error: {e}")
            return False

    async def invalidate(self, cache_key: str):
        """Invalidate a cache entry (e.g., when expert flags issues)."""
        try:
            r = self._get_redis()
            await r.delete(cache_key)
            logger.info(f"[Cache] INVALIDATED: {cache_key}")
        except Exception as e:
            logger.error(f"[Cache] Invalidation error: {e}")

    async def get_cache_stats(self) -> dict:
        """Get cache statistics for admin dashboard."""
        try:
            r = self._get_redis()
            keys = await r.keys(f"{settings.MASTER_CACHE_PREFIX}*")
            return {
                "total_cached_chapters": len(keys),
                "cache_keys": keys[:20],
            }
        except Exception as e:
            logger.error(f"[Cache] Stats error: {e}")
            return {"total_cached_chapters": 0}

    async def _increment_views(self, cache_key: str):
        """Increment view counter in Redis."""
        try:
            r = self._get_redis()
            view_key = f"{cache_key}:views"
            await r.incr(view_key)
        except Exception:
            pass

    async def _persist_to_db(self, cache_data: dict):
        """Persist cache entry to PostgreSQL for durability."""
        try:
            from models.user import MasterNotesCache, Language
            from models.database import get_async_session
            import uuid

            # Skip if chapter_id is a temporary ID (not a real UUID)
            chapter_id_str = cache_data.get("chapter_id", "")
            if not chapter_id_str or chapter_id_str.startswith("temp-"):
                logger.debug("Skipping DB persist for temp chapter_id")
                return

            async with get_async_session() as session:
                entry = MasterNotesCache(
                    cache_key=cache_data["cache_key"],
                    chapter_id=uuid.UUID(chapter_id_str),
                    language=Language(cache_data["language"]),
                    content_json=cache_data["content_json"],
                    pdf_url=cache_data["pdf_url"],
                    quality_score=cache_data["quality_score"],
                )
                session.add(entry)
                await session.commit()
        except Exception as e:
            logger.warning(f"[Cache] DB persist failed (non-critical): {e}")
