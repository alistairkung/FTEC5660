from pathlib import Path

from hw1 import (
    ReceiptCalculator,
    ReceiptValidator,
    build_receipt_extraction_chain,
    image_data_url,
    load_env_file,
)
from langchain_deepseek import ChatDeepSeek
import os


def extract_receipt():
    load_env_file()

    api_key = os.environ["DEEPSEEK_API_KEY"]

    llm = ChatDeepSeek(
        model="deepseek-v4-flash-vision-exp",
        api_key=api_key,
        max_tokens=6000,
        timeout=30,
        max_retries=2,
        extra_body={"thinking": {"type": "disabled"}},
    )

    image_paths = sorted(Path("public_test").glob("*.jpg"))

    validated_receipts = []

    chain = build_receipt_extraction_chain(llm)
    validator = ReceiptValidator()
    calculator = ReceiptCalculator()

    for image_path in image_paths:
        print(f"\nProcessing {image_path.name}")

        image_url = image_data_url(image_path)

        try:
            validated = extract_valid_receipt(
                image_url,
                chain,
                validator,
            )
            validated_receipts.append(validated)
            print("valid")

        except ValueError as error:
            print(f"error: {error}")

        print(
            f"\nValidated {len(validated_receipts)} " f"of {len(image_paths)} receipts"
        )

    answers = calculator.calculate(validated_receipts)

    print(answers)


def extract_valid_receipt(
    image_url,
    chain,
    validator,
    max_attempts=3,
):
    last_error = None

    for attempt in range(max_attempts):
        receipt = chain.invoke({"image_url": image_url})

        try:
            return validator.validate(receipt)
        except ValueError as error:
            last_error = error

    raise ValueError(
        f"Receipt failed validation after {max_attempts} attempts"
    ) from last_error


if __name__ == "__main__":
    extract_receipt()
