"""
EkalavyaAI — Agent 5: Notes Formatting Agent
Takes teacher content and structures it into premium exam-ready notes format.

Responsibilities:
- Parse teacher content into structured JSON schema
- Add metadata (chapter info, PYQ alerts, importance markers)
- Prepare notes structure for PDF/DOCX rendering
- Handle multi-language content formatting
"""
import json
import logging

from agents.base import BaseAgent, ModelConfig
from config import settings

logger = logging.getLogger(__name__)

# ─── Notes JSON Schema ───────────────────────────────────────────────────────
NOTES_SCHEMA = {
    "chapter_name": "string",
    "exam": "string",
    "subject": "string",
    "language": "string",
    "total_pages_estimate": "int",
    "sections": [
        {
            "type": "opening_hook",
            "title": "Why This Chapter Matters",
            "content": "string"
        },
        {
            "type": "topic",
            "title": "Topic Title",
            "content": "string",
            "importance": "HIGH|MEDIUM|LOW",
            "pyq_alert": "string or null",
            "formulas": ["Formula 1"],
            "memory_tips": ["Mnemonic 1"],
            "examples": [{"title": "Example 1", "content": "..."}],
            "diagrams": []
        },
        {
            "type": "common_mistakes",
            "title": "Common Mistakes to Avoid",
            "content": "string",
            "mistakes": ["Mistake 1"]
        },
        {
            "type": "exam_tips",
            "title": "Exam Tips & Quick Tricks",
            "content": "string",
            "tips": ["Tip 1"]
        },
        {
            "type": "summary",
            "title": "Quick Revision Summary",
            "points": ["Point 1"]
        }
    ],
    "metadata": {
        "total_topics": "int",
        "pyq_frequency": "int",
        "importance_score": "float",
        "estimated_exam_marks": "int",
        "revision_priority": "HIGH|MEDIUM|LOW"
    }
}


class NotesAgent(BaseAgent):
    """
    Agent 5 — Notes Formatting Agent

    Primary: Claude 3.5 Sonnet (best structured output)
    Backup 1: GPT-4o
    Backup 2: Gemini 1.5 Flash
    Free Fallback: Llama 3.1 70B (Groq)
    """

    def __init__(self):
        fallback_chain = [
            ModelConfig(
                model=settings.NOTES_MODEL_PRIMARY,
                provider="openrouter",
                max_tokens=8000,
                temperature=0.2,
            ),
            ModelConfig(
                model="openai/gpt-4o",
                provider="openrouter",
                max_tokens=6000,
                temperature=0.2,
            ),
            ModelConfig(
                model="google/gemini-flash-1.5",
                provider="openrouter",
                max_tokens=6000,
                temperature=0.2,
            ),
            ModelConfig(
                model="llama-3.1-70b-versatile",
                provider="groq",
                max_tokens=4000,
                temperature=0.2,
            ),
        ]
        super().__init__("NotesAgent", fallback_chain)

    async def run(self, state: dict) -> dict:
        """
        Convert teacher content into structured notes JSON.
        This JSON is used by PDF generator and frontend renderer.
        """
        teacher_content = state.get("teacher_content", "")
        chapter_name = state.get("chapter_name", "")
        exam = state.get("exam", "CA_FOUNDATION")
        subject = state.get("subject", "")
        language = state.get("language", "English")
        pyq_patterns = state.get("pyq_patterns", {})
        syllabus_context = state.get("syllabus_context", {})

        logger.info(f"[NotesAgent] Structuring notes for {chapter_name}")

        if not teacher_content:
            logger.error("[NotesAgent] No teacher content to structure!")
            return self._empty_notes(chapter_name, exam, subject, language)

        prompt = f"""
Convert this educational content into a structured notes JSON.

Chapter: {chapter_name}
Exam: {exam}
Subject: {subject}
Language: {language}

PYQ Info:
- Frequency: {pyq_patterns.get('frequency', 0)} times in last 10 years
- High probability topics: {pyq_patterns.get('high_probability_topics', [])}

Importance Score: {syllabus_context.get('importance_score', 0.7)}

TEACHER CONTENT TO STRUCTURE:
{teacher_content}

Return ONLY valid JSON following this schema exactly:
{json.dumps(NOTES_SCHEMA, indent=2)}

Rules:
1. Preserve ALL educational content — don't lose any explanation
2. Mark topics as HIGH/MEDIUM/LOW importance based on PYQ frequency
3. Add "pyq_alert" strings where topics have appeared in exams
4. Extract all formulas, memory tips, examples into their arrays
5. "sections" should have one entry per major topic
6. Ensure content is in {language} language
7. Return ONLY the JSON, no markdown fences
"""

        try:
            response = await self.call_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                json_mode=True,
            )
            structured = self._parse_and_validate(response)
            structured["chapter_name"] = chapter_name
            structured["exam"] = exam
            structured["subject"] = subject
            structured["language"] = language

            logger.info(
                f"[NotesAgent] Structured {len(structured.get('sections', []))} sections"
            )
            return structured

        except Exception as e:
            logger.error(f"[NotesAgent] Structuring failed: {e}")
            # Return basic structure with raw content
            return {
                "chapter_name": chapter_name,
                "exam": exam,
                "subject": subject,
                "language": language,
                "sections": [
                    {
                        "type": "topic",
                        "title": chapter_name,
                        "content": teacher_content,
                        "importance": "HIGH",
                    }
                ],
                "metadata": {
                    "total_topics": 1,
                    "pyq_frequency": pyq_patterns.get("frequency", 0),
                    "importance_score": 0.7,
                    "estimated_exam_marks": 10,
                    "revision_priority": "HIGH",
                },
            }

    def _parse_and_validate(self, response: str) -> dict:
        """Parse and validate JSON response."""
        clean = response.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1])
        parsed = json.loads(clean)
        # Ensure required fields
        if "sections" not in parsed:
            parsed["sections"] = []
        if "metadata" not in parsed:
            parsed["metadata"] = {}
        return parsed

    def _empty_notes(
        self, chapter_name: str, exam: str, subject: str, language: str
    ) -> dict:
        return {
            "chapter_name": chapter_name,
            "exam": exam,
            "subject": subject,
            "language": language,
            "sections": [],
            "metadata": {
                "total_topics": 0,
                "pyq_frequency": 0,
                "importance_score": 0.5,
                "estimated_exam_marks": 0,
                "revision_priority": "MEDIUM",
            },
        }
