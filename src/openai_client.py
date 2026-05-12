from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def ask_openai(prompt: str, model: str = "gpt-5.2") -> str:
    response = ChatOpenAI(model=model, temperature=0).invoke(
        [
            ("human", prompt),
        ]
    )
    return response.content if isinstance(response.content, str) else str(response.content)
