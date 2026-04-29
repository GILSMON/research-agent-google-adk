# Google ADK — Learning Log

## Step 1: Single Agent with One Tool

**What we built:** An agent with a single `get_current_time` tool that returns the local time for a given city.

**Concepts introduced:**

- **Agent** — the core ADK class. Takes a name, model, instruction (system prompt), and a list of tools.
- **Tool** — a plain Python function. ADK reads the function signature and docstring to tell the model what the tool does and what arguments it expects.
- **`root_agent`** — the required name for the top-level agent in an ADK package. ADK looks for this name to find the entry point.
- **`__init__.py`** — every ADK agent lives in a Python package. This file just does `from . import agent` so ADK can load it.
- **`adk web`** — command to launch the ADK dev UI at `localhost:8000`. Used to chat with the agent during development.
- **Model string** — passing `"gemini-2.5-flash-lite"` as the model means ADK calls the Gemini API directly. No extra setup needed beyond an API key.
- **`GOOGLE_API_KEY`** — set in `.env`. ADK picks it up automatically.
- **`zoneinfo`** — Python standard library module for timezone-aware datetimes. No API call, no internet — pure local computation.

**Key file:** `research_agent/agent.py`

---

## Step 2: Multiple Tools

**What we built:** Added `get_weather` and `convert_currency` tools. The agent can now answer questions about time, weather, and currency in a single conversation — and call multiple tools in one response.

**Concepts introduced:**

- **Multiple tools** — pass a list to the `tools=` parameter. The model decides which tool(s) to call based on the user's question.
- **Parallel tool calls** — if the user asks about weather AND time in one message, the model can call both tools in the same response turn.
- **Static data** — weather and currency use hardcoded dicts for now. The tool interface (function signature + docstring) is what matters; the data source can be swapped later.
- **LiteLLM** — an adapter layer that lets ADK talk to non-Gemini models. Import: `from google.adk.models.lite_llm import LiteLlm`. Used to connect to local Ollama models.
- **Ollama** — a local model runner. We use `gemma4:e4b` (9.6 GB). Started with `ollama serve`.
- **`USE_LOCAL` switch** — an env var that toggles between Gemini (cloud) and Gemma (local) at startup. Lets you develop offline or save API quota.
- **`extra_body={"think": False}`** — disables Gemma4's thinking mode, reducing latency.

**Known issue with Gemma4:** Gemma4 + Ollama + LiteLLM has a tool-calling bug where the model loops infinitely instead of forming a final answer. Gemini does not have this issue. Keep `USE_LOCAL=false` until this is resolved upstream.

**Free tier note:** `gemini-2.5-flash-lite` allows 1000 requests/day and 15 RPM on the free tier — the most generous free Gemini model as of early 2026.

**Key file:** `research_agent/agent.py`

---

## Step 3: Sessions and State

**What we built:** A `set_home_city` tool that saves the user's city to session state. `get_current_time` and `get_weather` fall back to the saved city when no city is provided.

**Concepts introduced:**

- **`ToolContext`** — an object ADK injects automatically into any tool that declares it as a parameter. Gives the tool access to session state, among other things.
- **`tool_context.state`** — a key-value dict that persists for the lifetime of a session. Any tool can read or write it.
- **`{state.key}` in instruction** — ADK substitutes live state values into the agent's system prompt before the model sees it. Lets the model always know the current state.
- **Session storage** — ADK stores sessions in a SQLite file at `research_agent/.adk/session.db`. State survives restarts as long as the same session ID is used.
- **Session scope** — state is isolated per session ID. A new session starts with empty state.

**Key file:** `research_agent/agent.py`

---

## Step 4: Multi-Agent System

**What we built:** Split the single agent into a team — a root orchestrator that delegates to three specialist sub-agents.

**Architecture:**
```
root_agent (orchestrator)
├── time_agent      → get_current_time
├── weather_agent   → get_weather
└── currency_agent  → convert_currency
```

**Concepts introduced:**

- **Sub-agents** — specialist agents with a narrow focus, their own instruction, and only the tools they need.
- **`AgentTool`** — wraps a sub-agent so the root agent can call it exactly like a regular tool. ADK uses the sub-agent's `description` as the tool description sent to the model.
- **Delegation** — the root agent reads the user's question and routes to the right specialist. It no longer calls tools directly (except `set_home_city`).
- **Model choice matters** — small models (8B) struggle with multi-agent orchestration and generate malformed tool calls. Use a larger model (70B+ or Gemini) for the orchestrator.

**Debugging learned:**
- `debug_run.py` — programmatic runner that prints every ADK event (tool calls, tool results, model responses) to the terminal
- `429 RESOURCE_EXHAUSTED` — each multi-agent turn costs 2-3 API calls (root decides → sub-agent executes → sub-agent responds). Free tier limits burn fast.
- Groq `llama-3.3-70b-versatile` works for orchestration but occasionally generates malformed `AgentTool` calls. Gemini is more reliable for multi-agent.

**Key file:** `research_agent/agent.py`

---

## Step 5: Built-in Tools — Google Search

**What we built:** Added a `search_agent` with ADK's built-in `google_search` tool. The root agent delegates open-ended or real-time questions to it.

**Architecture:**
```
root_agent (orchestrator)
├── time_agent
├── weather_agent
├── currency_agent
└── search_agent    → google_search (NEW)
```

**Concepts introduced:**

- **Built-in tools** — ADK ships pre-built tools you import and attach directly. No function to write. Import: `from google.adk.tools import google_search`.
- **Grounding** — the model's answer is backed by live search results, not just training data. The search results are injected into the model's context automatically.
- **`google_search` is Gemini-only** — it uses Gemini's grounding feature under the hood. It does NOT work with Groq, Ollama, or any non-Gemini model. This is why `search_agent` hardcodes `model="gemini-3.1-flash-lite-preview"` even when the rest of the system uses Groq.

**Why `google_search` only works with Gemini:**
Grounding is a Gemini API feature — it allows the model to retrieve and cite live web results during generation. Other providers (Groq, Ollama) do not expose this capability. It is not a limitation of ADK itself.

**Alternative search options (work with any model):**

| Option | Free tier | How to use |
|---|---|---|
| **Tavily** | 1,000 searches/month | Custom tool calling Tavily API |
| **SerpAPI** | 100 searches/month | Custom tool calling SerpAPI |
| **DuckDuckGo** | Unlimited (unofficial) | Custom tool using `duckduckgo-search` Python package |

For non-Gemini setups, build a custom tool function that calls one of the above APIs — same concept, just a Python function instead of a built-in.

**Key file:** `research_agent/agent.py`

---

## Definitions Glossary

| Term | Definition |
|---|---|
| **Agent** | ADK class that wraps a model + tools + instruction into a conversational unit |
| **Tool** | A Python function the agent can call. ADK auto-generates the schema from the signature and docstring |
| **Runner** | ADK class that manages the conversation loop — sends messages, collects tool results, feeds them back to the model |
| **Session** | A single conversation thread. Has a unique ID and its own state dict |
| **ToolContext** | ADK-injected object that gives a tool access to session state and other runtime context |
| **Session state** | `tool_context.state` — a key-value dict that persists across all turns in a session |
| **LiteLLM** | Adapter that translates ADK's model calls into the format expected by non-Gemini providers (Ollama, OpenAI, etc.) |
| **`root_agent`** | The required variable name for the entry-point agent in an ADK package |
| **`adk web`** | CLI command that launches the ADK developer UI for testing agents in a browser |
| **`{state.key}`** | Template syntax in agent instructions — ADK substitutes the live value from session state before the model sees the prompt |
