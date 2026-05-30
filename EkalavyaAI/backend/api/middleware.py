"""
EkalavyaAI — API Middleware
Rate limiting per plan, structured request logging.
"""
import logging
import time
import uuid
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings

logger = logging.getLogger(__name__)

# In-memory rate limit counters (use Redis in production)
_rate_counters: dict = defaultdict(lambda: {"count": 0, "reset_at": 0})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-plan rate limiting."""

    PLAN_LIMITS = {
        "FREE": settings.RATE_LIMIT_FREE_PER_MINUTE,
        "BASIC": settings.RATE_LIMIT_BASIC_PER_MINUTE,
        "PRO": settings.RATE_LIMIT_PRO_PER_MINUTE,
        "INSTITUTE": 200,
    }

    EXEMPT_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Extract client identifier
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        now = time.time()

        counter = _rate_counters[key]
        if now > counter["reset_at"]:
            counter["count"] = 0
            counter["reset_at"] = now + 60

        counter["count"] += 1
        limit = self.PLAN_LIMITS.get("FREE")  # Default; override with auth in production

        if counter["count"] > limit:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests. Limit: {limit}/minute.",
                    "retry_after": int(counter["reset_at"] - now),
                },
                headers={"Retry-After": str(int(counter["reset_at"] - now))},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - counter["count"]))
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging."""

    async def dispatch(self, request: Request, call_next):
        req_id = str(uuid.uuid4())[:8]
        start = time.time()

        logger.info(
            f"[{req_id}] → {request.method} {request.url.path} "
            f"| IP: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f"[{req_id}] ✗ Unhandled error: {exc}", exc_info=True)
            raise

        elapsed_ms = int((time.time() - start) * 1000)
        logger.info(
            f"[{req_id}] ← {response.status_code} | {elapsed_ms}ms"
        )
        response.headers["X-Request-ID"] = req_id
        return response
