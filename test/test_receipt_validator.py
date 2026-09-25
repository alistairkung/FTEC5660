from copy import deepcopy
from decimal import Decimal

import pytest

from lib.receipt_validator import ReceiptValidator

VALID_RECEIPT = {
    "items": [
        {
            "description": "Apples",
            "original_line_amount": 30.00,
        },
        {
            "description": "Milk",
            "original_line_amount": 20.00,
        },
    ],
    "discounts": [
        {
            "description": "Member discount",
            "discount_amount": 5.00,
        }
    ],
    "subtotal_after_discounts": 45.00,
    "rounding": -0.10,
    "amount_paid_after_rounding": 44.90,
}


def test_valid_receipt_is_returned_with_decimal_money():
    validator = ReceiptValidator()

    result = validator.validate(deepcopy(VALID_RECEIPT))

    assert result["items"][0]["original_line_amount"] == Decimal("30.0")
    assert result["items"][1]["original_line_amount"] == Decimal("20.0")
    assert result["discounts"][0]["discount_amount"] == Decimal("5.0")
    assert result["subtotal_after_discounts"] == Decimal("45.0")
    assert result["rounding"] == Decimal("-0.1")
    assert result["amount_paid_after_rounding"] == Decimal("44.9")

    assert result["items"][0]["description"] == "Apples"
    assert result["discounts"][0]["description"] == "Member discount"


@pytest.mark.parametrize(
    "missing_key",
    [
        "items",
        "discounts",
        "subtotal_after_discounts",
        "rounding",
        "amount_paid_after_rounding",
    ],
)
def test_missing_required_top_level_key_fails(missing_key):
    receipt = deepcopy(VALID_RECEIPT)
    del receipt[missing_key]

    with pytest.raises(ValueError):
        ReceiptValidator().validate(receipt)


@pytest.mark.parametrize(
    ("collection", "missing_key"),
    [
        ("items", "description"),
        ("items", "original_line_amount"),
        ("discounts", "description"),
        ("discounts", "discount_amount"),
    ],
)
def test_missing_required_nested_field_fails(collection, missing_key):
    receipt = deepcopy(VALID_RECEIPT)
    del receipt[collection][0][missing_key]

    with pytest.raises(ValueError):
        ReceiptValidator().validate(receipt)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("items", 0, "original_line_amount"), None),
        (("discounts", 0, "discount_amount"), None),
        (("subtotal_after_discounts",), None),
        (("rounding",), None),
        (("amount_paid_after_rounding",), None),
    ],
)
def test_null_required_monetary_value_fails(path, value):
    receipt = deepcopy(VALID_RECEIPT)

    target = receipt
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(ValueError):
        ReceiptValidator().validate(receipt)


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("items", 0, "original_line_amount"), -1),
        (("discounts", 0, "discount_amount"), -1),
        (("subtotal_after_discounts",), -1),
        (("amount_paid_after_rounding",), -1),
    ],
)
def test_invalid_money_sign_fails(path, invalid_value):
    receipt = deepcopy(VALID_RECEIPT)

    target = receipt
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = invalid_value

    with pytest.raises(ValueError):
        ReceiptValidator().validate(receipt)


def test_zero_item_amount_is_allowed():
    receipt = deepcopy(VALID_RECEIPT)

    receipt["items"].append(
        {
            "description": "Coupon marker",
            "original_line_amount": 0,
        }
    )

    result = ReceiptValidator().validate(receipt)

    assert result["items"][-1]["original_line_amount"] == Decimal("0")


def test_zero_discount_amount_is_allowed():
    receipt = deepcopy(VALID_RECEIPT)

    receipt["discounts"].append(
        {
            "description": "Promotion marker",
            "discount_amount": 0,
        }
    )

    result = ReceiptValidator().validate(receipt)

    assert result["discounts"][-1]["discount_amount"] == Decimal("0")


def test_items_minus_discounts_must_reconcile_to_subtotal():
    receipt = deepcopy(VALID_RECEIPT)
    receipt["items"][0]["original_line_amount"] = 31.00

    with pytest.raises(ValueError):
        ReceiptValidator().validate(receipt)


def test_subtotal_plus_rounding_must_reconcile_to_final_amount():
    receipt = deepcopy(VALID_RECEIPT)
    receipt["amount_paid_after_rounding"] = 44.80

    with pytest.raises(ValueError):
        ReceiptValidator().validate(receipt)
