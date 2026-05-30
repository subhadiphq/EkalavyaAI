"""
EkalavyaAI — Agent 3: PYQ (Past Year Questions) Agent
Analyzes 10 years of PYQ to identify patterns, frequency, examiner behavior.

Responsibilities:
- Fetch PYQ for the chapter from database
- Calculate topic frequency and trend analysis
- Identify examiner patterns and predictable question types
- Provide strategic exam preparation insights
"""
import json
import logging
from typing import Optional

from agents.base import BaseAgent, ModelConfig
from config import settings

logger = logging.getLogger(__name__)


class PYQAgent(BaseAgent):
    """
    Agent 3 — PYQ Pattern Analysis Agent

    Primary: GPT-4o (OpenRouter)
    Backup 1: GPT-4o-mini (OpenRouter — cost-efficient)
    Backup 2: DeepSeek V3
    Free Fallback: Mixtral 8x7B (Groq)
    """

    def __init__(self):
        fallback_chain = [
            ModelConfig(
                model=settings.PYQ_MODEL_PRIMARY,
                provider="openrouter",
                max_tokens=3000,
                temperature=0.2,
            ),
            ModelConfig(
                model=settings.PYQ_MODEL_BACKUP1,
                provider="openrouter",
                max_tokens=2000,
                temperature=0.2,
            ),
            ModelConfig(
                model="deepseek/deepseek-chat",
                provider="openrouter",
                max_tokens=3000,
                temperature=0.2,
            ),
            ModelConfig(
                model=settings.PYQ_MODEL_FREE,
                provider="groq",
                max_tokens=2000,
                temperature=0.2,
            ),
        ]
        super().__init__("PYQAgent", fallback_chain)

    async def run(self, state: dict) -> dict:
        """
        Analyze PYQ patterns for the requested chapter.
        Returns frequency data, patterns, and strategic insights.
        """
        exam = state.get("exam", "CA_FOUNDATION")
        chapter_id = state.get("chapter_id")
        chapter_name = state.get("chapter_name", "")

        logger.info(f"[PYQAgent] Analyzing PYQ for: {chapter_name} ({exam})")

        # Fetch questions from DB
        questions = await self._fetch_pyq_from_db(chapter_id, exam)

        if questions:
            return await self._analyze_patterns(questions, chapter_name, exam)
        else:
            # LLM-based pattern synthesis when DB has no questions yet
            return await self._synthesize_patterns_from_llm(chapter_name, exam)

    async def _fetch_pyq_from_db(self, chapter_id: Optional[str], exam: str) -> list:
        """Fetch past year questions from PostgreSQL."""
        if not chapter_id:
            return []
        try:
            from sqlalchemy import select
            from models.user import Question
            from models.database import get_async_session

            async with get_async_session() as session:
                result = await session.execute(
                    select(Question)
                    .where(
                        Question.chapter_id == chapter_id,
                        Question.exam == exam,
                        Question.verified == True,
                    )
                    .order_by(Question.year.desc())
                )
                questions = result.scalars().all()
                return [
                    {
                        "year": q.year,
                        "month": q.month,
                        "marks": q.marks,
                        "question_type": q.question_type,
                        "question_text": q.question_text[:200],
                        "difficulty": q.difficulty,
                    }
                    for q in questions
                ]
        except Exception as e:
            logger.warning(f"[PYQAgent] DB fetch error: {e}")
            return []

    async def _analyze_patterns(
        self, questions: list, chapter_name: str, exam: str
    ) -> dict:
        """Analyze question patterns using LLM."""
        questions_text = json.dumps(questions[:20], indent=2)

        prompt = f"""
Analyze these Past Year Questions from {exam} exam for chapter "{chapter_name}".

Questions (last 10 years):
{questions_text}

Return ONLY valid JSON with this structure:
{{
  "frequency": {len(questions)},
  "avg_marks": 5,
  "topic_frequency": {{"Topic A": 5, "Topic B": 3}},
  "question_types": {{"MCQ": 3, "DESCRIPTIVE": 5, "NUMERICAL": 4}},
  "difficulty_trend": "increasing",
  "patterns": [
    "Theory + practical often combined (8 marks)",
    "Numerical always from Topic X"
  ],
  "high_probability_topics": ["Topic A", "Topic B"],
  "examiner_notes": "Examiner prefers step-by-step solutions",
  "strategic_advice": "Focus on Topic A — appeared every year since 2020"
}}

Return ONLY the JSON.
"""
        try:
            response = await self.call_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                json_mode=True,
            )
            clean = response.strip().lstrip("```json").rstrip("```").strip()
            result = json.loads(clean)
            result["from_db"] = True
            result["total_questions"] = len(questions)
            return result
        except Exception as e:
            logger.error(f"[PYQAgent] Pattern analysis error: {e}")
            return self._default_pyq_data(len(questions))

    async def _synthesize_patterns_from_llm(
        self, chapter_name: str, exam: str
    ) -> dict:
        """Generate PYQ patterns from LLM knowledge when DB is empty."""
        prompt = f"""
Based on your knowledge of {exam} past papers, analyze the chapter "{chapter_name}".

Return ONLY valid JSON:
{{
  "frequency": 8,
  "avg_marks": 8,
  "topic_frequency": {{}},
  "patterns": ["Pattern 1", "Pattern 2"],
  "high_probability_topics": ["Topic A"],
  "examiner_notes": "...",
  "strategic_advice": "...",
  "from_db": false,
  "llm_synthesized": true
}}
"""
        try:
            response = await self.call_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                json_mode=True,
            )
            clean = response.strip().lstrip("```json").rstrip("```").strip()
            return json.loads(clean)
        except Exception as e:
            logger.error(f"[PYQAgent] LLM synthesis error: {e}")
            return self._default_pyq_data(0)

    async def get_practice_questions(
        self,
        chapter_id: str,
        exam: str,
        question_type: Optional[str] = None,
        difficulty: Optional[float] = None,
        limit: int = 10,
    ) -> list:
        """Fetch practice questions with optional filters."""
        try:
            from sqlalchemy import select
            from models.user import Question
            from models.database import get_async_session

            async with get_async_session() as session:
                query = select(Question).where(
                    Question.chapter_id == chapter_id,
                    Question.exam == exam,
                    Question.verified == True,
                )
                if question_type:
                    query = query.where(Question.question_type == question_type)
                if difficulty:
                    query = query.where(Question.difficulty <= difficulty + 0.2)

                query = query.order_by(Question.year.desc()).limit(limit)
                result = await session.execute(query)
                questions = result.scalars().all()

                return [
                    {
                        "id": str(q.id),
                        "year": q.year,
                        "month": q.month,
                        "marks": q.marks,
                        "question_type": q.question_type,
                        "question_text": q.question_text,
                        "options": q.options,
                        "difficulty": q.difficulty,
                        # Note: solution/answer not returned until attempt submitted
                    }
                    for q in questions
                ]
        except Exception as e:
            logger.error(f"[PYQAgent] Fetch practice questions error: {e}")
            return []

    def _default_pyq_data(self, count: int) -> dict:
        return {
            "frequency": count,
            "avg_marks": 5,
            "topic_frequency": {},
            "patterns": [],
            "high_probability_topics": [],
            "examiner_notes": "",
            "strategic_advice": "Study all topics thoroughly.",
            "from_db": False,
        }
