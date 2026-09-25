"""Contract tests for the reusable multimodal receipt extraction chain.

These tests deliberately fake the model boundary:
- no DeepSeek API calls;
- no receipt-image accuracy assertions;
- no validation/Decimal behaviour yet.

They specify only the extraction-chain behaviour we have designed.
"""

import json

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from hw1 import RECEIPT_EXTRACTION_PROMPT, build_receipt_extraction_chain

SAMPLE_EXTRACTION = {
    "items": [
        {
            "description": "Example item",
            "original_line_amount": 24.90,
        }
    ],
    "discounts": [
        {
            "description": "Example discount",
            "discount_amount": 2.40,
        }
    ],
    "subtotal_after_discounts": 22.50,
    "rounding": 0.00,
    "amount_paid_after_rounding": 22.50,
}


def _fake_llm_that_records(captured_messages):
    """Return a runnable fake model and record the prompt value it receives."""

    def respond(prompt_value):
        messages = prompt_value.to_messages()
        captured_messages.extend(messages)
        return AIMessage(content=json.dumps(SAMPLE_EXTRACTION))

    return RunnableLambda(respond)


def test_chain_sends_instruction_and_runtime_image_to_model():
    captured_messages = []
    fake_llm = _fake_llm_that_records(captured_messages)
    chain = build_receipt_extraction_chain(fake_llm)

    image_url = "data:image/jpeg;base64,receipt-one"
    chain.invoke({"image_url": image_url})

    assert len(captured_messages) == 1

    human_message = captured_messages[0]
    assert isinstance(human_message.content, list)

    text_parts = [
        part["text"] for part in human_message.content if part.get("type") == "text"
    ]
    image_parts = [
        part for part in human_message.content if part.get("type") == "image_url"
    ]

    assert len(text_parts) == 1

    rendered_prompt = text_parts[0]

    assert "Extract the information from the provided receipt image" in rendered_prompt
    assert '"items"' in rendered_prompt
    assert '"discounts"' in rendered_prompt
    assert '"subtotal_after_discounts"' in rendered_prompt
    assert '"rounding"' in rendered_prompt
    assert '"amount_paid_after_rounding"' in rendered_prompt


def test_chain_parses_valid_model_json_into_python_dict():
    captured_messages = []
    fake_llm = _fake_llm_that_records(captured_messages)
    chain = build_receipt_extraction_chain(fake_llm)

    result = chain.invoke(
        {
            "image_url": "data:image/jpeg;base64,receipt-one",
        }
    )

    assert result == SAMPLE_EXTRACTION
    assert isinstance(result, dict)


def test_same_chain_uses_each_runtime_image_url():
    captured_messages = []
    fake_llm = _fake_llm_that_records(captured_messages)
    chain = build_receipt_extraction_chain(fake_llm)

    first_url = "data:image/jpeg;base64,receipt-one"
    second_url = "data:image/jpeg;base64,receipt-two"

    chain.invoke({"image_url": first_url})
    chain.invoke({"image_url": second_url})

    assert len(captured_messages) == 2

    first_image = next(
        part["image_url"]["url"]
        for part in captured_messages[0].content
        if part.get("type") == "image_url"
    )
    second_image = next(
        part["image_url"]["url"]
        for part in captured_messages[1].content
        if part.get("type") == "image_url"
    )

    assert first_image == first_url
    assert second_image == second_url
