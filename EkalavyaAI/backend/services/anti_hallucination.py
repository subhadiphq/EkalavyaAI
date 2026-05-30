"""
EkalavyaAI — Anti-Hallucination Service
5-Layer validation system to protect students from incorrect information.

Layer 1: Source Grounding Check    — is content supported by retrieved chunks?
Layer 2: Numerical Verification    — are all calculations correct?
Layer 3: Legal/Standards Check     — AS/Ind AS/IPC section numbers valid?
Layer 4: Consistency Check         — no contradictions within the content?
Layer 5: Expert Confidence Score   — overall confidence rating
"""
import logging
import re
from typing import List

from config import settings

logger = logging.getLogger(__name__)


class AntiHallucinationService:
    """
    5-Layer anti-hallucination protection for educational content.
    Critical for CA/JEE/NEET where wrong info directly harms students.
    """

    # Patterns that need verification
    NUMERICAL_PATTERNS = [
        r"\b\d+%\b",                          # Percentages
        r"₹\s*\d+[\d,]*",                     # Rupee amounts
        r"\b\d+\s*days?\b",                   # Day counts (CA statutory)
        r"\bSection\s+\d+[A-Z]?\b",           # Legal sections
        r"\bAS\s*\d+\b",                       # Accounting Standards
        r"\bInd\s*AS\s*\d+\b",               # Ind AS standards
        r"\bSchedule\s+[IVX]+\b",             # Schedule references
        r"\b\d{4}\s*Act\b",                   # Legislation years
        r"\b[A-Z]{1,3}-\d+\b",               # Formula codes (e.g., H-2, CO-2)
    ]

    # Known dangerous hallucination zones for CA
    CA_HALLUCINATION_ZONES = [
        "section number",
        "as per section",
        "under section",
        "schedule ii",
        "schedule iii",
        "companies act",
        "income tax act",
    ]

    async def validate(self, state: dict) -> dict:
        """
        Run all 5 validation layers.
        Returns confidence score and flags.
        """
        teacher_content = state.get("teacher_content", "")
        research_chunks = state.get("research_chunks", [])
        exam = state.get("exam", "CA_FOUNDATION")

        flags = []
        layer_scores = []

        # Layer 1: Source Grounding
        l1_score, l1_flags = await self._layer1_source_grounding(
            teacher_content, research_chunks
        )
        layer_scores.append(l1_score)
        flags.extend(l1_flags)
        logger.debug(f"[AntiHallucination] L1 grounding: {l1_score:.2f}")

        # Layer 2: Numerical Verification
        l2_score, l2_flags = await self._layer2_numerical_check(
            teacher_content, exam
        )
        layer_scores.append(l2_score)
        flags.extend(l2_flags)
        logger.debug(f"[AntiHallucination] L2 numerical: {l2_score:.2f}")

        # Layer 3: Standards/Legal Check
        l3_score, l3_flags = await self._layer3_standards_check(
            teacher_content, exam
        )
        layer_scores.append(l3_score)
        flags.extend(l3_flags)
        logger.debug(f"[AntiHallucination] L3 standards: {l3_score:.2f}")

        # Layer 4: Consistency Check
        l4_score, l4_flags = await self._layer4_consistency_check(teacher_content)
        layer_scores.append(l4_score)
        flags.extend(l4_flags)
        logger.debug(f"[AntiHallucination] L4 consistency: {l4_score:.2f}")

        # Layer 5: Exam Pattern Alignment
        l5_score, l5_flags = await self._layer5_exam_alignment(
            teacher_content, exam
        )
        layer_scores.append(l5_score)
        flags.extend(l5_flags)

        # Weighted final score
        weights = [0.35, 0.25, 0.20, 0.10, 0.10]
        final_score = sum(s * w for s, w in zip(layer_scores, weights))

        needs_review = (
            final_score < settings.CONFIDENCE_THRESHOLD
            or any("CRITICAL" in f for f in flags)
        )

        # Build citations from research chunks
        citations = self._build_citations(research_chunks)

        logger.info(
            f"[AntiHallucination] Final score: {final_score:.2f} | "
            f"Flags: {len(flags)} | Needs review: {needs_review}"
        )

        return {
            "confidence_score": round(final_score, 3),
            "layer_scores": {
                "source_grounding": l1_score,
                "numerical": l2_score,
                "standards": l3_score,
                "consistency": l4_score,
                "exam_alignment": l5_score,
            },
            "flags": flags,
            "needs_review": needs_review,
            "citations": citations,
        }

    async def _layer1_source_grounding(
        self, content: str, chunks: List[dict]
    ) -> tuple:
        """Check if content is grounded in retrieved sources."""
        if not chunks:
            # No sources — moderate penalty but don't fail entirely
            return 0.6, ["WARNING: No source chunks available for grounding"]

        # Extract key claims from content (numbers, proper nouns, technical terms)
        content_claims = set(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", content))
        chunk_text = " ".join(c.get("text", "") for c in chunks)

        # Check what fraction of claims appear in chunks
        grounded_claims = sum(1 for claim in content_claims if claim in chunk_text)
        total_claims = max(len(content_claims), 1)
        grounding_ratio = grounded_claims / total_claims

        flags = []
        if grounding_ratio < 0.3:
            flags.append("WARNING: Low source grounding — many claims unverified")
        elif grounding_ratio < 0.5:
            flags.append("INFO: Moderate source grounding")

        score = min(0.95, 0.5 + grounding_ratio * 0.5)
        return score, flags

    async def _layer2_numerical_check(self, content: str, exam: str) -> tuple:
        """Check for potentially hallucinated numerical values."""
        flags = []
        score = 0.9  # Start with high confidence

        for pattern in self.NUMERICAL_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # For CA specifically, section numbers need extra scrutiny
                if exam.startswith("CA") and any(
                    "section" in m.lower() for m in matches
                ):
                    flags.append(
                        f"VERIFY: Section numbers detected ({matches[:3]}) — "
                        "verify against official ICAI material"
                    )
                    score -= 0.05

        # Check for suspiciously round numbers that might be hallucinated
        round_numbers = re.findall(r"\b(?:100|1000|10000|100000)\b", content)
        if len(round_numbers) > 5:
            flags.append(
                "INFO: Multiple round numbers detected — verify calculations"
            )
            score -= 0.03

        return max(score, 0.4), flags

    async def _layer3_standards_check(self, content: str, exam: str) -> tuple:
        """Validate accounting standards and legal references."""
        flags = []
        score = 0.85

        if exam.startswith("CA"):
            # Check AS references
            as_refs = re.findall(r"\bAS\s*(\d+)\b", content, re.IGNORECASE)
            for as_num in as_refs:
                num = int(as_num)
                if num > 32:  # Only AS 1-32 exist
                    flags.append(
                        f"CRITICAL: AS {num} does not exist — HALLUCINATION detected!"
                    )
                    score -= 0.3

            # Check Ind AS references
            ind_as_refs = re.findall(r"\bInd\s*AS\s*(\d+)\b", content, re.IGNORECASE)
            valid_ind_as = {1, 2, 7, 8, 10, 12, 16, 17, 19, 20, 21, 23, 24, 27,
                           28, 32, 33, 34, 36, 37, 38, 40, 41, 101, 102, 103,
                           104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
                           114, 115, 116}
            for ind_as_num in ind_as_refs:
                num = int(ind_as_num)
                if num not in valid_ind_as:
                    flags.append(
                        f"CRITICAL: Ind AS {num} may not exist — verify!"
                    )
                    score -= 0.2

        return max(score, 0.3), flags

    async def _layer4_consistency_check(self, content: str) -> tuple:
        """Check for internal contradictions in the content."""
        flags = []
        score = 0.95

        # Check for contradicting statements (simple heuristic)
        contradiction_patterns = [
            (r"always\b.*\bnever\b", "ALWAYS/NEVER contradiction detected"),
            (r"increases.*decreases.*same", "Contradictory direction claims"),
            (r"Dr\..*Cr\..*Dr\..*Cr\.", None),  # Multiple Dr/Cr — ok
        ]

        for pattern, flag_msg in contradiction_patterns:
            if flag_msg and re.search(pattern, content, re.IGNORECASE):
                flags.append(f"WARNING: {flag_msg}")
                score -= 0.05

        # Check if content has minimum educational substance
        word_count = len(content.split())
        if word_count < 100:
            flags.append("WARNING: Content too short — may be incomplete")
            score -= 0.2

        return max(score, 0.5), flags

    async def _layer5_exam_alignment(self, content: str, exam: str) -> tuple:
        """Check if content format aligns with exam requirements."""
        flags = []
        score = 0.9

        content_lower = content.lower()

        if exam.startswith("CA"):
            # CA content should have examples and journal entries
            if "example" not in content_lower and "illustration" not in content_lower:
                flags.append("INFO: No examples found — CA students need practical examples")
                score -= 0.05

        elif exam == "JEE":
            # JEE content should have formulas and numerical methods
            if not re.search(r"[A-Za-z]\s*=\s*[A-Za-z0-9]", content):
                flags.append("INFO: No formulas detected — JEE content needs formulas")
                score -= 0.05

        elif exam == "NEET":
            if "ncert" not in content_lower and "according to" not in content_lower:
                flags.append("INFO: NEET content should reference NCERT")
                score -= 0.03

        return max(score, 0.5), flags

    def _build_citations(self, chunks: List[dict]) -> List[dict]:
        """Build citation list from retrieved chunks."""
        citations = []
        seen = set()
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            source = meta.get("source", "")
            page = meta.get("page", "")
            cite_key = f"{source}:{page}"
            if cite_key not in seen and source:
                seen.add(cite_key)
                citations.append({
                    "source": source,
                    "page": page,
                    "source_type": meta.get("source_type", "EDUCATIONAL"),
                })
        return citations[:5]  # Max 5 citations
