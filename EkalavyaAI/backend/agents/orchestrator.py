"""
EkalavyaAI — LangGraph Orchestrator
The central brain coordinating all 7 agents via stateful graph.
Handles: Notes Generation, Question Solving, PYQ Practice
"""
import asyncio
import logging
import time
from typing import TypedDict, Annotated, Sequence, Optional, AsyncGenerator
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator

from config import settings
from agents.syllabus_agent import SyllabusAgent
from agents.research_agent import ResearchAgent
from agents.pyq_agent import PYQAgent
from agents.teacher_agent import TeacherAgent
from agents.notes_agent import NotesAgent
from agents.diagram_agent import DiagramAgent
from agents.memory_agent import MemoryAgent
from services.anti_hallucination import AntiHallucinationService
from services.cache_service import CacheService

logger = logging.getLogger(__name__)


# ─── Intent Types ────────────────────────────────────────────────────────────
class IntentType(str, Enum):
    NOTES_GENERATION = "notes_generation"
    QUESTION_SOLVING = "question_solving"
    PYQ_PRACTICE = "pyq_practice"
    GENERAL_CHAT = "general_chat"


# ─── Graph State ─────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    """Shared state object passed between all agents."""
    # ── Request Context ──
    request_id: str
    student_id: str
    intent: str
    exam: str
    subject: str
    chapter_id: Optional[str]
    chapter_name: str
    language: str
    query: Optional[str]

    # ── Student Context (from Memory Agent) ──
    student_level: str  # WEAK | AVERAGE | TOPPER
    student_name: str
    weak_chapters: list
    exam_date: Optional[str]
    behavioral_profile: dict

    # ── Agent Outputs ──
    syllabus_context: dict       # From Syllabus Agent
    research_chunks: list        # From Research Agent (top-8 chunks)
    pyq_patterns: dict           # From PYQ Agent
    teacher_content: str         # From Teacher Agent (Claude 3.5 Sonnet)
    structured_notes: dict       # From Notes Agent
    diagrams: list               # From Diagram Agent (SVGs)

    # ── Quality Control ──
    confidence_score: float
    hallucination_flags: list
    needs_expert_review: bool
    citations: list

    # ── Output ──
    pdf_url: Optional[str]
    docx_url: Optional[str]
    stream_chunks: Annotated[list, operator.add]  # Accumulated stream output

    # ── Meta ──
    agent_timings: dict
    errors: list
    cache_hit: bool
    start_time: float
    has_numerical: bool


# ─── Orchestrator ────────────────────────────────────────────────────────────
class EkalavyaOrchestrator:
    """
    LangGraph-based orchestrator for the 7-agent EkalavyaAI system.
    Manages stateful multi-agent coordination with parallel execution.
    """

    def __init__(self):
        self.syllabus_agent = SyllabusAgent()
        self.research_agent = ResearchAgent()
        self.pyq_agent = PYQAgent()
        self.teacher_agent = TeacherAgent()
        self.notes_agent = NotesAgent()
        self.diagram_agent = DiagramAgent()
        self.memory_agent = MemoryAgent()
        self.anti_hallucination = AntiHallucinationService()
        self.cache_service = CacheService()

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        graph = StateGraph(AgentState)

        # ── Add Nodes ──
        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("check_cache", self._check_cache)
        graph.add_node("memory_read", self._memory_read)
        graph.add_node("parallel_agents", self._run_parallel_agents)
        graph.add_node("teacher_agent", self._run_teacher_agent)
        graph.add_node("notes_agent", self._run_notes_agent)
        graph.add_node("diagram_agent", self._run_diagram_agent)
        graph.add_node("anti_hallucination", self._run_anti_hallucination)
        graph.add_node("generate_pdf", self._generate_pdf)
        graph.add_node("memory_write", self._memory_write)
        graph.add_node("question_solve", self._question_solve)
        graph.add_node("general_chat", self._general_chat)
        graph.add_node("serve_cache", self._serve_from_cache)

        # ── Entry Point ──
        graph.set_entry_point("classify_intent")

        # ── Routing Logic ──
        graph.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "notes": "check_cache",
                "question": "memory_read",
                "general": "general_chat",
            },
        )

        # ── Notes Generation Flow ──
        graph.add_conditional_edges(
            "check_cache",
            self._route_cache,
            {
                "cache_hit": "serve_cache",
                "cache_miss": "memory_read",
            },
        )
        graph.add_edge("memory_read", "parallel_agents")
        graph.add_edge("parallel_agents", "teacher_agent")
        graph.add_edge("teacher_agent", "notes_agent")
        graph.add_edge("notes_agent", "diagram_agent")
        graph.add_edge("diagram_agent", "anti_hallucination")
        graph.add_conditional_edges(
            "anti_hallucination",
            self._route_quality,
            {
                "approved": "generate_pdf",
                "needs_review": "generate_pdf",  # Generate anyway, flag for review
            },
        )
        graph.add_edge("generate_pdf", "memory_write")
        graph.add_edge("memory_write", END)

        # ── Question/Chat Flows ──
        graph.add_edge("question_solve", "memory_write")
        graph.add_edge("general_chat", END)
        graph.add_edge("serve_cache", "memory_write")

        return graph.compile(checkpointer=MemorySaver())

    # ─── Node Implementations ─────────────────────────────────────────────────

    async def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify student request intent."""
        t = time.time()
        intent = state.get("intent", IntentType.GENERAL_CHAT)
        logger.info(f"[{state['request_id']}] Intent: {intent}")
        state["agent_timings"]["classify"] = time.time() - t
        return state

    async def _check_cache(self, state: AgentState) -> AgentState:
        """Check master notes cache before running agents."""
        t = time.time()
        cache_key = self.cache_service.build_key(
            state["exam"], state["subject"], state["chapter_id"], state["language"]
        )
        cached = await self.cache_service.get_master_cache(cache_key)
        if cached:
            state["cache_hit"] = True
            state["structured_notes"] = cached["content_json"]
            state["pdf_url"] = cached["pdf_url"]
            logger.info(f"[{state['request_id']}] Cache HIT: {cache_key}")
        else:
            state["cache_hit"] = False
            logger.info(f"[{state['request_id']}] Cache MISS: {cache_key}")
        state["agent_timings"]["cache_check"] = time.time() - t
        return state

    async def _memory_read(self, state: AgentState) -> AgentState:
        """Read student memory and inject personalization context."""
        t = time.time()
        memory = await self.memory_agent.read_student_profile(state["student_id"])
        state.update({
            "student_level": memory.get("level", "AVERAGE"),
            "student_name": memory.get("name", "Student"),
            "weak_chapters": memory.get("weak_chapters", []),
            "exam_date": memory.get("exam_date"),
            "behavioral_profile": memory.get("behavioral_profile", {}),
        })
        logger.info(
            f"[{state['request_id']}] Memory loaded | "
            f"Level: {state['student_level']} | "
            f"Weak chapters: {len(state['weak_chapters'])}"
        )
        state["agent_timings"]["memory_read"] = time.time() - t
        return state

    async def _run_parallel_agents(self, state: AgentState) -> AgentState:
        """Run Syllabus, Research, and PYQ agents in parallel (~3s)."""
        t = time.time()
        logger.info(f"[{state['request_id']}] Starting parallel agents")

        syllabus_task = self.syllabus_agent.run(state)
        research_task = self.research_agent.run(state)
        pyq_task = self.pyq_agent.run(state)

        results = await asyncio.gather(
            syllabus_task, research_task, pyq_task,
            return_exceptions=True
        )

        # Handle individual agent failures gracefully
        syllabus_result, research_result, pyq_result = results

        if not isinstance(syllabus_result, Exception):
            state["syllabus_context"] = syllabus_result
        else:
            logger.warning(f"Syllabus agent failed: {syllabus_result}")
            state["syllabus_context"] = {}

        if not isinstance(research_result, Exception):
            state["research_chunks"] = research_result
        else:
            logger.warning(f"Research agent failed: {research_result}")
            state["research_chunks"] = []

        if not isinstance(pyq_result, Exception):
            state["pyq_patterns"] = pyq_result
        else:
            logger.warning(f"PYQ agent failed: {pyq_result}")
            state["pyq_patterns"] = {}

        elapsed = time.time() - t
        state["agent_timings"]["parallel_agents"] = elapsed
        logger.info(f"[{state['request_id']}] Parallel agents done in {elapsed:.2f}s")
        return state

    async def _run_teacher_agent(self, state: AgentState) -> AgentState:
        """Run Teacher Agent (Claude 3.5 Sonnet) — most critical step."""
        t = time.time()
        logger.info(f"[{state['request_id']}] Teacher Agent (Claude) starting")
        state["teacher_content"] = await self.teacher_agent.run(state)
        state["agent_timings"]["teacher"] = time.time() - t
        return state

    async def _run_notes_agent(self, state: AgentState) -> AgentState:
        """Structure teacher content into premium notes format."""
        t = time.time()
        state["structured_notes"] = await self.notes_agent.run(state)
        state["agent_timings"]["notes"] = time.time() - t
        return state

    async def _run_diagram_agent(self, state: AgentState) -> AgentState:
        """Detect visual triggers and generate SVG diagrams."""
        t = time.time()
        state["diagrams"] = await self.diagram_agent.run(state)
        state["agent_timings"]["diagrams"] = time.time() - t
        return state

    async def _run_anti_hallucination(self, state: AgentState) -> AgentState:
        """Run 5-layer anti-hallucination validation."""
        t = time.time()
        result = await self.anti_hallucination.validate(state)
        state["confidence_score"] = result["confidence_score"]
        state["hallucination_flags"] = result["flags"]
        state["needs_expert_review"] = result["needs_review"]
        state["citations"] = result["citations"]
        state["agent_timings"]["anti_hallucination"] = time.time() - t
        logger.info(
            f"[{state['request_id']}] Anti-hallucination: "
            f"confidence={result['confidence_score']:.2f} "
            f"review_needed={result['needs_review']}"
        )
        return state

    async def _generate_pdf(self, state: AgentState) -> AgentState:
        """Generate premium PDF and DOCX notes."""
        t = time.time()
        from services.pdf_generator import PDFGenerator
        pdf_gen = PDFGenerator()

        pdf_url, docx_url = await pdf_gen.generate(
            notes=state["structured_notes"],
            diagrams=state["diagrams"],
            student_name=state["student_name"],
            chapter_name=state["chapter_name"],
            exam=state["exam"],
            language=state["language"],
        )
        state["pdf_url"] = pdf_url
        state["docx_url"] = docx_url

        # Save to master cache
        await self.cache_service.set_master_cache(
            exam=state["exam"],
            subject=state["subject"],
            chapter_id=state["chapter_id"],
            language=state["language"],
            content_json=state["structured_notes"],
            pdf_url=pdf_url,
        )

        state["agent_timings"]["pdf_generation"] = time.time() - t
        return state

    async def _memory_write(self, state: AgentState) -> AgentState:
        """Update student memory, revision schedule, and progress."""
        t = time.time()
        await self.memory_agent.update_student_profile(
            student_id=state["student_id"],
            session_data={
                "chapter_studied": state.get("chapter_id"),
                "topics_covered": state.get("syllabus_context", {}).get("topics", []),
                "level": state["student_level"],
                "weak_chapters": state["weak_chapters"],
                "agent_timings": state["agent_timings"],
            }
        )
        state["agent_timings"]["memory_write"] = time.time() - t
        return state

    async def _question_solve(self, state: AgentState) -> AgentState:
        """Solve a student question with exam-appropriate format."""
        # Run PYQ + Memory in parallel
        pyq_result, memory_data = await asyncio.gather(
            self.pyq_agent.run(state),
            self.memory_agent.read_student_profile(state["student_id"]),
        )
        state["pyq_patterns"] = pyq_result
        state["student_level"] = memory_data.get("level", "AVERAGE")

        # Teacher agent generates exam-style answer
        state["teacher_content"] = await self.teacher_agent.solve_question(state)

        # Verify calculations if numerical
        if state.get("has_numerical"):
            try:
                from services.code_interpreter import CodeInterpreter
                state["teacher_content"] = await CodeInterpreter().verify_numericals(
                    state["teacher_content"]
                )
            except Exception as e:
                logger.warning(f"Code interpreter failed: {e}")

        # Diagram if needed
        state["diagrams"] = await self.diagram_agent.run(state)
        return state

    async def _general_chat(self, state: AgentState) -> AgentState:
        """Direct Groq Llama response for general questions — no agent overhead."""
        from utils.model_router import ModelRouter
        router = ModelRouter()
        response = await router.call_groq(
            model=settings.GENERAL_CHAT_MODEL,
            messages=[{"role": "user", "content": state["query"]}],
            system="You are EkalavyaAI, a helpful education assistant. "
                   "Answer student questions clearly and concisely.",
        )
        state["stream_chunks"].append({"type": "text", "content": response})
        return state

    async def _serve_from_cache(self, state: AgentState) -> AgentState:
        """Serve cached notes with personalization layer."""
        logger.info(f"[{state['request_id']}] Serving from master cache")

        # Add personalization via small Groq call
        personalization = await self.memory_agent.get_personalization_prefix(
            student_id=state["student_id"],
            cached_notes=state["structured_notes"],
            level=state["student_level"],
        )
        state["structured_notes"]["personalization"] = personalization
        state["cache_hit"] = True
        return state

    # ─── Routing Functions ────────────────────────────────────────────────────

    def _route_by_intent(self, state: AgentState) -> str:
        intent = state.get("intent", "general")
        if intent == IntentType.NOTES_GENERATION:
            return "notes"
        elif intent in (IntentType.QUESTION_SOLVING, IntentType.PYQ_PRACTICE):
            return "question"
        return "general"

    def _route_cache(self, state: AgentState) -> str:
        return "cache_hit" if state.get("cache_hit") else "cache_miss"

    def _route_quality(self, state: AgentState) -> str:
        if state.get("needs_expert_review"):
            # Queue for expert review (async) but still serve student
            asyncio.create_task(
                self._queue_expert_review(state)
            )
        return "approved"

    async def _queue_expert_review(self, state: AgentState):
        """Queue low-confidence content for expert verification."""
        from tasks.celery_app import celery_app
        celery_app.send_task(
            "tasks.expert_review_task",
            kwargs={
                "chapter_id": state.get("chapter_id"),
                "content_json": state.get("structured_notes"),
                "flags": state.get("hallucination_flags"),
                "confidence": state.get("confidence_score"),
            }
        )

    # ─── Public Interface ─────────────────────────────────────────────────────

    async def generate_notes(
        self,
        student_id: str,
        exam: str,
        subject: str,
        chapter_id: str,
        chapter_name: str,
        language: str = "English",
        request_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Main entry point for notes generation.
        Yields stream chunks as they're produced.
        """
        import uuid as _uuid
        req_id = request_id or str(_uuid.uuid4())[:8]

        initial_state: AgentState = {
            "request_id": req_id,
            "student_id": student_id,
            "intent": IntentType.NOTES_GENERATION,
            "exam": exam,
            "subject": subject,
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
            "language": language,
            "query": None,
            "student_level": "AVERAGE",
            "student_name": "Student",
            "weak_chapters": [],
            "exam_date": None,
            "behavioral_profile": {},
            "syllabus_context": {},
            "research_chunks": [],
            "pyq_patterns": {},
            "teacher_content": "",
            "structured_notes": {},
            "diagrams": [],
            "confidence_score": 0.0,
            "hallucination_flags": [],
            "needs_expert_review": False,
            "citations": [],
            "pdf_url": None,
            "docx_url": None,
            "stream_chunks": [],
            "agent_timings": {},
            "errors": [],
            "cache_hit": False,
            "start_time": time.time(),
        }

        config = {"configurable": {"thread_id": f"{student_id}:{req_id}"}}

        async for chunk in self.graph.astream(initial_state, config=config):
            for node_name, node_state in chunk.items():
                if node_state.get("stream_chunks"):
                    for stream_chunk in node_state["stream_chunks"]:
                        yield stream_chunk

        # Yield final result
        final_state = await self.graph.aget_state(config)
        if final_state.values:
            yield {
                "type": "complete",
                "pdf_url": final_state.values.get("pdf_url"),
                "docx_url": final_state.values.get("docx_url"),
                "confidence": final_state.values.get("confidence_score"),
                "from_cache": final_state.values.get("cache_hit"),
                "timing_ms": int((time.time() - initial_state["start_time"]) * 1000),
            }

    async def solve_question(
        self,
        student_id: str,
        question: str,
        exam: str,
        chapter_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Entry point for question solving."""
        import uuid as _uuid
        req_id = str(_uuid.uuid4())[:8]

        initial_state: AgentState = {
            "request_id": req_id,
            "student_id": student_id,
            "intent": IntentType.QUESTION_SOLVING,
            "exam": exam,
            "subject": "",
            "chapter_id": chapter_id,
            "chapter_name": "",
            "language": "English",
            "query": question,
            "student_level": "AVERAGE",
            "student_name": "Student",
            "weak_chapters": [],
            "exam_date": None,
            "behavioral_profile": {},
            "syllabus_context": {},
            "research_chunks": [],
            "pyq_patterns": {},
            "teacher_content": "",
            "structured_notes": {},
            "diagrams": [],
            "confidence_score": 0.0,
            "hallucination_flags": [],
            "needs_expert_review": False,
            "citations": [],
            "pdf_url": None,
            "docx_url": None,
            "stream_chunks": [],
            "agent_timings": {},
            "errors": [],
            "cache_hit": False,
            "start_time": time.time(),
            "has_numerical": any(
                char.isdigit() for char in question
            ),
        }

        config = {"configurable": {"thread_id": f"{student_id}:{req_id}"}}
        async for chunk in self.graph.astream(initial_state, config=config):
            for node_name, node_state in chunk.items():
                for stream_chunk in node_state.get("stream_chunks", []):
                    yield stream_chunk


# ─── Singleton ───────────────────────────────────────────────────────────────
_orchestrator: Optional[EkalavyaOrchestrator] = None


def get_orchestrator() -> EkalavyaOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EkalavyaOrchestrator()
    return _orchestrator
