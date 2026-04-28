"""
Debug runner — prints every ADK event so you can see exactly what the model
and tools are doing turn by turn.

Usage:
    python debug_run.py
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from research_agent.agent import root_agent

SESSION_SERVICE = InMemorySessionService()
APP_NAME = "debug"
USER_ID = "dev"
SESSION_ID = "debug-session-1"


async def chat(runner: Runner, message: str) -> None:
    print(f"\n{'='*60}")
    print(f"USER: {message}")
    print(f"{'='*60}")

    content = types.Content(role="user", parts=[types.Part(text=message)])

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        # Tool call
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    print(f"\n  [TOOL CALL] {fc.name}({dict(fc.args)})")
                elif hasattr(part, "function_response") and part.function_response:
                    fr = part.function_response
                    print(f"  [TOOL RESULT] {fr.name} → {fr.response}")
                elif hasattr(part, "text") and part.text:
                    print(f"\n  [MODEL] {part.text}")

        if event.error_code:
            print(f"\n  [ERROR] code={event.error_code} message={event.error_message}")


async def main() -> None:
    await SESSION_SERVICE.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=SESSION_SERVICE,
    )

    # Test the session state flow step by step
    await chat(runner, "My home city is Dubai")
    await chat(runner, "What's the weather?")
    await chat(runner, "What time is it?")


if __name__ == "__main__":
    asyncio.run(main())
