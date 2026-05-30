"""
EkalavyaAI — Agent 7: Student Memory & Personalization Agent
Always uses Groq (free, fast) — runs before and after every request.

Responsibilities:
- Read/write student profile from PostgreSQL
- Inject personalization prefix into every request
- Extract session facts via LLM and store in Pinecone
- Generate weekly study plan
- Run SM-2 spaced repetition algorithm
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
import uuid

from agents.base import BaseAgent, ModelConfig
from config import settings, SM2_INTERVALS

logger = logging.getLogger(__name__)

# SM-2 Algorithm Constants
SM2_INITIAL_EASINESS = 2.5
SM2_MIN_EASINESS = 1.3


class MemoryAgent(BaseAgent):
    """
    Agent 7 — Student Memory & Personalization Agent

    Primary: Groq Llama 3.1 70B (ALWAYS FREE, < 1 second)
    Backup 1: Gemma 2 9B (Groq — free)
    Backup 2: Mixtral 8x7B (Groq — free)
    Last Resort: Llama 3.1 8B on NVIDIA NIM (free tier)
    """

    def __init__(self):
        fallback_chain = [
            ModelConfig(
                model=settings.MEMORY_MODEL,  # llama-3.1-70b
                provider="groq",
                max_tokens=2048,
                temperature=0.1,  # Low temperature for structured extraction
            ),
            ModelConfig(
                model=settings.MEMORY_MODEL_BACKUP,  # gemma2-9b
                provider="groq",
                max_tokens=2048,
                temperature=0.1,
            ),
            ModelConfig(
                model="mixtral-8x7b-32768",
                provider="groq",
                max_tokens=2048,
                temperature=0.1,
            ),
        ]
        super().__init__("MemoryAgent", fallback_chain)
        self._pinecone_client = None
        self._db = None

    async def _get_db(self):
        """Lazy DB connection."""
        if not self._db:
            from models.database import get_async_session
            self._db = get_async_session()
        return self._db

    async def _get_pinecone(self):
        """Lazy Pinecone connection."""
        if not self._pinecone_client:
            from pinecone import Pinecone
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._pinecone_client = pc.Index(settings.PINECONE_MEMORY_INDEX)
        return self._pinecone_client

    async def run(self, state: dict) -> dict:
        """Standard agent interface — reads student profile."""
        return await self.read_student_profile(state["student_id"])

    async def read_student_profile(self, student_id: str) -> dict:
        """
        Read student profile from PostgreSQL + retrieve relevant memories from Pinecone.
        Returns enriched student context for injection into other agents.
        """
        try:
            from sqlalchemy import select
            from models.user import StudentProfile, User
            async with await self._get_db() as session:
                result = await session.execute(
                    select(User, StudentProfile)
                    .join(StudentProfile, User.id == StudentProfile.user_id)
                    .where(User.id == uuid.UUID(student_id))
                )
                row = result.first()

                if not row:
                    return self._default_profile()

                user, profile = row
                return {
                    "student_id": str(user.id),
                    "name": user.name,
                    "level": profile.level.value,
                    "language": profile.language.value,
                    "exam_targets": profile.exam_targets,
                    "exam_dates": profile.exam_dates,
                    "weak_chapters": profile.weak_chapters,
                    "learning_style": profile.learning_style,
                    "behavioral_profile": profile.behavioral_profile,
                    "login_streak": profile.login_streak,
                    "readiness_scores": profile.readiness_scores,
                }
        except Exception as e:
            logger.error(f"[MemoryAgent] DB read error: {e}")
            return self._default_profile()

    async def update_student_profile(self, student_id: str, session_data: dict):
        """
        Update student profile after a study session.
        1. Extract session facts via LLM
        2. Update PostgreSQL profile
        3. Update Pinecone semantic memory
        4. Update revision schedule (SM-2)
        """
        try:
            # Extract session facts using Groq
            facts = await self._extract_session_facts(session_data)
            logger.info(f"[MemoryAgent] Extracted {len(facts)} facts for {student_id}")

            # Update PostgreSQL
            await self._update_db_profile(student_id, session_data, facts)

            # Store facts in Pinecone
            if facts:
                await self._store_memory_embeddings(student_id, facts)

            # Update revision schedule
            chapter_id = session_data.get("chapter_studied")
            if chapter_id:
                await self._update_revision_schedule(student_id, chapter_id)

        except Exception as e:
            logger.error(f"[MemoryAgent] Update error for {student_id}: {e}")

    async def _extract_session_facts(self, session_data: dict) -> list:
        """Use Groq LLM to extract 3-5 memorable facts from session."""
        prompt = f"""
Extract 3-5 important memory facts from this study session.
Facts should be specific, personalized, and useful for future sessions.

Session Data:
{json.dumps(session_data, indent=2)}

Return ONLY a JSON array of fact strings. Example:
["Student studied Partnership Accounts — struggled with goodwill valuation",
 "Student is weak in Chapter 5 — needs more examples",
 "Student prefers examples before theory"]

Return ONLY the JSON array, nothing else.
"""
        try:
            response = await self.call_groq_direct(
                model=settings.MEMORY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            # Clean and parse JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except Exception as e:
            logger.warning(f"[MemoryAgent] Fact extraction failed: {e}")
            return []

    async def _store_memory_embeddings(self, student_id: str, facts: list):
        """Embed and store session facts in Pinecone for semantic retrieval."""
        try:
            from rag.embeddings import EmbeddingService
            embedder = EmbeddingService()
            index = await self._get_pinecone()

            vectors = []
            for i, fact in enumerate(facts):
                embedding = await embedder.embed_text(fact)
                vectors.append({
                    "id": f"{student_id}:{datetime.utcnow().isoformat()}:{i}",
                    "values": embedding,
                    "metadata": {
                        "student_id": student_id,
                        "fact": fact,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                })

            if vectors:
                index.upsert(vectors=vectors, namespace=f"student_{student_id}")
                logger.info(f"[MemoryAgent] Stored {len(vectors)} memory vectors")
        except Exception as e:
            logger.error(f"[MemoryAgent] Pinecone storage error: {e}")

    async def retrieve_relevant_memories(
        self, student_id: str, context: str, top_k: int = 5
    ) -> list:
        """Retrieve semantically relevant memories for current session context."""
        try:
            from rag.embeddings import EmbeddingService
            embedder = EmbeddingService()
            index = await self._get_pinecone()

            query_embedding = await embedder.embed_text(context)
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=f"student_{student_id}",
                include_metadata=True,
            )

            return [
                match["metadata"]["fact"]
                for match in results.get("matches", [])
                if match["score"] > 0.7
            ]
        except Exception as e:
            logger.error(f"[MemoryAgent] Memory retrieval error: {e}")
            return []

    async def _update_db_profile(
        self, student_id: str, session_data: dict, facts: list
    ):
        """Update PostgreSQL with session results."""
        try:
            from sqlalchemy import update
            from models.user import StudentProfile, StudySession
            async with await self._get_db() as session:
                # Log study session
                study_session = StudySession(
                    student_id=uuid.UUID(student_id),
                    start_time=datetime.utcnow() - timedelta(minutes=30),
                    end_time=datetime.utcnow(),
                    topics_covered=session_data.get("topics_covered", []),
                    agent_calls_made=len(session_data.get("agent_timings", {})),
                    session_facts=facts,
                    memory_updated=True,
                )
                session.add(study_session)
                await session.commit()
        except Exception as e:
            logger.error(f"[MemoryAgent] DB update error: {e}")

    async def _update_revision_schedule(self, student_id: str, chapter_id: str):
        """Update SM-2 spaced repetition schedule."""
        try:
            from sqlalchemy import select
            from models.user import RevisionSchedule
            async with await self._get_db() as db_session:
                result = await db_session.execute(
                    select(RevisionSchedule).where(
                        RevisionSchedule.student_id == uuid.UUID(student_id),
                        RevisionSchedule.chapter_id == uuid.UUID(chapter_id),
                    )
                )
                schedule = result.scalar_one_or_none()

                if schedule:
                    # Progress SM-2
                    new_level = min(schedule.sm2_level + 1, len(SM2_INTERVALS) - 1)
                    days_until_next = SM2_INTERVALS[new_level]
                    schedule.sm2_level = new_level
                    schedule.due_date = datetime.utcnow() + timedelta(days=days_until_next)
                    schedule.completed = True
                else:
                    # Create new schedule entry
                    new_schedule = RevisionSchedule(
                        student_id=uuid.UUID(student_id),
                        chapter_id=uuid.UUID(chapter_id),
                        due_date=datetime.utcnow() + timedelta(days=SM2_INTERVALS[1]),
                        sm2_level=1,
                        sm2_easiness=SM2_INITIAL_EASINESS,
                        priority=5,
                    )
                    db_session.add(new_schedule)

                await db_session.commit()
        except Exception as e:
            logger.error(f"[MemoryAgent] Revision schedule update error: {e}")

    async def get_personalization_prefix(
        self, student_id: str, cached_notes: dict, level: str
    ) -> str:
        """
        Generate a small personalization layer for cached notes.
        Uses Groq for cheapness and speed.
        """
        prompt = f"""
A student (level: {level}) is accessing cached study notes.
Generate a SHORT personalized intro message (3-4 sentences) to add at the top of the notes.

Adapt for level:
- WEAK: More encouragement, suggest starting with examples first
- AVERAGE: Balanced, suggest focusing on PYQ sections
- TOPPER: Direct, suggest attempting advanced questions after

Chapter: {cached_notes.get('chapter_name', 'this chapter')}
Student level: {level}

Return ONLY the message text, no quotes or labels.
"""
        return await self.call_groq_direct(
            model=settings.MEMORY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5,
        )

    async def generate_weekly_report(self, student_id: str) -> dict:
        """
        Generate AI weekly study report for a student.
        Called by Celery nightly job every Monday.
        """
        # Gather week's activity from DB
        profile = await self.read_student_profile(student_id)

        prompt = f"""
Generate a personalized weekly study report for a {profile.get('exam_targets', ['CA'])} student.

Student Profile:
- Level: {profile.get('level')}
- Weak chapters: {profile.get('weak_chapters', [])}
- Readiness scores: {profile.get('readiness_scores', {})}
- Login streak: {profile.get('login_streak', 0)} days

Write a motivating but honest 3-4 sentence report like:
"This week you studied X chapters — great consistency! However, [topic] needs attention.
[Days] days until your exam. You're currently on track for a [grade] grade.
To reach [better grade], complete [specific action] by [day]."

Be specific. Use real numbers. Be encouraging but honest.
"""
        report_text = await self.call_groq_direct(
            model=settings.MEMORY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )

        return {
            "student_id": student_id,
            "report_text": report_text,
            "generated_at": datetime.utcnow().isoformat(),
            "readiness_score": profile.get("readiness_scores", {}),
        }

    async def calculate_readiness_score(self, student_id: str, exam: str) -> float:
        """
        Calculate 0-100% exam readiness score.
        Syllabus Coverage 35% + PYQ Accuracy 30% + Revision 20% + Depth 15%
        """
        try:
            from sqlalchemy import select, func
            from models.user import StudentProfile, QuestionAttempt, RevisionSchedule
            from models.user import Chapter

            # This would normally query the DB — simplified here
            # In production, run actual DB aggregations
            score = 45.0  # Default placeholder — replace with real DB queries
            return min(max(score, 0.0), 100.0)
        except Exception as e:
            logger.error(f"[MemoryAgent] Readiness score error: {e}")
            return 0.0

    def _default_profile(self) -> dict:
        """Default profile for new/error cases."""
        return {
            "student_id": "",
            "name": "Student",
            "level": "AVERAGE",
            "language": "English",
            "exam_targets": [],
            "exam_dates": {},
            "weak_chapters": [],
            "learning_style": {},
            "behavioral_profile": {},
            "login_streak": 0,
            "readiness_scores": {},
        }
