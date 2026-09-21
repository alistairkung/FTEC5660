"""Guiding deterministic integration test for the receipt calculator.

These fixtures model successful outputs from the future vision/LLM extraction
stage. No model/API call belongs in this test.
"""

from lib.receipt_calculator import ReceiptCalculator


def test_calculates_both_queries_across_receipts_1_and_2():
    receipts = [
        {
            "items": [
                # TODO: transcribe receipt1 original positive line amounts.
            ],
            "discounts": [
                # TODO: add receipt1 discount artifacts for reconciliation.
            ],
            "subtotal_after_discounts": 394.72,
            "rounding": -0.02,
            "amount_paid_after_rounding": 394.70,
        },
        {
            "items": [
                # TODO: transcribe receipt2 original positive line amounts.
            ],
            "discounts": [
                # TODO: add receipt2 discount artifacts for reconciliation.
            ],
            "subtotal_after_discounts": 316.11,
            "rounding": -0.01,
            "amount_paid_after_rounding": 316.10,
        },
    ]

    calculator = ReceiptCalculator()

    result = calculator.calculate(receipts)

    assert result["amount_paid"] == 710.80
    assert result["amount_without_discounts"] == 872.40
