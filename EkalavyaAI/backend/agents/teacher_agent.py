"""
EkalavyaAI — Agent 4: Human Teacher Simulation Agent
THE MOST CRITICAL AGENT — Claude 3.5 Sonnet ONLY (no exceptions for primary)

Responsibilities:
- Transform raw agent outputs into warm, human teacher voice
- Adapt content to student level (Weak/Average/Topper)
- Add mnemonics, analogies, exam warnings, common mistakes
- Generate exam-specific formats (ICAI for CA, shortcut for JEE, MCQ for NEET)
"""
import json
import logging
from typing import Optional

from agents.base import BaseAgent, ModelConfig
from config import settings

logger = logging.getLogger(__name__)

# ─── Teacher Persona System Prompt ──────────────────────────────────────────
TEACHER_SYSTEM_PROMPT = """You are EkalavyaAI's Master Teacher — India's best exam coach, specialized in {exam}.

## YOUR IDENTITY
- You are a real human teacher, not an AI chatbot
- 15+ years of coaching experience for {exam}
- You have personally helped thousands of students become toppers
- You know exactly what examiners look for and what trips students up

## YOUR VOICE — MANDATORY
✅ ALWAYS USE: 
- "Now here's where students get confused..."
- "Quick trick:" / "Memory tip:"
- "In the {month} {year} exam, this came for {marks} marks..."
- "Mark this in RED — examiners love asking this"
- "Don't panic when you see this in exam — here's what to do..."
- "Your teacher mistake: most students write X, but the correct approach is Y"

❌ NEVER USE (BANNED PHRASES):
- "Certainly!", "Of course!", "Absolutely!"
- "It is important to note that"
- "This is crucial" / "This is essential"
- "In conclusion" / "To summarize" / "In summary"
- "Delve into" / "Leverage" / "Utilize"
- "I hope this helps" / "Feel free to ask"

## LEVEL ADAPTATION
{level_instructions}

## EXAM FORMAT RULES
{exam_format_rules}

## ANTI-HALLUCINATION RULE
- ONLY use information from the provided context
- If you don't find information in context, say "Verify from {exam} official material"
- NEVER generate financial figures, legal provisions, or scientific values from memory
- All numerical answers must reference the provided source

## LANGUAGE
Respond in {language}. If language is Bengali/Hindi, use the language for explanations 
but keep technical terms, formula names, and legal section numbers in English.
"""

LEVEL_INSTRUCTIONS = {
    "WEAK": """
## WEAK STUDENT INSTRUCTIONS:
- Use 2-3 simple examples for every concept (real-life relatable)
- Break every complex concept into tiny steps
- Add "Simple way to remember:" before every formula/rule
- Slower pace — explain the 'why' before the 'what'
- More encouragement: "You're going to get this!"
- Avoid jargon — explain every technical term
- Add "Common mistake students make: X — DON'T do this!"
""",
    "AVERAGE": """
## AVERAGE STUDENT INSTRUCTIONS:
- Balance explanation with exam-readiness
- Give 1-2 examples per concept
- Connect new concepts to things they already know
- Flag what's important for exam vs what's background knowledge
- Add "PYQ Alert" whenever a topic has appeared in past papers
""",
    "TOPPER": """
## TOPPER STUDENT INSTRUCTIONS:
- No hand-holding — go directly to the substance
- Add advanced nuances, exceptions, inter-topic connections
- Challenge them: "A topper should be able to handle this variant..."
- Include examiner's perspective: "Why this question tests X skill"
- Connect to higher concepts and integrated application
- Add "Distinguish from:" comparisons for similar concepts
""",
}

EXAM_FORMAT_RULES = {
    "CA_FOUNDATION": """
## CA Foundation Format:
- ICAI-style: follow the Institute's recommended answer format
- For theory: Definition → Provisions → Example → Key Points
- For problems: Given → Find → Solution → Journal entries/Working notes
- Mark allocation awareness: mention marks per section
- Common mistakes in CA Foundation: write them explicitly
""",
    "CA_INTERMEDIATE": """
## CA Intermediate Format:
- More technical depth than Foundation
- Standards references (AS, Ind AS, SA numbers) must be accurate — verify from context
- Case study approach: fact identification → applicable provision → conclusion
- Inter-subject connections (Tax + Accounts, Laws + Audit)
""",
    "CA_FINAL": """
## CA Final Format:
- Advanced Ind AS, SFM, Transfer Pricing, Complex audit scenarios
- Professional skepticism and judgment emphasized
- Multiple correct approaches — present all valid methods
- ICAI Guidance Notes and Technical Guides references
""",
    "JEE": """
## JEE Format:
- Shortcut-first approach: "Long method → Short method (for exam)"
- Every numerical: show units at each step
- Important formulas highlighted in boxes
- "JEE trap:" warnings for common trick questions
- Speed optimization: which method is fastest for MCQ
- Cover both JEE Mains (MCQ) and Advanced (descriptive/paragraph) approaches
""",
    "NEET": """
## NEET Format:
- MCQ-optimized: connect every concept to how it appears in MCQ options
- NCERT-first: "As per NCERT page X..."
- Elimination strategy: "Option A is wrong because..."
- Biology: NCERT diagram descriptions with labeled parts
- Chemistry: Reaction mechanisms with arrow-pushing notation
- Physics: Same as JEE but emphasis on conceptual MCQs
""",
}


class TeacherAgent(BaseAgent):
    """
    Agent 4 — Human Teacher Simulation Agent

    Primary: Claude 3.5 Sonnet (OpenRouter) — NO EXCEPTIONS
    Backup 1: GPT-4o (OpenRouter)
    Backup 2: Gemini 1.5 Pro
    Free Fallback: Llama 3.1 70B (Groq) — quality degraded, emergency only
    """

    def __init__(self):
        fallback_chain = [
            ModelConfig(
                model=settings.TEACHER_MODEL_PRIMARY,  # claude-3-5-sonnet
                provider="openrouter",
                max_tokens=8000,
                temperature=0.4,
            ),
            ModelConfig(
                model=settings.TEACHER_MODEL_BACKUP1,  # gpt-4o
                provider="openrouter",
                max_tokens=6000,
                temperature=0.4,
            ),
            ModelConfig(
                model=settings.TEACHER_MODEL_BACKUP2,  # gemini-1.5-pro
                provider="openrouter",
                max_tokens=6000,
                temperature=0.4,
            ),
            ModelConfig(
                model=settings.TEACHER_MODEL_FREE,  # llama-3.1-70b (Groq)
                provider="groq",
                max_tokens=4000,
                temperature=0.4,
            ),
        ]
        super().__init__("TeacherAgent", fallback_chain)

    async def run(self, state: dict) -> str:
        """
        Generate human-teacher-voice educational content.
        Returns a rich, exam-quality explanation in teacher voice.
        """
        exam = state.get("exam", "CA_FOUNDATION")
        language = state.get("language", "English")
        level = state.get("student_level", "AVERAGE")
        chapter_name = state.get("chapter_name", "")
        student_name = state.get("student_name", "Student")

        # Build system prompt
        system = TEACHER_SYSTEM_PROMPT.format(
            exam=exam,
            language=language,
            level_instructions=LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS["AVERAGE"]),
            exam_format_rules=EXAM_FORMAT_RULES.get(exam, EXAM_FORMAT_RULES["CA_FOUNDATION"]),
            month="May",
            year="2024",
            marks="10",
        )

        # Build context from other agents
        research_context = self._format_research_context(state.get("research_chunks", []))
        syllabus_context = self._format_syllabus_context(state.get("syllabus_context", {}))
        pyq_context = self._format_pyq_context(state.get("pyq_patterns", {}))

        # Personalization
        weak_note = ""
        if chapter_name in state.get("weak_chapters", []):
            weak_note = f"\n⚠️ NOTE: {student_name} has struggled with this chapter before. Extra examples and simpler explanations needed.\n"

        user_message = f"""
## TEACHING TASK
Generate a complete, premium-quality chapter explanation for:
- Chapter: {chapter_name}
- Exam: {exam}
- Student Level: {level}
- Language: {language}
{weak_note}

## VERIFIED EDUCATIONAL CONTEXT (use ONLY this — do not add from memory):

### SYLLABUS STRUCTURE:
{syllabus_context}

### VERIFIED EDUCATIONAL CONTENT (from ICAI/NCERT):
{research_context}

### PYQ PATTERNS (past exam trends):
{pyq_context}

## OUTPUT REQUIREMENTS:
Generate a comprehensive teacher-voice explanation with:
1. Opening hook (why this chapter matters for exam)
2. All topics covered systematically
3. PYQ Alert boxes where relevant
4. Examples adapted to student level ({level})
5. Common mistakes section
6. Exam tips and quick tricks
7. Memory aids (mnemonics, analogies)

Format as structured markdown with clear headings.
This will be converted to premium PDF notes.
"""

        content = await self.call_with_fallback(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system,
        )

        logger.info(
            f"[TeacherAgent] Generated {len(content)} chars for "
            f"{chapter_name} | Level: {level} | Exam: {exam}"
        )
        return content

    async def solve_question(self, state: dict) -> str:
        """
        Generate an exam-appropriate answer for a student question.
        Uses ICAI format for CA, shortcut+concept for JEE, MCQ-optimized for NEET.
        """
        exam = state.get("exam", "CA_FOUNDATION")
        question = state.get("query", "")
        level = state.get("student_level", "AVERAGE")
        language = state.get("language", "English")

        research_context = self._format_research_context(state.get("research_chunks", []))
        pyq_context = self._format_pyq_context(state.get("pyq_patterns", {}))

        system = TEACHER_SYSTEM_PROMPT.format(
            exam=exam,
            language=language,
            level_instructions=LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS["AVERAGE"]),
            exam_format_rules=EXAM_FORMAT_RULES.get(exam, EXAM_FORMAT_RULES["CA_FOUNDATION"]),
            month="May", year="2024", marks="",
        )

        user_message = f"""
## STUDENT QUESTION (from {exam} student — Level: {level})
{question}

## VERIFIED CONTEXT:
{research_context}

## SIMILAR PAST EXAM QUESTIONS:
{pyq_context}

## ANSWER REQUIREMENTS:
- Answer in {exam}-appropriate format (see your format rules above)
- If this has appeared in PYQ, say: "This exact pattern appeared in [exam] [year]"
- For numerical: show each step clearly, verify all calculations
- End with: "Exam Tip:" — one key thing to remember about this type of question
- Answer in {language}
"""
        return await self.call_with_fallback(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system,
        )

    def _format_research_context(self, chunks: list) -> str:
        if not chunks:
            return "No specific context retrieved — use general knowledge for this exam."
        formatted = []
        for i, chunk in enumerate(chunks[:8], 1):
            source = chunk.get("metadata", {}).get("source", "Educational Material")
            page = chunk.get("metadata", {}).get("page", "")
            text = chunk.get("text", "")
            formatted.append(f"[Source {i} — {source} p.{page}]\n{text}")
        return "\n\n---\n\n".join(formatted)

    def _format_syllabus_context(self, syllabus: dict) -> str:
        if not syllabus:
            return "Standard syllabus structure."
        topics = syllabus.get("topics", [])
        return "\n".join(f"• {t['name']} (importance: {t.get('score', 'N/A')})"
                         for t in topics)

    def _format_pyq_context(self, pyq: dict) -> str:
        if not pyq:
            return "No PYQ data available for this chapter."
        frequency = pyq.get("frequency", 0)
        patterns = pyq.get("patterns", [])
        result = f"Appeared {frequency} times in last 10 years.\n"
        if patterns:
            result += "Common question patterns:\n"
            for p in patterns[:3]:
                result += f"• {p}\n"
        return result
