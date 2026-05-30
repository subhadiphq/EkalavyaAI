"""
EkalavyaAI — Agent 1: Syllabus Agent
Uses Gemini 1.5 Pro (1M context) to understand full exam syllabus structure.

Responsibilities:
- Map chapter to syllabus position (unit, topic hierarchy)
- Calculate topic importance scores from ICAI/NCERT curriculum
- Identify inter-chapter connections via Neo4j knowledge graph
- Provide learning sequence recommendations
"""
import json
import logging
from typing import Optional

from agents.base import BaseAgent, ModelConfig
from config import settings

logger = logging.getLogger(__name__)


class SyllabusAgent(BaseAgent):
    """
    Agent 1 — Syllabus Mapping Agent

    Primary: Gemini 1.5 Pro (1M context, Google AI Studio)
    Backup 1: Claude 3.5 Sonnet (OpenRouter)
    Backup 2: Moonshot Kimi (128K context, OpenRouter)
    Free Fallback: Llama 3.1 70B (Groq)
    """

    def __init__(self):
        fallback_chain = [
            ModelConfig(
                model=settings.SYLLABUS_MODEL_PRIMARY,
                provider="openrouter",
                max_tokens=4096,
                temperature=0.1,
            ),
            ModelConfig(
                model=settings.SYLLABUS_MODEL_BACKUP1,
                provider="openrouter",
                max_tokens=4096,
                temperature=0.1,
            ),
            ModelConfig(
                model=settings.SYLLABUS_MODEL_BACKUP2,
                provider="openrouter",
                max_tokens=4096,
                temperature=0.1,
            ),
            ModelConfig(
                model=settings.SYLLABUS_MODEL_FREE,
                provider="groq",
                max_tokens=2048,
                temperature=0.1,
            ),
        ]
        super().__init__("SyllabusAgent", fallback_chain)

    async def run(self, state: dict) -> dict:
        """
        Returns structured syllabus context for the requested chapter.
        """
        exam = state.get("exam", "CA_FOUNDATION")
        subject = state.get("subject", "")
        chapter_name = state.get("chapter_name", "")
        chapter_id = state.get("chapter_id")

        logger.info(f"[SyllabusAgent] Mapping: {chapter_name} ({exam})")

        # First try DB cache
        db_context = await self._get_from_db(chapter_id)
        if db_context:
            return db_context

        # Build from LLM
        return await self._build_syllabus_context(exam, subject, chapter_name)

    async def _get_from_db(self, chapter_id: Optional[str]) -> Optional[dict]:
        """Try to get pre-mapped syllabus from PostgreSQL."""
        if not chapter_id:
            return None
        try:
            from sqlalchemy import select
            from models.user import Chapter, Topic
            from models.database import get_async_session

            async with get_async_session() as session:
                result = await session.execute(
                    select(Chapter).where(Chapter.id == chapter_id)
                )
                chapter = result.scalar_one_or_none()
                if not chapter:
                    return None

                topic_result = await session.execute(
                    select(Topic).where(Topic.chapter_id == chapter_id)
                    .order_by(Topic.importance_score.desc())
                )
                topics = topic_result.scalars().all()

                return {
                    "chapter_name": chapter.name,
                    "exam": chapter.exam.value,
                    "subject": chapter.subject,
                    "chapter_no": chapter.chapter_no,
                    "importance_score": chapter.importance_score,
                    "pyq_frequency": chapter.pyq_frequency,
                    "topics": [
                        {
                            "name": t.name,
                            "score": t.importance_score,
                            "pyq_frequency": t.pyq_frequency,
                        }
                        for t in topics
                    ],
                }
        except Exception as e:
            logger.warning(f"[SyllabusAgent] DB fetch error: {e}")
            return None

    async def _build_syllabus_context(
        self, exam: str, subject: str, chapter_name: str
    ) -> dict:
        """Build syllabus context using LLM when DB cache misses."""
        prompt = f"""
Analyze the syllabus structure for this exam chapter and return structured JSON.

Exam: {exam}
Subject: {subject}
Chapter: {chapter_name}

Return ONLY valid JSON in this exact format:
{{
  "chapter_name": "{chapter_name}",
  "exam": "{exam}",
  "subject": "{subject}",
  "importance_score": 0.85,
  "estimated_marks": 10,
  "topics": [
    {{"name": "Topic 1", "score": 0.9, "pyq_frequency": 5}},
    {{"name": "Topic 2", "score": 0.7, "pyq_frequency": 3}}
  ],
  "prerequisites": ["Chapter X", "Chapter Y"],
  "connects_to": ["Chapter Z"],
  "exam_tips": ["Tip 1", "Tip 2"],
  "common_mistakes": ["Mistake 1"]
}}

Use your knowledge of {exam} official syllabus.
For CA: follow ICAI curriculum. For JEE/NEET: follow NCERT.
Return ONLY the JSON, no other text.
"""
        try:
            response = await self.call_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                json_mode=True,
            )
            # Clean response
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            return json.loads(clean)
        except Exception as e:
            logger.error(f"[SyllabusAgent] LLM build error: {e}")
            return {
                "chapter_name": chapter_name,
                "exam": exam,
                "subject": subject,
                "importance_score": 0.7,
                "topics": [],
                "prerequisites": [],
            }
