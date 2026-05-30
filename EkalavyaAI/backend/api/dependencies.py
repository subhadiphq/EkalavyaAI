"""
EkalavyaAI — FastAPI Dependencies
JWT authentication, plan limit checking with Redis counters, DB session injection.
"""
import logging
from datetime import datetime
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings, SUBSCRIPTION_PLANS

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Decode JWT and return current user from DB."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please sign in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    from sqlalchemy import select
    from models.user import User
    from models.database import get_async_session

    async with get_async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or deactivated",
            )
        return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
):
    """Optional authentication — returns None if no token provided."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def check_plan_limit(user, feature: str) -> None:
    """
    Check plan limits with Redis counters.
    Raises HTTP 403 if feature not available or limit exceeded.
    """
    plan = getattr(user, "plan", "FREE")
    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["FREE"])

    feature_limits = {
        "chapter_explanations": ("chapter_explanations_per_month", "monthly"),
        "notes_download":       ("notes_download_per_month",       "monthly"),
        "pyq_questions":        ("pyq_questions",                  "daily"),
        "general_chat":         ("general_chat_per_day",           "daily"),
    }

    mapping = feature_limits.get(feature)
    if not mapping:
        return  # Unknown feature — allow

    limit_key, period = mapping
    limit = plan_config.get(limit_key, 0)

    if limit == -1:
        return  # Unlimited

    if limit == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "FEATURE_NOT_AVAILABLE",
                "message": "This feature is not available on your current plan.",
                "current_plan": plan,
                "upgrade_url": f"{settings.APP_URL}/pricing",
            },
        )

    # Redis usage counting
    try:
        import redis.asyncio as redis_client

        r = redis_client.from_url(settings.REDIS_URL, decode_responses=True)
        student_id = str(user.id)

        if period == "daily":
            today = datetime.utcnow().strftime("%Y%m%d")
            redis_key = f"usage:{student_id}:{feature}:{today}"
            ttl = 86400  # 24 hours
        else:  # monthly
            month = datetime.utcnow().strftime("%Y%m")
            redis_key = f"usage:{student_id}:{feature}:{month}"
            ttl = 86400 * 31  # ~31 days

        current = await r.get(redis_key)
        current_count = int(current) if current else 0

        if current_count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "LIMIT_EXCEEDED",
                    "message": f"You've reached your {period} limit of {limit} for {feature}.",
                    "limit": limit,
                    "used": current_count,
                    "period": period,
                    "upgrade_url": f"{settings.APP_URL}/pricing",
                },
            )

        # Increment counter
        pipe = r.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, ttl)
        await pipe.execute()

    except HTTPException:
        raise
    except Exception as e:
        # Redis unavailable — fail open (allow the request)
        logger.warning(f"Rate limit check failed (Redis error): {e} — allowing request")


async def require_pro_plan(user=Depends(get_current_user)):
    """Require PRO or higher plan."""
    if user.plan not in ("PRO", "INSTITUTE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PRO_REQUIRED",
                "message": "This feature requires the Pro plan.",
                "upgrade_url": f"{settings.APP_URL}/pricing",
            },
        )
    return user


async def require_admin(user=Depends(get_current_user)):
    """Require admin role."""
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
