import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# ── Model switch ─────────────────────────────────────────────────────────────
# Set USE_LOCAL=true in .env to use local Ollama/Gemma instead of Gemini.

USE_LOCAL = os.getenv("USE_LOCAL", "false").lower() == "true"

if USE_LOCAL:
    model = LiteLlm(model="ollama_chat/gemma4:e4b", extra_body={"think": False})
else:
    model = "gemini-2.5-flash-lite"

# ── Tool ─────────────────────────────────────────────────────────────────────

def get_current_time(city: str) -> dict:
    """Returns the current local time for a given city.

    Args:
        city: The name of the city (e.g. 'Tokyo', 'London').

    Returns:
        A dict with city, current_time, timezone, and date.
    """
    import datetime
    import zoneinfo

    city_timezones = {
        "new york": "America/New_York",
        "london": "Europe/London",
        "tokyo": "Asia/Tokyo",
        "sydney": "Australia/Sydney",
        "paris": "Europe/Paris",
        "dubai": "Asia/Dubai",
        "los angeles": "America/Los_Angeles",
    }

    timezone_name = city_timezones.get(city.lower())

    if not timezone_name:
        return {"error": f"Sorry, I don't have timezone data for '{city}'."}

    tz = zoneinfo.ZoneInfo(timezone_name)
    now = datetime.datetime.now(tz)

    return {
        "city": city,
        "current_time": now.strftime("%I:%M %p"),
        "timezone": timezone_name,
        "date": now.strftime("%A, %B %d %Y"),
    }


# ── Agent ─────────────────────────────────────────────────────────────────────

root_agent = Agent(
    name="research_agent",
    model=model,
    description="A helpful assistant that can tell you the current time in cities around the world.",
    instruction="You are a helpful assistant. When a user asks for the time in a city, use the get_current_time tool. Be friendly and concise.",
    tools=[get_current_time],
)
