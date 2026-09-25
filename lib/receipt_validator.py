"""Validation and normalisation boundary for model-extracted receipts."""

from __future__ import annotations

from typing import Any


class ReceiptValidator:
    """Validate an untrusted extracted receipt and return a trusted equivalent.

    Intended responsibilities:
    - required receipt/item/discount fields exist;
    - required monetary values are present;
    - monetary values are normalised to Decimal;
    - signs satisfy the receipt-domain contract;
    - extracted totals reconcile.

    Invalid model output should fail explicitly rather than being silently repaired.
    """

    def validate(self, receipt: dict[str, Any]) -> dict[str, Any]:
        """Return a normalised trusted receipt, or raise ValueError when invalid."""
        raise NotImplementedError
