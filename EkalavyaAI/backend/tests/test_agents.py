"""Structural tests for the 7 agents and their fallback chains (no network)."""
import pytest

from config import settings
from agents.teacher_agent import TeacherAgent
from agents.syllabus_agent import SyllabusAgent
from agents.research_agent import ResearchAgent
from agents.pyq_agent import PYQAgent
from agents.notes_agent import NotesAgent
from agents.diagram_agent import DiagramAgent
from agents.memory_agent import MemoryAgent

ALL_AGENTS = [
    TeacherAgent, SyllabusAgent, ResearchAgent,
    PYQAgent, NotesAgent, DiagramAgent, MemoryAgent,
]


@pytest.mark.parametrize("AgentCls", ALL_AGENTS)
def test_agent_has_fallback_chain(AgentCls):
    agent = AgentCls()
    assert agent.name
    assert len(agent.fallback_chain) >= 1
    for mc in agent.fallback_chain:
        assert mc.model
        assert mc.provider in {"openrouter", "groq", "google", "nvidia", "anthropic"}


def test_teacher_primary_is_claude():
    """Human Teacher Agent must lead with Claude (per spec)."""
    agent = TeacherAgent()
    primary = agent.fallback_chain[0]
    assert primary.model == settings.TEACHER_MODEL_PRIMARY
    assert "claude" in primary.model.lower()


def test_memory_agent_is_groq():
    """Memory Agent runs on free/fast Groq models."""
    agent = MemoryAgent()
    assert all(mc.provider == "groq" for mc in agent.fallback_chain)


def test_teacher_has_fallback_depth():
    """Fallback chain should have multiple tiers (primary + backups/free)."""
    agent = TeacherAgent()
    assert len(agent.fallback_chain) >= 2
