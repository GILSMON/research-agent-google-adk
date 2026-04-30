"""
Debug runner for research_agent_langgraph.
Streams every graph event so you can see which node ran and what it produced.

Usage:
    python debug_langgraph.py
"""

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from research_agent_langgraph.agent import app


def chat(message: str) -> None:
    print(f"\n{'='*60}")
    print(f"USER: {message}")
    print(f"{'='*60}")

    for chunk in app.stream(
        {"messages": [HumanMessage(content=message)]},
        stream_mode="values",
    ):
        last_message = chunk["messages"][-1]
        last_message.pretty_print()


if __name__ == "__main__":
    chat("What time is it in Tokyo?")
