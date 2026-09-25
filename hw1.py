#!/usr/bin/env python3
"""FTEC5660 HW1 student starter: build a chain for supermarket receipts."""

from __future__ import annotations

import os
import argparse
from copy import deepcopy
import base64
import csv
import json
import mimetypes
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

QUERY_1 = "How much money did I spend in total for these bills?"
QUERY_2 = "How much would I have had to pay without the discount?"
QUERIES = (QUERY_1, QUERY_2)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DUMMY_RESPONSE = "please design your chain to answer these two queries."


def load_env_file(path: Path = Path(".env")) -> None:
    """Load the simple KEY=VALUE entries used by this homework."""
    if not path.is_file():
        return
    import os

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def image_files(folder: Path) -> list[Path]:
    """Return supported images directly inside *folder*, sorted by filename."""
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def image_data_url(path: Path) -> str:
    """Encode a local image in the format accepted by a multimodal prompt."""
    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


# Student solution components are kept in this file to match the submission requirement.

RECEIPT_EXTRACTION_PROMPT = """
TASK

Extract the information from the provided receipt image into the specified JSON structure.

INPUT

One receipt image.

SEMANTIC CONSTRAINTS

- original_line_amount is the positive pre-discount amount for a purchased item line.

QUANTITY RULE

When an item quantity is greater than 1:

- original_line_amount must be the total pre-discount amount for the entire purchased quantity.
- Do not return the per-unit price.
- Do not divide a displayed line total by the quantity.
- If both a unit price and an extended line total are visible,
  use the extended line total.

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

{{
    "items": [
        {{
            "description": "string",
            "original_line_amount": 0.00
        }}
    ],
    "discounts": [
        {{
            "description": "string",
            "discount_amount": 0.00
        }}
    ],
    "subtotal_after_discounts": 0.00,
    "rounding": 0.00,
    "amount_paid_after_rounding": 0.00
}}

Any monetary field may be null only when its value cannot be reliably read from the receipt.
"""


def build_receipt_extraction_chain(llm):
    """A reusable one-receipt multimodal extraction chain.

    Runtime contract:
        {"image_url": "data:image/jpeg;base64,..."}

    Output contract:
        Parsed Python dict matching RECEIPT_EXTRACTION_PROMPT.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "human",
                [
                    {
                        "type": "text",
                        "text": RECEIPT_EXTRACTION_PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "{image_url}",
                        },
                    },
                ],
            )
        ]
    )
    return prompt | llm | JsonOutputParser()


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

    AGGREGATE_AMOUNT_FIELDS = [
        "subtotal_after_discounts",
        "rounding",
        "amount_paid_after_rounding",
    ]

    REQUIRED_FIELDS = [
        "items",
        "discounts",
        "subtotal_after_discounts",
        "rounding",
        "amount_paid_after_rounding",
    ]

    REQUIRED_ITEM_KEYS = ["description", "original_line_amount"]

    REQUIRED_DISCOUNT_KEYS = ["description", "discount_amount"]

    def validate(self, receipt: dict[str, Any]) -> dict[str, Any]:
        self._validate_required(receipt)
        self._validate_present(receipt)

        normalised = self._normalise_amounts(receipt)

        self._validate_item_amounts_are_non_negative(normalised)
        self._validate_discount_amounts_are_non_negative(normalised)
        self._validate_subtotal_final(normalised)
        self._validate_extracted_sum_equals_totals(normalised)

        return normalised

    def _validate_required(self, receipt: dict[str, Any]) -> None:
        if not all(key in receipt for key in self.REQUIRED_FIELDS):
            raise ValueError("Missing required receipt field")

        if not all(
            all(key in item for key in self.REQUIRED_ITEM_KEYS)
            for item in receipt["items"]
        ):
            raise ValueError("Missing required item field")

        if not all(
            all(key in discount for key in self.REQUIRED_DISCOUNT_KEYS)
            for discount in receipt["discounts"]
        ):
            raise ValueError("Missing required discount field")

    def _validate_present(self, receipt: dict[str, Any]) -> None:
        if not all(receipt[key] is not None for key in self.AGGREGATE_AMOUNT_FIELDS):
            raise ValueError("Required monetary field is null")

        if not all(
            all(item[key] is not None for key in self.REQUIRED_ITEM_KEYS)
            for item in receipt["items"]
        ):
            raise ValueError("Required item field is null")

        if not all(
            all(discount[key] is not None for key in self.REQUIRED_DISCOUNT_KEYS)
            for discount in receipt["discounts"]
        ):
            raise ValueError("Required discount field is null")

    def _normalise_amounts(self, receipt: dict[str, Any]) -> dict[str, Any]:
        r = deepcopy(receipt)

        r["items"] = [
            {
                **item,
                "original_line_amount": Decimal(str(item["original_line_amount"])),
            }
            for item in r["items"]
        ]

        r["discounts"] = [
            {
                **discount,
                "discount_amount": Decimal(str(discount["discount_amount"])),
            }
            for discount in r["discounts"]
        ]

        r["subtotal_after_discounts"] = Decimal(str(r["subtotal_after_discounts"]))

        r["rounding"] = Decimal(str(r["rounding"]))

        r["amount_paid_after_rounding"] = Decimal(str(r["amount_paid_after_rounding"]))

        return r

    def _validate_item_amounts_are_non_negative(self, receipt: dict[str, Any]) -> None:
        if not all(item["original_line_amount"] >= 0 for item in receipt["items"]):
            raise ValueError("Item amounts cannot be negative")

    def _validate_discount_amounts_are_non_negative(
        self, receipt: dict[str, Any]
    ) -> None:
        if not all(
            discount["discount_amount"] >= 0 for discount in receipt["discounts"]
        ):
            raise ValueError("Discount amounts cannot be negative")

    def _validate_subtotal_final(self, receipt: dict[str, Any]) -> None:
        if receipt["subtotal_after_discounts"] < 0:
            raise ValueError("Subtotal cannot be negative")

        if receipt["amount_paid_after_rounding"] < 0:
            raise ValueError("Final amount paid cannot be negative")

    def _validate_extracted_sum_equals_totals(self, receipt: dict[str, Any]) -> None:
        item_total = sum(item["original_line_amount"] for item in receipt["items"])

        discount_total = sum(
            discount["discount_amount"] for discount in receipt["discounts"]
        )

        expected_subtotal = item_total - discount_total

        if expected_subtotal != receipt["subtotal_after_discounts"]:
            raise ValueError(
                "Extracted items and discounts do not reconcile to subtotal"
            )

        expected_final = receipt["subtotal_after_discounts"] + receipt["rounding"]

        if expected_final != receipt["amount_paid_after_rounding"]:
            raise ValueError("Subtotal and rounding do not reconcile to final amount")


class ReceiptCalculator:
    """Calculate the two homework answers from already-extracted receipts."""

    def calculate(self, receipts: list[dict[str, Any]]) -> dict[str, Decimal]:
        """Return aggregate paid and pre-discount totals.

        Contract:
        - Q1 uses each receipt's authoritative amount_paid_after_rounding.
        - Q2 uses the sum of each item's original_line_amount.

        Implement this during the red -> green step.
        """
        gross_subtotal = Decimal("0.00")
        total_amount_paid = Decimal("0.00")

        for receipt in receipts:
            for item in receipt["items"]:
                gross_subtotal += Decimal(str(item["original_line_amount"]))

            total_amount_paid += Decimal(str(receipt["amount_paid_after_rounding"]))

        return {
            "amount_paid": total_amount_paid,
            "amount_without_discounts": gross_subtotal,
        }



def build_chain() -> Any:
    api_key = os.environ["DEEPSEEK_API_KEY"]

    llm = ChatDeepSeek(
        model="deepseek-v4-flash-vision-exp",
        api_key=api_key,
        max_tokens=6000,
        timeout=30,
        max_retries=2,
        extra_body={"thinking": {"type": "disabled"}},
    )

    validator = ReceiptValidator()

    raw_chain = build_receipt_extraction_chain(llm)

    validated_chain = (raw_chain | RunnableLambda(validator.validate)).with_retry(
        retry_if_exception_type=(ValueError,),
        stop_after_attempt=10,
    )

    return {
        "raw": raw_chain,
        "validated": validated_chain,
    }


def answer_queries(chain: Any, images: list[Path]) -> dict[str, Any]:
    receipts = []

    for image in images:
        print(f"Processing {image.name}")

        image_input = {"image_url": image_data_url(image)}

        try:
            receipt = chain["validated"].invoke(image_input)
            print("  correctly validated")
        except ValueError as error:
            print(f"  validation failed after retries: {error}")
            print("  using raw extraction fallback")
            receipt = chain["raw"].invoke(image_input)

        receipts.append(receipt)

    calculator = ReceiptCalculator()
    answers = calculator.calculate(receipts)

    return {
        QUERY_1: f"HK${answers['amount_paid']:.2f}",
        QUERY_2: f"HK${answers['amount_without_discounts']:.2f}",
    }


# Everything below is provided runner/scoring code. No edits are needed.

_MONEY_RE = re.compile(
    r"(?<![\w.])(?:HK\$|\$)?\s*(-?\d[\d,]*(?:\.\d+)?)(?![\w.])",
    re.IGNORECASE,
)


def response_text(value: Any) -> str:
    """Convert common LangChain response shapes to text for results.csv."""
    content = getattr(value, "content", value)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts).strip()
    if isinstance(content, (dict, list)):
        return json.dumps(content, ensure_ascii=False)
    return str(content).strip()


def parse_single_amount(text: str) -> Decimal | None:
    """Accept a response only when it contains exactly one numeric amount."""
    matches = _MONEY_RE.findall(text)
    if len(matches) != 1:
        return None
    try:
        return Decimal(matches[0].replace(",", "")).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def read_ground_truth(folder: Path) -> dict[str, Decimal]:
    """Read aggregate answers from the test folder."""
    path = folder / "ground_truth.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    answers = data.get("answers", data)
    return {
        query: Decimal(str(answers[query])).quantize(Decimal("0.01"))
        for query in QUERIES
    }


def correctness_text(response: str, expected: Decimal | None) -> str:
    """Return `correct`, or an expected/predicted mismatch explanation."""
    if expected is None:
        return "not graded: ground_truth.json is missing"
    predicted = parse_single_amount(response)
    if predicted == expected:
        return "correct"
    shown = f"HK${predicted:.2f}" if predicted is not None else repr(response)
    return f"incorrect: expected HK${expected:.2f}, predicted {shown}"


def write_results(responses: dict[str, Any], truth: dict[str, Decimal]) -> Path:
    """Write the required three-column results.csv file."""
    output = Path("results.csv")
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["query", "model_response", "correctness"])
        for query in QUERIES:
            text = response_text(responses.get(query, "<missing response>"))
            writer.writerow([query, text, correctness_text(text, truth.get(query))])
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FTEC5660 HW1 on receipt images")
    parser.add_argument(
        "--image-folder",
        required=True,
        type=Path,
        help="folder containing supermarket receipt images",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.image_folder.is_dir():
        raise SystemExit(f"not a folder: {args.image_folder}")

    images = image_files(args.image_folder)
    if not images:
        raise SystemExit(f"no supported images found in {args.image_folder}")

    load_env_file()
    chain = build_chain()
    responses = answer_queries(chain, images)
    if not isinstance(responses, dict):
        raise TypeError("answer_queries() must return a dictionary")

    output = write_results(responses, read_ground_truth(args.image_folder))
    print(f"Processed {len(images)} receipt(s). Wrote {output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
