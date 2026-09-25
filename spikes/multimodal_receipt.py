from pathlib import Path

from hw1 import image_data_url, load_env_file
from lib.receipt_extractor import build_receipt_extraction_chain
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

    image_path = Path("public_test/receipt1.jpg")

    chain = build_receipt_extraction_chain(llm)

    result = chain.invoke({"image_url": image_data_url(image_path)})

    print(result)

    # response = chain.invoke({"image_url": image_data_url(image_path)})

    # print(response)
    # print("CONTENT:", repr(response.content))


if __name__ == "__main__":
    extract_receipt()
