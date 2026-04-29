# Research Agent — Google ADK Learning Project

A step-by-step learning project for **Google Agent Development Kit (ADK)**, building a travel assistant agent incrementally — one concept per step.

## What it does

A multi-agent travel assistant that answers questions about:
- Current local time in major cities
- Weather conditions
- Currency conversion
- Remembers your home city across the conversation (session state)

## Steps built

| Step | Concept | What was added |
|---|---|---|
| 1 | Single agent + tool | `get_current_time` tool, Gemini + Ollama model switch |
| 2 | Multiple tools | `get_weather`, `convert_currency`, parallel tool calls |
| 3 | Sessions & state | `set_home_city`, `ToolContext`, state persisted in SQLite |
| 4 | Multi-agent system | Root orchestrator delegates to `time_agent`, `weather_agent`, `currency_agent` |

## Key concepts learned

- **Agent** — wraps a model + tools + instruction into a conversational unit
- **Tool** — a plain Python function the model can call
- **ToolContext** — ADK-injected object giving tools access to session state
- **Session state** — `tool_context.state` key-value store persisting across turns
- **AgentTool** — wraps a sub-agent so another agent can call it like a tool
- **LiteLLM** — adapter to use non-Gemini models (Ollama, Groq) with ADK

## Models supported

| Switch | Model | Use case |
|---|---|---|
| default | `gemini-3.1-flash-lite-preview` | Best free tier (15 RPM, 500 RPD) |
| `USE_GROQ=true` | `groq/llama-3.3-70b-versatile` | High quota testing |
| `USE_LOCAL=true` | `ollama/gemma4:e4b` | Offline development |

## Setup

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install google-adk litellm python-dotenv

# 3. Add your API key to .env
cp .env.example .env
# edit .env and add GOOGLE_API_KEY

# 4. Run the dev UI
adk web
```

## Project structure

```
research_agent/
├── __init__.py       # ADK package entry point
└── agent.py          # All agents and tools
debug_run.py          # Programmatic debug runner (traces all ADK events)
Lessons.md            # Learning log with concepts per step
```
