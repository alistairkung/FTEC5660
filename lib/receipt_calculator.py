"""Deterministic calculation boundary for extracted receipt data.

The vision/LLM stage should produce receipt dictionaries matching the agreed
contract. This module deliberately contains no model or LangChain code.
"""

from __future__ import annotations

from typing import Any


class ReceiptCalculator:
    """Calculate the two homework answers from already-extracted receipts."""

    def calculate(self, receipts: list[dict[str, Any]]) -> dict[str, float]:
        """Return aggregate paid and pre-discount totals.

        Contract:
        - Q1 uses each receipt's authoritative amount_paid_after_rounding.
        - Q2 uses the sum of each item's original_line_amount.

        Implement this during the red -> green step.
        """
        raise NotImplementedError
