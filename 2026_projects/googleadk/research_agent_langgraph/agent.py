import os
import datetime
import zoneinfo

from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

# ── Model switch ─────────────────────────────────────────────────────────────
# Same pattern as research_agent — USE_LOCAL=true for Gemma/Ollama, default Gemini.

USE_LOCAL = os.getenv("LG_USE_LOCAL", "false").lower() == "true"

if USE_LOCAL:
    llm = ChatOllama(model="gemma4:e4b", temperature=0)
else:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

# ── Tool 1: Time ──────────────────────────────────────────────────────────────

@tool
def get_current_time(city: str) -> str:
    """Returns the current local time for a given city.

    Args:
        city: The name of the city (e.g. 'Tokyo', 'London', 'Dubai').

    Returns:
        A string with the city, current time, timezone, and date.
    """
    city_timezones = {
        "new york":    "America/New_York",
        "london":      "Europe/London",
        "tokyo":       "Asia/Tokyo",
        "sydney":      "Australia/Sydney",
        "paris":       "Europe/Paris",
        "dubai":       "Asia/Dubai",
        "los angeles": "America/Los_Angeles",
    }

    tz_name = city_timezones.get(city.lower())
    if not tz_name:
        return f"No timezone data for '{city}'."

    tz = zoneinfo.ZoneInfo(tz_name)
    now = datetime.datetime.now(tz)

    return (
        f"City: {city} | "
        f"Time: {now.strftime('%I:%M %p')} | "
        f"Timezone: {tz_name} | "
        f"Date: {now.strftime('%A, %B %d %Y')}"
    )


# ── Tool 2: Weather ───────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> str:
    """Returns the current weather for a given city.

    Args:
        city: The name of the city (e.g. 'Tokyo', 'London', 'Dubai').

    Returns:
        A string with the city, condition, temperature, and humidity.
    """
    weather_data = {
        "new york":    {"condition": "Cloudy",  "temp_c": 15, "humidity": 72},
        "london":      {"condition": "Rainy",   "temp_c": 11, "humidity": 85},
        "tokyo":       {"condition": "Sunny",   "temp_c": 22, "humidity": 60},
        "sydney":      {"condition": "Clear",   "temp_c": 26, "humidity": 55},
        "paris":       {"condition": "Overcast","temp_c": 13, "humidity": 78},
        "dubai":       {"condition": "Hot",     "temp_c": 38, "humidity": 40},
        "los angeles": {"condition": "Sunny",   "temp_c": 24, "humidity": 50},
    }

    data = weather_data.get(city.lower())
    if not data:
        return f"No weather data for '{city}'."

    return (
        f"City: {city} | "
        f"Condition: {data['condition']} | "
        f"Temp: {data['temp_c']}°C | "
        f"Humidity: {data['humidity']}%"
    )


# ── Bind tools to model ───────────────────────────────────────────────────────
# bind_tools() sends the tool schemas to the model so it knows what it can call.

tools = [get_current_time, get_weather]
llm_with_tools = llm.bind_tools(tools)

# ── Graph ─────────────────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition


def call_model(state: MessagesState) -> dict:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


tool_node = ToolNode(tools)

graph_builder = StateGraph(MessagesState)
graph_builder.add_node("agent", call_model)
graph_builder.add_node("tools", tool_node)
graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges("agent", tools_condition)
graph_builder.add_edge("tools", "agent")

app = graph_builder.compile()
