from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def ask_openai(prompt: str, model: str = "gpt-5.2") -> str:
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text
