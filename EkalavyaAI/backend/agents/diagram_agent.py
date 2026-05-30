"""
EkalavyaAI — Agent 6: Diagram Generation Agent
Generates inline SVG diagrams for educational content.

Exam-specific diagrams:
- CA: T-Accounts, Cash Flow diagrams, Journal Entry layouts, Balance Sheet format
- JEE: Circuit diagrams, Physics force diagrams, Math function plots, Chemistry structures
- NEET: Cell diagrams, Heart anatomy, Plant cell cross-sections, Food chains
"""
import logging
import re
from typing import List

from agents.base import BaseAgent, ModelConfig
from config import settings

logger = logging.getLogger(__name__)

# Visual triggers per exam type
VISUAL_TRIGGERS = {
    "CA_FOUNDATION": [
        "T-account", "journal entry", "ledger", "trial balance", "balance sheet",
        "cash flow", "ratio analysis", "depreciation", "partnership", "sole proprietor",
    ],
    "CA_INTERMEDIATE": [
        "consolidated", "amalgamation", "AS ", "Ind AS", "deferred tax",
        "segment", "cash flow statement", "financial instruments",
    ],
    "CA_FINAL": [
        "Ind AS", "IFRS", "consolidation", "forex", "hedge", "derivative",
    ],
    "JEE": [
        "circuit", "force diagram", "projectile", "wave", "lens", "prism",
        "organic mechanism", "titration", "crystal structure", "function graph",
        "integration", "differentiation", "vector",
    ],
    "NEET": [
        "cell", "mitosis", "meiosis", "heart", "kidney", "neuron",
        "photosynthesis", "respiration", "digestive", "plant",
        "chromosome", "DNA", "RNA", "enzyme",
    ],
}


class DiagramAgent(BaseAgent):
    """
    Agent 6 — SVG Diagram Generation Agent

    Primary: Claude 3.5 Sonnet (best SVG generation)
    Backup 1: GPT-4o
    Backup 2: Gemini 1.5 Flash
    Free Fallback: Llama 3.1 70B (Groq) — simpler diagrams
    """

    def __init__(self):
        fallback_chain = [
            ModelConfig(
                model=settings.DIAGRAM_MODEL_PRIMARY,
                provider="openrouter",
                max_tokens=6000,
                temperature=0.3,
            ),
            ModelConfig(
                model="openai/gpt-4o",
                provider="openrouter",
                max_tokens=4000,
                temperature=0.3,
            ),
            ModelConfig(
                model="google/gemini-flash-1.5",
                provider="openrouter",
                max_tokens=4000,
                temperature=0.3,
            ),
            ModelConfig(
                model="llama-3.1-70b-versatile",
                provider="groq",
                max_tokens=3000,
                temperature=0.3,
            ),
        ]
        super().__init__("DiagramAgent", fallback_chain)

    async def run(self, state: dict) -> List[dict]:
        """
        Detect visual triggers in notes and generate SVG diagrams.
        Returns list of diagram objects with SVG code and placement info.
        """
        exam = state.get("exam", "CA_FOUNDATION")
        teacher_content = state.get("teacher_content", "")
        structured_notes = state.get("structured_notes", {})
        chapter_name = state.get("chapter_name", "")

        # Detect which diagrams are needed
        triggers = self._detect_triggers(teacher_content, exam)

        if not triggers:
            logger.info(f"[DiagramAgent] No visual triggers found for {chapter_name}")
            return []

        logger.info(f"[DiagramAgent] Found {len(triggers)} diagram triggers: {triggers}")

        # Generate diagrams (max 3 per chapter to control token usage)
        diagrams = []
        for trigger in triggers[:3]:
            diagram = await self._generate_diagram(trigger, exam, chapter_name)
            if diagram:
                diagrams.append(diagram)

        logger.info(f"[DiagramAgent] Generated {len(diagrams)} diagrams")
        return diagrams

    def _detect_triggers(self, content: str, exam: str) -> List[str]:
        """Detect visual trigger keywords in teacher content."""
        content_lower = content.lower()
        triggers = VISUAL_TRIGGERS.get(exam, [])
        found = []

        for trigger in triggers:
            if trigger.lower() in content_lower:
                found.append(trigger)

        return found[:5]  # Max 5 triggers detected

    async def _generate_diagram(
        self, trigger: str, exam: str, chapter_name: str
    ) -> dict:
        """Generate a single SVG diagram for a trigger."""
        diagram_type = self._classify_diagram_type(trigger, exam)
        prompt = self._build_diagram_prompt(trigger, diagram_type, exam, chapter_name)

        try:
            svg_response = await self.call_with_fallback(
                messages=[{"role": "user", "content": prompt}],
            )

            svg_code = self._extract_svg(svg_response)
            if not svg_code:
                return None

            return {
                "trigger": trigger,
                "type": diagram_type,
                "title": f"{trigger.title()} Diagram",
                "svg": svg_code,
                "placement": "after_concept",  # where to place in notes
            }
        except Exception as e:
            logger.error(f"[DiagramAgent] SVG generation failed for {trigger}: {e}")
            return None

    def _classify_diagram_type(self, trigger: str, exam: str) -> str:
        """Classify the type of diagram needed."""
        trigger_lower = trigger.lower()
        if any(t in trigger_lower for t in ["t-account", "ledger", "journal"]):
            return "accounting_entry"
        elif any(t in trigger_lower for t in ["balance sheet", "cash flow"]):
            return "financial_statement"
        elif any(t in trigger_lower for t in ["circuit", "force", "wave"]):
            return "physics_diagram"
        elif any(t in trigger_lower for t in ["cell", "heart", "neuron", "kidney"]):
            return "biology_diagram"
        elif any(t in trigger_lower for t in ["organic", "titration", "crystal"]):
            return "chemistry_diagram"
        elif any(t in trigger_lower for t in ["function", "graph", "vector"]):
            return "math_diagram"
        return "concept_diagram"

    def _build_diagram_prompt(
        self, trigger: str, diagram_type: str, exam: str, chapter_name: str
    ) -> str:
        """Build specific prompt for each diagram type."""
        base = f"Generate an educational SVG diagram for '{trigger}' from {exam} {chapter_name}."
        style = """
SVG Requirements:
- viewBox="0 0 500 350" 
- Clean white background (rect fill="#ffffff")
- Professional fonts: font-family="Arial, sans-serif"
- Clear labels with font-size 12-14px
- Colors: #1e40af (blue) for main elements, #d97706 (amber) for highlights, #065f46 (green) for values
- Rounded rectangles (rx="6") for boxes
- 2px strokes for lines
- Return ONLY the SVG code starting with <svg and ending with </svg>
- No markdown, no explanation, just the SVG
"""
        type_specific = {
            "accounting_entry": """
T-Account format:
- Two columns: Debit (left) and Credit (right)
- Account name at top center
- Header row: Dr | Cr
- Sample entries with amounts
- Total line at bottom
""",
            "financial_statement": """
Clean table format:
- Proper financial statement structure
- Indented sub-items
- Total rows clearly marked
- ₹ symbols for amounts
""",
            "biology_diagram": """
Simple labeled anatomy diagram:
- Clear outline shapes
- Labeled arrows pointing to parts
- Color-coded regions
- Title at top
""",
            "physics_diagram": """
Physics diagram:
- Clear force arrows with labels
- Coordinate axes if needed
- Angle markings
- Component labels
""",
            "math_diagram": """
Mathematical graph:
- Coordinate axes with labels
- Function curves
- Key points marked
- Grid lines (light gray)
""",
        }

        specific = type_specific.get(diagram_type, "Educational diagram with clear labels.")
        return f"{base}\n\nDiagram type: {diagram_type}\n{specific}\n{style}"

    def _extract_svg(self, response: str) -> str:
        """Extract SVG code from model response."""
        response = response.strip()

        # Direct SVG response
        if response.startswith("<svg"):
            end = response.rfind("</svg>")
            if end != -1:
                return response[:end + 6]

        # SVG in code block
        svg_match = re.search(r"<svg[\s\S]*?</svg>", response, re.IGNORECASE)
        if svg_match:
            return svg_match.group(0)

        return ""
