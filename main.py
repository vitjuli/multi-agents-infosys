from src.openai_client import ask_openai


def researcher_agent(topic: str) -> str:
    prompt = f"""
    You are a research agent.
    Find the most important technical points about this topic:

    Topic: {topic}
    """
    return ask_openai(prompt)


def critic_agent(text: str) -> str:
    prompt = f"""
    You are a critical reviewer.
    Identify weaknesses, missing assumptions, and possible improvements:

    Text:
    {text}
    """
    return ask_openai(prompt)


def final_writer_agent(research: str, critique: str) -> str:
    prompt = f"""
    Write a final polished answer using the research and critique.

    Research:
    {research}

    Critique:
    {critique}
    """
    return ask_openai(prompt)


if __name__ == "__main__":
    topic = "How LLM agents can help scientific research"

    research = researcher_agent(topic)
    print("\n=== RESEARCH ===\n")
    print(research)

    critique = critic_agent(research)
    print("\n=== CRITIQUE ===\n")
    print(critique)

    final = final_writer_agent(research, critique)
    print("\n=== FINAL ANSWER ===\n")
    print(final)