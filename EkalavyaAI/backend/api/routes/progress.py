"""
EkalavyaAI — Progress API Routes
Exam readiness score, syllabus coverage heatmap, revision schedule, weekly AI report.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_current_user
from agents.memory_agent import MemoryAgent
from models.database import get_async_session

logger = logging.getLogger(__name__)
router = APIRouter()
memory_agent = MemoryAgent()


@router.get("/readiness")
async def get_readiness_score(
    exam: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
):
    """
    Get exam readiness score (0-100%).
    Formula: Syllabus Coverage 35% + PYQ Accuracy 30% + Revision 20% + Depth 15%
    """
    try:
        profile = await memory_agent.read_student_profile(str(current_user.id))
        target_exam = exam or (profile.get("exam_targets") or ["CA_FOUNDATION"])[0]

        readiness_scores = profile.get("readiness_scores", {})
        score = readiness_scores.get(target_exam, 0.0)

        # Compute live stats
        stats = await _get_progress_stats(str(current_user.id), target_exam)

        return {
            "readiness_score": round(score, 1),
            "exam": target_exam,
            "breakdown": {
                "syllabus_coverage": stats.get("syllabus_pct", 0),
                "pyq_accuracy": stats.get("pyq_accuracy", 0),
                "revision_completion": stats.get("revision_pct", 0),
                "concept_depth": stats.get("depth_score", 0),
            },
            "chapters_studied": stats.get("chapters_studied", 0),
            "pyq_solved": stats.get("pyq_solved", 0),
            "credits": stats.get("credits", 0),
            "login_streak": profile.get("login_streak", 0),
            "level": profile.get("level", "AVERAGE"),
            "grade_prediction": _predict_grade(score),
        }
    except Exception as e:
        logger.error(f"Readiness score error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/syllabus")
async def get_syllabus_heatmap(
    exam: str = Query(...),
    current_user=Depends(get_current_user),
):
    """
    Get syllabus coverage heatmap.
    Returns per-chapter studied/not-studied status with importance scores.
    """
    try:
        from sqlalchemy import select, func
        from models.user import Chapter, Note

        async with get_async_session() as session:
            # All chapters for this exam
            chapters_result = await session.execute(
                select(Chapter).where(Chapter.exam == exam).order_by(
                    Chapter.subject, Chapter.chapter_no
                )
            )
            all_chapters = chapters_result.scalars().all()

            # Which chapters has this student studied?
            studied_result = await session.execute(
                select(Note.chapter_id).where(
                    Note.student_id == current_user.id
                ).distinct()
            )
            studied_ids = {str(row) for row in studied_result.scalars().all()}

            # Group by subject
            subjects: dict = {}
            for ch in all_chapters:
                subj = ch.subject
                if subj not in subjects:
                    subjects[subj] = {"chapters": [], "studied": 0, "total": 0}
                is_studied = str(ch.id) in studied_ids
                subjects[subj]["chapters"].append({
                    "id": str(ch.id),
                    "name": ch.name,
                    "chapter_no": ch.chapter_no,
                    "importance_score": ch.importance_score,
                    "pyq_frequency": ch.pyq_frequency,
                    "studied": is_studied,
                })
                subjects[subj]["total"] += 1
                if is_studied:
                    subjects[subj]["studied"] += 1

            # Coverage percentages
            for subj_data in subjects.values():
                t = subj_data["total"]
                subj_data["coverage_pct"] = round(
                    (subj_data["studied"] / t * 100) if t else 0, 1
                )

            return {
                "exam": exam,
                "subjects": subjects,
                "overall_coverage": round(
                    len(studied_ids) / max(len(all_chapters), 1) * 100, 1
                ),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revision")
async def get_revision_schedule(
    days_ahead: int = Query(7, le=30),
    current_user=Depends(get_current_user),
):
    """Get upcoming SM-2 spaced repetition revision schedule."""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import select
        from models.user import RevisionSchedule, Chapter

        async with get_async_session() as session:
            cutoff = datetime.utcnow() + timedelta(days=days_ahead)
            result = await session.execute(
                select(RevisionSchedule, Chapter)
                .join(Chapter, RevisionSchedule.chapter_id == Chapter.id)
                .where(
                    RevisionSchedule.student_id == current_user.id,
                    RevisionSchedule.due_date <= cutoff,
                    RevisionSchedule.completed == False,
                )
                .order_by(RevisionSchedule.due_date.asc())
                .limit(20)
            )
            rows = result.all()

            today = datetime.utcnow().date()
            return {
                "revisions": [
                    {
                        "id": str(rev.id),
                        "chapter_id": str(rev.chapter_id),
                        "chapter_name": ch.name,
                        "subject": ch.subject,
                        "exam": ch.exam.value,
                        "due_date": rev.due_date.isoformat(),
                        "is_overdue": rev.due_date.date() < today,
                        "sm2_level": rev.sm2_level,
                        "priority": rev.priority,
                    }
                    for rev, ch in rows
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_weekly_report(
    current_user=Depends(get_current_user),
):
    """Get AI-generated weekly study performance report."""
    try:
        report = await memory_agent.generate_weekly_report(str(current_user.id))
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Helpers ─────────────────────────────────────────────────────────────────
async def _get_progress_stats(student_id: str, exam: str) -> dict:
    """Aggregate live progress stats from DB."""
    try:
        from sqlalchemy import select, func
        from models.user import Note, QuestionAttempt, RevisionSchedule, Credit, Chapter

        async with get_async_session() as session:
            # Chapters studied count
            notes_result = await session.execute(
                select(func.count(Note.id.distinct())).where(
                    Note.student_id == student_id
                )
            )
            chapters_studied = notes_result.scalar() or 0

            # PYQ accuracy
            attempts_result = await session.execute(
                select(
                    func.count(QuestionAttempt.id),
                    func.sum(QuestionAttempt.is_correct.cast("int")),
                ).where(QuestionAttempt.student_id == student_id)
            )
            total_attempts, correct_attempts = attempts_result.one()
            pyq_accuracy = round(
                (correct_attempts / total_attempts * 100) if total_attempts else 0, 1
            )

            # Credits
            credit_result = await session.execute(
                select(Credit).where(Credit.student_id == student_id)
            )
            credit = credit_result.scalar_one_or_none()

            # Total chapters for exam
            total_result = await session.execute(
                select(func.count(Chapter.id)).where(Chapter.exam == exam)
            )
            total_chapters = total_result.scalar() or 1

            return {
                "chapters_studied": chapters_studied,
                "syllabus_pct": round(chapters_studied / total_chapters * 100, 1),
                "pyq_solved": total_attempts or 0,
                "pyq_accuracy": pyq_accuracy,
                "revision_pct": 60.0,  # Simplified
                "depth_score": 70.0,   # Simplified
                "credits": credit.balance if credit else 0,
            }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {}


def _predict_grade(score: float) -> str:
    """Predict exam grade from readiness score."""
    if score >= 85:
        return "Merit / Distinction"
    elif score >= 70:
        return "Pass with Good Marks"
    elif score >= 50:
        return "Pass"
    else:
        return "Needs More Preparation"
