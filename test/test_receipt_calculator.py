"""Guiding deterministic integration test for the receipt calculator.

These fixtures model successful outputs from the future vision/LLM extraction
stage. No model/API call belongs in this test.
"""

from decimal import Decimal

from hw1 import ReceiptCalculator


def test_calculates_both_queries_across_receipts_1_and_2():
    receipts = [
        {
            "items": [
                {"description": "韭菜豬肉雲吞20粒裝 #1", "original_line_amount": 24.90},
                {"description": "韭菜豬肉雲吞20粒裝 #2", "original_line_amount": 24.90},
                {"description": "韭菜豬肉雲吞20粒裝 #3", "original_line_amount": 24.90},
                {"description": "IF100% COCONUT WATER (qty 2)", "original_line_amount": 57.80},
                {"description": "玉芒 (qty 3)", "original_line_amount": 29.70},
                {"description": "Fresh綜合蔬汁 (qty 2)", "original_line_amount": 35.80},
                {"description": "雀巢脫脂高鈣牛奶飲品", "original_line_amount": 21.90},
                {"description": "蔬菜先生包裝蕃茄", "original_line_amount": 9.90},
                {"description": "蔬菜先生翠玉瓜1磅", "original_line_amount": 7.90},
                {"description": "咸蛋蒸肉餅", "original_line_amount": 36.90},
                {"description": "金御膳龍口粉絲 (qty 2)", "original_line_amount": 23.80},
                {"description": "(業務用)急凍蝦子肉 (qty 2)", "original_line_amount": 130.00},
                {"description": "白柳姬菇", "original_line_amount": 14.90},
                {"description": "蒜汁雞扒", "original_line_amount": 36.90},
            ],
            "discounts": [
                {"description": "包裝變形 #1", "discount_amount": 12.40},
                {"description": "包裝變形 #2", "discount_amount": 12.40},
                {"description": "包裝變形 #3", "discount_amount": 12.40},
                {"description": "Buy 2 Save $12.8", "discount_amount": 12.80},
                {"description": "Buy 3 Save $10.8", "discount_amount": 10.80},
                {"description": "Buy 2 Save $3.9", "discount_amount": 3.90},
                {"description": "5% OFF (CU)", "discount_amount": 20.78},
            ],
            "subtotal_after_discounts": 394.72,
            "rounding": -0.02,
            "amount_paid_after_rounding": 394.70,
        },
        {
            "items": [
                {"description": "PLASTIC BAG CHARGING", "original_line_amount": 1.00},
                {"description": "JADE MANGO (qty 3)", "original_line_amount": 29.70},
                {"description": "DORITOS NACHO CHEESE (qty 2)", "original_line_amount": 31.00},
                {"description": "MUSO SOUR AND SPICY (qty 2)", "original_line_amount": 29.80},
                {"description": "SELECT FISH & CUTTL (qty 2)", "original_line_amount": 31.80},
                {"description": "QUAKER QUICK COOKING (qty 2)", "original_line_amount": 19.80},
                {"description": "JAX COCO 100 PURE CO", "original_line_amount": 26.00},
                {"description": "FARMFRESH BLACK PEPP (qty 2)", "original_line_amount": 91.80},
                {"description": "YAKULT PROBIOTICS DR", "original_line_amount": 28.90},
                {"description": "TRAPPIST HI-CAL LOW", "original_line_amount": 22.90},
                {"description": "ORGANIC SOYA BEAN S", "original_line_amount": 15.90},
                {"description": "CASTLE SOFT PACK FAC", "original_line_amount": 11.90},
                {"description": "FRENCH BEAN (CHINA) (qty 2)", "original_line_amount": 19.80},
                {"description": "OWN RUN BAKERY BREAD", "original_line_amount": 16.00},
                {"description": "INDOMIE MI GORENG 5", "original_line_amount": 15.90},
            ],
            "discounts": [
                {"description": "Buy 3 Save $9.8", "discount_amount": 9.80},
                {"description": "Buy 2 Save $6", "discount_amount": 6.00},
                {"description": "Buy 2 Save $5.9", "discount_amount": 5.90},
                {"description": "Buy 2 Save $5.8", "discount_amount": 5.80},
                {"description": "Buy 2 Save $2", "discount_amount": 2.00},
                {"description": "MB APP UPGRADE", "discount_amount": 10.00},
                {"description": "App Upgrade", "discount_amount": 20.00},
                {"description": "5% OFF (CU-SCO)", "discount_amount": 16.59},
            ],
            "subtotal_after_discounts": 316.11,
            "rounding": -0.01,
            "amount_paid_after_rounding": 316.10,
        },
    ]

    calculator = ReceiptCalculator()

    result = calculator.calculate(receipts)

    assert result["amount_paid"] == Decimal("710.80")
    assert result["amount_without_discounts"] == Decimal("872.40")
