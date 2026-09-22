from pathlib import Path

from hw1 import image_data_url, load_env_file
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage
import os

def extract_receipt():
    load_env_file()

    api_key = os.environ["DEEPSEEK_API_KEY"]

    llm = ChatDeepSeek(
        model="deepseek-v4-flash-vision-exp",
        api_key=api_key,
        temperature=0,
        max_tokens=500,
        timeout=30,
        max_retries=2,
    )

    image_path = Path("public_test/receipt1.jpg")
    image_url = image_data_url(image_path)

    message = HumanMessage(
        content=[
            {"type": "text", "text": "Describe this receipt briefly."},
            {
                "type": "image_url",
                "image_url": {"url": image_url}
            }
        ]
    )

    response = llm.invoke([message])
    print(response.content)

if __name__ == "__main__":
    extract_receipt()
