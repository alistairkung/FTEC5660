"""Multimodal receipt extraction boundary.

The learner implements build_receipt_extraction_chain during the red -> green step.
"""

RECEIPT_EXTRACTION_PROMPT = """
TASK

Extract the information from the provided receipt image into the specified JSON structure.

INPUT

One receipt image.

SEMANTIC CONSTRAINTS

- original_line_amount is the positive pre-discount amount for a purchased item line.
- If a quantity is shown and the receipt provides an extended line total, use the extended line total rather than recalculating unit price × quantity.
- discount_amount is the positive magnitude of a discount, even if the receipt displays the discount as a negative value.
- Discounts may apply to an individual item or to the receipt as a whole. Do not invent an item association when none is shown.
- subtotal_after_discounts is the subtotal after discounts have been applied but before rounding.
- rounding is the signed rounding adjustment shown on the receipt. Preserve whether it increases or decreases the total.
- amount_paid_after_rounding is the final amount actually charged after rounding.
- Do not treat wallet balances, remaining stored-value balances, payment-card balances, previous balances, top-ups, or similar payment metadata as purchased items.
- Do not invent information that cannot be read from the receipt.
- If a required monetary value cannot be read, use null.
- If an item or discount amount is readable but its description is not, use "description unknown".
- Monetary values must be numbers, not strings.
- Return discount magnitudes as positive numbers. Preserve the sign only for rounding.

OUTPUT

Return only valid JSON. Do not include Markdown, code fences, commentary, or explanatory text.

Use exactly these top-level keys and this structure:

{
    "items": [
        {
            "description": "string",
            "original_line_amount": 0.00
        }
    ],
    "discounts": [
        {
            "description": "string",
            "discount_amount": 0.00
        }
    ],
    "subtotal_after_discounts": 0.00,
    "rounding": 0.00,
    "amount_paid_after_rounding": 0.00
}

Any monetary field may be null only when its value cannot be reliably read from the receipt.
"""


def build_receipt_extraction_chain(llm):
    """Build a reusable one-receipt multimodal extraction chain.

    Runtime contract:
        {"image_url": "data:image/jpeg;base64,..."}

    Output contract:
        Parsed Python dict matching RECEIPT_EXTRACTION_PROMPT.

    Implement this during the red -> green step.
    """
    raise NotImplementedError
