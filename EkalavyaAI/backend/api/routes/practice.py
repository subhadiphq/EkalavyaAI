"""
EkalavyaAI — Practice API Routes
PYQ practice: fetch questions, submit attempts, get AI feedback.
"""
import logging
import uuid as _uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.dependencies import get_current_user, check_plan_limit
from agents.pyq_agent import PYQAgent
from models.database import get_async_session

logger = logging.getLogger(__name__)
router = APIRouter()
pyq_agent = PYQAgent()


class AttemptRequest(BaseModel):
    question_id: str
    student_answer: str
    time_taken_seconds: Optional[int] = None


class FeedbackRequest(BaseModel):
    question_id: str
    student_answer: str
    exam: str


@router.get("/questions")
@router.get("/pyq")  # alias — same handler (matches /practice/pyq spec)
async def get_practice_questions(
    exam: str = Query(...),
    chapter_id: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),  # MCQ | DESCRIPTIVE | NUMERICAL
    difficulty: Optional[float] = Query(None, ge=0.0, le=1.0),
    year_from: Optional[int] = Query(None),
    limit: int = Query(10, le=50),
    current_user=Depends(get_current_user),
):
    """Get filtered PYQ practice questions (also at ``/practice/pyq``)."""
    await check_plan_limit(current_user, "pyq_questions")

    try:
        from sqlalchemy import select
        from models.user import Question

        async with get_async_session() as session:
            query = select(Question).where(
                Question.exam == exam,
                Question.verified == True,
            )
            if chapter_id:
                query = query.where(Question.chapter_id == chapter_id)
            if question_type:
                query = query.where(Question.question_type == question_type)
            if difficulty is not None:
                query = query.where(Question.difficulty <= difficulty + 0.2)
            if year_from:
                query = query.where(Question.year >= year_from)

            query = query.order_by(Question.year.desc()).limit(limit)
            result = await session.execute(query)
            questions = result.scalars().all()

            return {
                "questions": [
                    {
                        "id": str(q.id),
                        "year": q.year,
                        "month": q.month,
                        "marks": q.marks,
                        "question_type": q.question_type,
                        "question_text": q.question_text,
                        "options": q.options,
                        "difficulty": q.difficulty,
                        "exam": q.exam.value,
                        # ⚠️ answer NOT returned — only after attempt
                    }
                    for q in questions
                ],
                "total": len(questions),
                "exam": exam,
            }
    except Exception as e:
        logger.error(f"Get questions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attempt")
async def submit_attempt(
    request: AttemptRequest,
    current_user=Depends(get_current_user),
):
    """
    Submit a PYQ answer attempt.
    Returns whether correct + reveals solution + AI explanation.
    """
    try:
        from sqlalchemy import select
        from models.user import Question, QuestionAttempt

        async with get_async_session() as session:
            result = await session.execute(
                select(Question).where(Question.id == request.question_id)
            )
            question = result.scalar_one_or_none()
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")

            # Check correctness
            is_correct = _check_answer(
                question.question_type,
                request.student_answer,
                question.correct_answer,
            )

            # Save attempt
            attempt = QuestionAttempt(
                student_id=current_user.id,
                question_id=question.id,
                student_answer=request.student_answer,
                is_correct=is_correct,
                time_taken_seconds=request.time_taken_seconds,
                score=1.0 if is_correct else 0.0,
            )
            session.add(attempt)
            await session.commit()

            return {
                "is_correct": is_correct,
                "correct_answer": question.correct_answer,
                "solution": question.solution,
                "explanation": question.explanation,
                "examiner_notes": question.examiner_notes,
                "attempt_id": str(attempt.id),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit attempt error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def get_ai_feedback(
    request: FeedbackRequest,
    current_user=Depends(get_current_user),
):
    """Get personalized AI feedback on a descriptive/numerical answer."""
    from agents.teacher_agent import TeacherAgent
    from agents.memory_agent import MemoryAgent

    teacher = TeacherAgent()
    memory = MemoryAgent()

    profile = await memory.read_student_profile(str(current_user.id))

    # Fetch question
    from sqlalchemy import select
    from models.user import Question

    async with get_async_session() as session:
        result = await session.execute(
            select(Question).where(Question.id == request.question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

    feedback_prompt = f"""
A {request.exam} student (level: {profile.get('level', 'AVERAGE')}) answered this question:

QUESTION: {question.question_text}
MARKS: {question.marks}

STUDENT'S ANSWER: {request.student_answer}

CORRECT SOLUTION: {question.solution}

Provide constructive feedback:
1. What they got right ✅
2. What was missing or wrong ❌  
3. How to improve their answer for full marks
4. Exam-specific tips for this type of question

Be encouraging but specific. Use {request.exam} marking scheme format.
"""
    state = {
        "exam": request.exam,
        "language": profile.get("language", "English"),
        "student_level": profile.get("level", "AVERAGE"),
        "query": feedback_prompt,
        "research_chunks": [],
        "pyq_patterns": {},
    }
    feedback = await teacher.solve_question(state)

    return {"feedback": feedback, "question_id": request.question_id}


@router.get("/mistakes")
async def get_mistake_history(
    exam: Optional[str] = Query(None),
    limit: int = Query(20, le=50),
    current_user=Depends(get_current_user),
):
    """Get student's mistake history for targeted revision."""
    try:
        from sqlalchemy import select
        from models.user import Mistake, Chapter

        async with get_async_session() as session:
            query = (
                select(Mistake, Chapter)
                .join(Chapter, Mistake.chapter_id == Chapter.id, isouter=True)
                .where(
                    Mistake.student_id == current_user.id,
                    Mistake.resolved == False,
                )
                .order_by(Mistake.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            rows = result.all()

            return {
                "mistakes": [
                    {
                        "id": str(m.id),
                        "chapter": ch.name if ch else "Unknown",
                        "type": m.mistake_type.value,
                        "description": m.description,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m, ch in rows
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _check_answer(question_type: str, student: str, correct: str) -> bool:
    """Simple answer checking logic."""
    if question_type == "MCQ":
        return student.strip().upper() == correct.strip().upper()
    # For descriptive: use AI feedback instead of boolean
    return False
