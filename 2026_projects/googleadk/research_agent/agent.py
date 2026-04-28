import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

# ── Model switch ─────────────────────────────────────────────────────────────
# Set USE_LOCAL=true in .env to use local Ollama/Gemma instead of Gemini.

USE_GROQ  = os.getenv("USE_GROQ",  "false").lower() == "true"
USE_LOCAL = os.getenv("USE_LOCAL", "false").lower() == "true"

if USE_LOCAL:
    model = LiteLlm(model="ollama_chat/gemma4:e4b", extra_body={"think": False})
elif USE_GROQ:
    model = LiteLlm(model="groq/llama-3.3-70b-versatile")
else:
    model = "gemini-2.5-flash"

# ── Tool 0: State — set home city ────────────────────────────────────────────

def set_home_city(city: str, tool_context: ToolContext) -> dict:
    """Saves the user's home city so it can be used in future questions.

    Args:
        city: The city the user wants to set as their home city.
        tool_context: Injected by ADK — provides access to session state.

    Returns:
        A confirmation dict.
    """
    tool_context.state["home_city"] = city.lower()
    return {"status": "saved", "home_city": city}


# ── Tool 1: Time ──────────────────────────────────────────────────────────────

def get_current_time(city: str, tool_context: ToolContext) -> dict:
    """Returns the current local time for a given city.
    If city is empty, falls back to the user's saved home city.

    Args:
        city: The name of the city (e.g. 'Tokyo', 'London'). Can be empty to use home city.
        tool_context: Injected by ADK — provides access to session state.

    Returns:
        A dict with city, current_time, timezone, and date.
    """
    import datetime
    import zoneinfo

    if not city:
        city = tool_context.state.get("home_city", "")
    if not city:
        return {"error": "No city provided and no home city saved. Ask the user to set a home city."}

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
        return {"error": f"No timezone data for '{city}'."}

    tz = zoneinfo.ZoneInfo(timezone_name)
    now = datetime.datetime.now(tz)

    return {
        "city": city,
        "current_time": now.strftime("%I:%M %p"),
        "timezone": timezone_name,
        "date": now.strftime("%A, %B %d %Y"),
    }


# ── Sub-agent 1: Time ────────────────────────────────────────────────────────

time_agent = Agent(
    name="time_agent",
    model=model,
    description="Returns the current local time for a given city.",
    instruction=(
        "You are a time specialist. "
        "The user's home city is: {state.home_city}. "
        "Use get_current_time to answer questions about the current time. "
        "If no city is given, pass an empty string — the tool will use the saved home city."
    ),
    tools=[get_current_time],
)


# ── Tool 2: Weather ───────────────────────────────────────────────────────────

def get_weather(city: str, tool_context: ToolContext) -> dict:
    """Returns the current weather conditions for a given city.
    If city is empty, falls back to the user's saved home city.

    Args:
        city: The name of the city to get weather for. Can be empty to use home city.
        tool_context: Injected by ADK — provides access to session state.

    Returns:
        A dict with city, temperature_celsius, condition, and humidity.
    """
    if not city:
        city = tool_context.state.get("home_city", "")
    if not city:
        return {"error": "No city provided and no home city saved. Ask the user to set a home city."}

    # Static data for now — we'll replace with a real API in a later step
    weather_data = {
        "tokyo":       {"temperature_celsius": 22, "condition": "Partly cloudy", "humidity": "65%"},
        "london":      {"temperature_celsius": 14, "condition": "Rainy",         "humidity": "80%"},
        "new york":    {"temperature_celsius": 18, "condition": "Sunny",         "humidity": "55%"},
        "sydney":      {"temperature_celsius": 26, "condition": "Clear skies",   "humidity": "50%"},
        "paris":       {"temperature_celsius": 16, "condition": "Overcast",      "humidity": "70%"},
        "dubai":       {"temperature_celsius": 38, "condition": "Hot and sunny", "humidity": "40%"},
        "los angeles": {"temperature_celsius": 24, "condition": "Sunny",         "humidity": "45%"},
    }

    data = weather_data.get(city.lower())
    if not data:
        return {"error": f"No weather data for '{city}'."}

    return {"city": city, **data}


# ── Sub-agent 2: Weather ──────────────────────────────────────────────────────

weather_agent = Agent(
    name="weather_agent",
    model=model,
    description="Returns the current weather conditions for a given city.",
    instruction=(
        "You are a weather specialist. "
        "The user's home city is: {state.home_city}. "
        "Use get_weather to answer questions about weather or temperature. "
        "If no city is given, pass an empty string — the tool will use the saved home city."
    ),
    tools=[get_weather],
)


# ── Tool 3: Currency ──────────────────────────────────────────────────────────

def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Converts an amount from one currency to another.

    Args:
        amount: The numeric amount to convert.
        from_currency: The source currency code (e.g. 'USD', 'EUR', 'GBP').
        to_currency: The target currency code (e.g. 'INR', 'JPY', 'AED').

    Returns:
        A dict with the original amount, converted amount, and exchange rate used.
    """
    # Static rates relative to USD — we'll replace with a live API in a later step
    rates_to_usd = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.27,
        "JPY": 0.0067,
        "INR": 0.012,
        "AED": 0.27,
        "AUD": 0.65,
    }

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    if from_curr not in rates_to_usd:
        return {"error": f"Unknown currency: {from_currency}"}
    if to_curr not in rates_to_usd:
        return {"error": f"Unknown currency: {to_currency}"}

    # Convert: source → USD → target
    amount_in_usd = amount * rates_to_usd[from_curr]
    converted = amount_in_usd / rates_to_usd[to_curr]
    rate = rates_to_usd[from_curr] / rates_to_usd[to_curr]

    return {
        "original": f"{amount} {from_curr}",
        "converted": f"{converted:.2f} {to_curr}",
        "rate_used": f"1 {from_curr} = {rate:.4f} {to_curr}",
    }


# ── Sub-agent 3: Currency ─────────────────────────────────────────────────────

currency_agent = Agent(
    name="currency_agent",
    model=model,
    description="Converts an amount from one currency to another.",
    instruction=(
        "You are a currency specialist. "
        "Use convert_currency to answer questions about currency conversion. "
        "Always ask for the amount, source currency, and target currency if not provided."
    ),
    tools=[convert_currency],
)


# ── Agent ─────────────────────────────────────────────────────────────────────

root_agent = Agent(
    name="research_agent",
    model=model,
    description="A travel assistant that answers questions about time, weather, and currency.",
    instruction=(
        "You are a helpful travel assistant and orchestrator. "
        "The user's home city is: {state.home_city} (may be empty if not set yet). "
        "Use set_home_city when the user tells you their city or asks you to remember it. "
        "Delegate to time_agent when asked about the current time in a city. "
        "Delegate to weather_agent when asked about weather or temperature. "
        "Delegate to currency_agent when asked to convert money between currencies. "
        "You can delegate to multiple agents in one response if the user asks about more than one thing."
    ),
    tools=[set_home_city, AgentTool(time_agent), AgentTool(weather_agent), AgentTool(currency_agent)],
)
