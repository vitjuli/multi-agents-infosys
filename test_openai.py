from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5.2",
    input="Say hello in one short sentence."
)

print(response.output_text)
