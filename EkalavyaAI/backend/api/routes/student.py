"""
EkalavyaAI — Student API Routes
Profile management, credits, referral system, onboarding.
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_current_user
from config import CREDIT_ACTIONS, CREDIT_REDEMPTIONS
from models.database import get_async_session

logger = logging.getLogger(__name__)
router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    exam_targets: Optional[List[str]] = None
    exam_dates: Optional[dict] = None
    level: Optional[str] = None
    language: Optional[str] = None


class OnboardingRequest(BaseModel):
    exam_targets: List[str]
    exam_dates: dict
    level: str
    language: str
    weak_subjects: List[str] = []
    study_hours_per_day: int = 4
    learning_style: str = "visual"


class RedeemRequest(BaseModel):
    action: str  # e.g., "EXTRA_NOTES_PDF"


@router.get("/profile")
async def get_profile(current_user=Depends(get_current_user)):
    """Get full student profile."""
    from sqlalchemy import select
    from models.user import StudentProfile, Credit, Referral

    async with get_async_session() as session:
        profile_result = await session.execute(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        )
        profile = profile_result.scalar_one_or_none()

        credit_result = await session.execute(
            select(Credit).where(Credit.student_id == current_user.id)
        )
        credit = credit_result.scalar_one_or_none()

        referral_result = await session.execute(
            select(Referral).where(
                Referral.referrer_id == current_user.id,
                Referral.status == "ACTIVE",
            )
        )
        referral = referral_result.scalar_one_or_none()

        return {
            "id": str(current_user.id),
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "plan": current_user.plan,
            "is_verified": current_user.is_verified,
            "profile": {
                "exam_targets": profile.exam_targets if profile else [],
                "exam_dates": profile.exam_dates if profile else {},
                "level": profile.level.value if profile else "AVERAGE",
                "language": profile.language.value if profile else "English",
                "weak_chapters": profile.weak_chapters if profile else [],
                "login_streak": profile.login_streak if profile else 0,
                "readiness_scores": profile.readiness_scores if profile else {},
                "onboarding_complete": profile.onboarding_complete if profile else False,
            },
            "credits": credit.balance if credit else 0,
            "referral_code": referral.code if referral else None,
        }


@router.put("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
):
    """Update student profile."""
    from sqlalchemy import select
    from models.user import User, StudentProfile, Language, StudentLevel

    async with get_async_session() as session:
        # Update user
        if request.name:
            current_user.name = request.name
        if request.phone:
            current_user.phone = request.phone
        session.add(current_user)

        # Update profile
        result = await session.execute(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = StudentProfile(user_id=current_user.id)
            session.add(profile)

        if request.exam_targets:
            profile.exam_targets = request.exam_targets
        if request.exam_dates:
            profile.exam_dates = request.exam_dates
        if request.level:
            profile.level = StudentLevel(request.level)
        if request.language:
            profile.language = Language(request.language)

        await session.commit()
        return {"message": "Profile updated successfully"}


@router.post("/onboarding")
async def complete_onboarding(
    request: OnboardingRequest,
    current_user=Depends(get_current_user),
):
    """Complete the 5-step onboarding flow."""
    from sqlalchemy import select
    from models.user import StudentProfile, Credit, Language, StudentLevel
    from datetime import datetime

    async with get_async_session() as session:
        result = await session.execute(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = StudentProfile(user_id=current_user.id)
            session.add(profile)

        profile.exam_targets = request.exam_targets
        profile.exam_dates = request.exam_dates
        profile.level = StudentLevel(request.level)
        profile.language = Language(request.language)
        profile.learning_style = {
            "style": request.learning_style,
            "study_hours": request.study_hours_per_day,
        }
        profile.onboarding_complete = True

        # Award onboarding credits
        credit_result = await session.execute(
            select(Credit).where(Credit.student_id == current_user.id)
        )
        credit = credit_result.scalar_one_or_none()
        if credit:
            credit.balance += CREDIT_ACTIONS["COMPLETE_PROFILE"]
            credit.transaction_history = credit.transaction_history + [{
                "action": "COMPLETE_PROFILE",
                "amount": CREDIT_ACTIONS["COMPLETE_PROFILE"],
                "at": datetime.utcnow().isoformat(),
            }]

        await session.commit()
        return {
            "message": "Onboarding complete! Welcome to EkalavyaAI 🎉",
            "credits_earned": CREDIT_ACTIONS["COMPLETE_PROFILE"],
        }


@router.get("/credits")
async def get_credits(current_user=Depends(get_current_user)):
    """Get credit balance and transaction history."""
    from sqlalchemy import select
    from models.user import Credit

    async with get_async_session() as session:
        result = await session.execute(
            select(Credit).where(Credit.student_id == current_user.id)
        )
        credit = result.scalar_one_or_none()
        return {
            "balance": credit.balance if credit else 0,
            "history": (credit.transaction_history[-20:] if credit else []),
            "earning_actions": CREDIT_ACTIONS,
            "redemption_options": CREDIT_REDEMPTIONS,
        }


@router.post("/credits/redeem")
async def redeem_credits(
    request: RedeemRequest,
    current_user=Depends(get_current_user),
):
    """Redeem credits for a feature unlock."""
    from sqlalchemy import select
    from models.user import Credit
    from datetime import datetime

    cost = CREDIT_REDEMPTIONS.get(request.action)
    if not cost:
        raise HTTPException(status_code=400, detail="Invalid redemption action")

    async with get_async_session() as session:
        result = await session.execute(
            select(Credit).where(Credit.student_id == current_user.id)
        )
        credit = result.scalar_one_or_none()
        if not credit or credit.balance < cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient credits. Required: {cost}, Available: {credit.balance if credit else 0}",
            )

        credit.balance -= cost
        credit.transaction_history = credit.transaction_history + [{
            "action": f"REDEEM:{request.action}",
            "amount": -cost,
            "at": datetime.utcnow().isoformat(),
        }]
        await session.commit()

        return {
            "message": f"Redeemed: {request.action}",
            "credits_used": cost,
            "new_balance": credit.balance,
        }


@router.get("/referral")
async def get_referral_info(current_user=Depends(get_current_user)):
    """Get referral code and stats."""
    from sqlalchemy import select, func
    from models.user import Referral

    async with get_async_session() as session:
        referral_result = await session.execute(
            select(Referral).where(
                Referral.referrer_id == current_user.id,
                Referral.status == "ACTIVE",
            )
        )
        referral = referral_result.scalar_one_or_none()

        used_result = await session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == current_user.id,
                Referral.status == "USED",
            )
        )
        used_count = used_result.scalar() or 0

        return {
            "code": referral.code if referral else None,
            "referral_link": f"https://ekalavya.ai/signup?ref={referral.code}" if referral else None,
            "successful_referrals": used_count,
            "credits_earned": used_count * CREDIT_ACTIONS["REFERRAL_SUCCESS"],
            "credits_per_referral": CREDIT_ACTIONS["REFERRAL_SUCCESS"],
        }


@router.post("/referral")
async def apply_referral(
    referral_code: str,
    current_user=Depends(get_current_user),
):
    """Apply a referral code post-signup."""
    from sqlalchemy import select
    from models.user import Referral, Credit
    from datetime import datetime

    async with get_async_session() as session:
        result = await session.execute(
            select(Referral).where(
                Referral.code == referral_code,
                Referral.status == "ACTIVE",
            )
        )
        referral = result.scalar_one_or_none()
        if not referral:
            raise HTTPException(status_code=400, detail="Invalid or expired referral code")

        if str(referral.referrer_id) == str(current_user.id):
            raise HTTPException(status_code=400, detail="Cannot use your own referral code")

        # Award referrer credits
        referrer_credit_result = await session.execute(
            select(Credit).where(Credit.student_id == referral.referrer_id)
        )
        referrer_credit = referrer_credit_result.scalar_one_or_none()
        if referrer_credit:
            referrer_credit.balance += CREDIT_ACTIONS["REFERRAL_SUCCESS"]

        # Award new user credits
        my_credit_result = await session.execute(
            select(Credit).where(Credit.student_id == current_user.id)
        )
        my_credit = my_credit_result.scalar_one_or_none()
        if my_credit:
            my_credit.balance += CREDIT_ACTIONS["REFERRAL_BONUS_NEW_USER"]

        referral.referred_id = current_user.id
        referral.status = "USED"
        referral.credited_at = datetime.utcnow()

        await session.commit()
        return {
            "message": "Referral applied!",
            "credits_earned": CREDIT_ACTIONS["REFERRAL_BONUS_NEW_USER"],
        }
