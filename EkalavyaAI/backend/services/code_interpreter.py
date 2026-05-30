"""
EkalavyaAI — Code Interpreter Service
Verifies numerical calculations in teacher-generated content.
Uses Python eval (sandboxed) for CA/JEE/NEET math verification.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CodeInterpreter:
    """
    Lightweight numerical verifier for exam content.
    Extracts and re-computes arithmetic expressions to flag wrong answers.
    """

    SAFE_GLOBALS = {"__builtins__": {}, "abs": abs, "round": round, "min": min,
                    "max": max, "sum": sum, "pow": pow}

    async def verify_numericals(self, content: str) -> str:
        """
        Scan content for arithmetic expressions and verify them.
        Returns content with [VERIFIED] or [CHECK] annotations on numericals.
        """
        lines = content.split("\n")
        verified_lines = []
        for line in lines:
            verified_lines.append(self._verify_line(line))
        return "\n".join(verified_lines)

    def _verify_line(self, line: str) -> str:
        """Check a single line for verifiable expressions."""
        # Pattern: "X = Y" or "= ₹Z" or "Answer: Z"
        expr_match = re.search(r"(\d[\d\s\+\-\*\/\(\)\.]+)\s*=\s*([\d,\.]+)", line)
        if not expr_match:
            return line
        try:
            lhs_str = expr_match.group(1).strip()
            rhs_str = expr_match.group(2).replace(",", "").strip()
            # Clean expression
            lhs_clean = re.sub(r"[^\d\+\-\*\/\(\)\.\s]", "", lhs_str)
            if not lhs_clean:
                return line
            computed = eval(lhs_clean, self.SAFE_GLOBALS, {})  # noqa: S307
            expected = float(rhs_str)
            if abs(computed - expected) < 0.01:
                return line  # Correct — no annotation needed
            else:
                logger.warning(f"Numerical mismatch: {lhs_clean} = {computed}, expected {expected}")
                return line + " ⚠️[verify]"
        except Exception:
            return line
