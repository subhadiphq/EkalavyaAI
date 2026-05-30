"""
EkalavyaAI — Authentication Routes
JWT-based auth with email/password and Google OAuth.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from config import settings, CREDIT_ACTIONS
from api.dependencies import get_current_user
from models.database import get_async_session

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    referral_code: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    google_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _create_jwt(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _generate_referral_code(name: str) -> str:
    """Generate unique referral code like EKA-RAVI-4B2F."""
    prefix = name[:3].upper()
    suffix = str(uuid.uuid4())[:6].upper().replace("-", "")
    return f"EKA-{prefix}-{suffix[:4]}"


# ─── Routes ──────────────────────────────────────────────────────────────────
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """Register a new student."""
    from sqlalchemy import select
    from models.user import User, StudentProfile, Credit, Referral, Language, StudentLevel

    async with get_async_session() as session:
        # Check email uniqueness
        existing = await session.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user
        user = User(
            name=request.name,
            email=request.email,
            password_hash=_hash_password(request.password),
            plan="FREE",
            is_verified=False,
        )
        session.add(user)
        await session.flush()  # Get user.id

        # Create student profile
        profile = StudentProfile(
            user_id=user.id,
            level=StudentLevel.AVERAGE,
            language=Language.ENGLISH,
        )
        session.add(profile)

        # Initialize credits
        credit = Credit(student_id=user.id, balance=0, transaction_history=[])
        session.add(credit)

        # Create referral entry for this user
        referral = Referral(
            referrer_id=user.id,
            code=_generate_referral_code(request.name),
            status="ACTIVE",
        )
        session.add(referral)

        # Process incoming referral
        if request.referral_code:
            await _process_referral(
                session, request.referral_code, user.id, credit
            )

        await session.commit()
        await session.refresh(user)

        # Send welcome email (async task)
        _send_welcome_email_task(str(user.id), user.name, user.email)

        token = _create_jwt(str(user.id), user.email)
        return TokenResponse(
            access_token=token,
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            user={
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "plan": user.plan,
                "onboarding_complete": False,
            },
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    from sqlalchemy import select
    from models.user import User, StudentProfile

    async with get_async_session() as session:
        result = await session.execute(
            select(User).where(User.email == request.email, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not _verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Update last login + streak
        user.last_login = datetime.utcnow()

        # Update login streak
        profile_result = await session.execute(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            await _update_streak(session, profile)

        await session.commit()

        token = _create_jwt(str(user.id), user.email)
        return TokenResponse(
            access_token=token,
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            user={
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "plan": user.plan,
                "onboarding_complete": profile.onboarding_complete if profile else False,
            },
        )


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest):
    """Login/Register with Google OAuth token."""
    # Verify Google token
    google_user = await _verify_google_token(request.google_token)
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    from sqlalchemy import select
    from models.user import User, StudentProfile, Credit, Referral, Language, StudentLevel

    async with get_async_session() as session:
        # Find or create user
        result = await session.execute(
            select(User).where(User.email == google_user["email"])
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                name=google_user["name"],
                email=google_user["email"],
                google_id=google_user["sub"],
                plan="FREE",
                is_verified=True,
            )
            session.add(user)
            await session.flush()

            profile = StudentProfile(user_id=user.id)
            session.add(profile)
            credit = Credit(student_id=user.id, balance=0, transaction_history=[])
            session.add(credit)
            referral = Referral(
                referrer_id=user.id,
                code=_generate_referral_code(user.name),
                status="ACTIVE",
            )
            session.add(referral)
            is_new = True
        else:
            user.last_login = datetime.utcnow()
            is_new = False

        await session.commit()
        await session.refresh(user)

        token = _create_jwt(str(user.id), user.email)
        return TokenResponse(
            access_token=token,
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            user={
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "plan": user.plan,
                "is_new": is_new,
                "onboarding_complete": not is_new,
            },
        )


@router.post("/refresh")
async def refresh_token(current_user=Depends(get_current_user)):
    """Refresh JWT token."""
    token = _create_jwt(str(current_user.id), current_user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_HOURS * 3600,
    }


@router.post("/logout")
async def logout():
    """Logout (client-side token invalidation)."""
    return {"message": "Logged out successfully"}


# ─── Helpers ─────────────────────────────────────────────────────────────────
async def _verify_google_token(token: str) -> Optional[dict]:
    """Verify Google OAuth token and return user info."""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request())
        return {
            "sub": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo.get("name", "Student"),
        }
    except Exception as e:
        logger.error(f"Google token verification failed: {e}")
        return None


async def _process_referral(session, referral_code: str, new_user_id, credit):
    """Process a referral code and award credits."""
    from sqlalchemy import select
    from models.user import Referral, Credit
    from datetime import datetime

    result = await session.execute(
        select(Referral).where(
            Referral.code == referral_code,
            Referral.status == "ACTIVE",
        )
    )
    referral = result.scalar_one_or_none()
    if not referral:
        return

    referral.referred_id = new_user_id
    referral.status = "USED"
    referral.credited_at = datetime.utcnow()

    # Credit the referrer
    referrer_credit_result = await session.execute(
        select(Credit).where(Credit.student_id == referral.referrer_id)
    )
    referrer_credit = referrer_credit_result.scalar_one_or_none()
    if referrer_credit:
        referrer_credit.balance += CREDIT_ACTIONS["REFERRAL_SUCCESS"]

    # Credit the new user
    credit.balance += CREDIT_ACTIONS["REFERRAL_BONUS_NEW_USER"]


async def _update_streak(session, profile):
    """Update login streak using SM-2 schedule."""
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    if profile.last_streak_date:
        last = profile.last_streak_date.date()
        if last == today:
            return  # Already counted today
        elif last == today - timedelta(days=1):
            profile.login_streak += 1
        else:
            profile.login_streak = 1
    else:
        profile.login_streak = 1
    profile.last_streak_date = datetime.utcnow()


def _send_welcome_email_task(user_id: str, name: str, email: str):
    """Queue welcome email via Celery."""
    try:
        from tasks.celery_app import celery_app
        celery_app.send_task(
            "tasks.send_welcome_email",
            kwargs={"user_id": user_id, "name": name, "email": email},
        )
    except Exception as e:
        logger.warning(f"Could not queue welcome email: {e}")
