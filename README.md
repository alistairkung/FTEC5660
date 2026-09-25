# FTEC5660 Homework 1: Receipt Chain

Build a LangChain pipeline that reads every supermarket receipt in a folder
with the vision-capable DeepSeek Flash model and answers these two questions:

1. How much money did I spend in total for these bills?
2. How much would I have had to pay without the discount?

For this homework, **amount spent** means the final payment after the receipt's
rounding line. **Without the discount** means the sum of the original positive
item prices: add back every promotion, coupon, member, app, packaging-damage,
and percentage discount, but do not add back rounding.

## Student task

Only edit the two functions in `hw1.py` that contain `### YOUR CODE HERE`:

- `build_chain()` creates your LangChain chain.
- `answer_queries()` runs the chain on the receipt images and returns one final
  response for each question.

You may use prompt chaining, routing, parallel calls, reflection, or a
combination. Your final responses should each contain one HKD amount. Do not
hard-code filenames or public answers; grading uses unseen receipt folders.

## Setup and public test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Put your DeepSeek key after `DEEPSEEK_API_KEY=` in `.env`, then run:

```bash
python3 hw1.py --image-folder public_test
```

The program creates `results.csv` in the current directory. Its columns are
`query`, `model_response`, and `correctness`. The public answers are in
`public_test/ground_truth.json`.

The required model is `deepseek-v4-flash-vision-exp`, the vision-capable
DeepSeek Flash model. JPEG, PNG, GIF, and WebP inputs are accepted by the
homework runner.

## Homework 1 solution

The implementation is intentionally contained in **one submission file,
`hw1.py`**. Within that file I still keep three conceptual boundaries:
extraction, validation, and deterministic calculation.

### 1. Multimodal extraction

Each receipt image is converted to a data URL and passed through a reusable LCEL
chain:

```text
ChatPromptTemplate
    | DeepSeek vision
    | JsonOutputParser
```

The model returns a structured receipt containing:

- original item line amounts;
- discounts as positive magnitudes;
- subtotal after discounts;
- signed rounding;
- final amount paid after rounding.

The prompt explicitly treats quantity lines as **extended line totals**, not
unit prices. This mattered in testing because the model could otherwise read a
per-unit value when a receipt showed quantity > 1.

I disabled DeepSeek thinking mode for this extraction step. With thinking
enabled, the model spent very large token budgets repeatedly reasoning through
receipt arithmetic and sometimes produced no final JSON. The intended
responsibility split is instead:

```text
LLM: visual interpretation / transcription
Python: validation / arithmetic
```

### 2. Validation and normalisation

A `ReceiptValidator` is composed into the runnable using `RunnableLambda`.
It first normalises monetary values to `Decimal`, then checks:

- required receipt/item/discount fields are present;
- required monetary values are not null;
- item and discount amounts are non-negative;
- subtotal and final payment are non-negative;
- `sum(items) - sum(discounts) == subtotal_after_discounts`;
- `subtotal_after_discounts + rounding == amount_paid_after_rounding`.

The redundant receipt fields are deliberate. They are not all needed to answer
the two homework questions, but they provide an arithmetic consistency check
against noisy vision-model extraction.

### 3. Validation-gated retry and graceful fallback

The extraction + validation runnable uses `.with_retry(...)`. Validation
failures therefore cause the **whole extraction to run again**, rather than
re-validating the same bad dictionary.

This became important because repeated calls on the same receipt sometimes
produced different OCR/quantity interpretations. A bounded retry significantly
improved reliability on the public receipts.

The grading script is expected to run once, and producing a CSV is preferable
to crashing the entire batch because one receipt never validates. Therefore
`build_chain()` exposes both:

- a validated/retrying chain; and
- the raw extraction chain.

`answer_queries()` uses the validated chain first, but if validation still
fails after all retries it falls back to one raw extraction for that receipt and
continues processing the rest of the folder. This is a deliberate availability
trade-off: validated data is preferred, but one stubborn receipt should not
prevent `results.csv` from being written.

### 4. Deterministic calculation

After receipt extraction, no LLM is used for the final arithmetic.

- Q1 sums each receipt's authoritative `amount_paid_after_rounding`.
- Q2 sums every `original_line_amount`.

The calculator uses `Decimal` rather than binary floating point so currency
sums are exact.

## Tests

The tests remain separate from the single-file submission implementation and
import the relevant components directly from `hw1.py`.

Run the complete suite with:

```bash
python -m pytest
```

Using `python -m pytest` is preferred for this repository because it reliably
places the repository root on Python's import path.

The test suite covers three levels:

- **Extractor contract tests** use a fake runnable model to verify prompt/image
  wiring and JSON parsing without API calls.
- **Validator unit tests** cover required/null fields, sign boundaries (including
  zero-value marker lines), Decimal normalisation, and reconciliation failures.
- **Calculator integration tests** use known extracted receipt fixtures to verify
  both aggregate answers deterministically.

For the final public end-to-end check:

```bash
python hw1.py --image-folder public_test
cat results.csv
```

The public test should report both responses as `correct`.
