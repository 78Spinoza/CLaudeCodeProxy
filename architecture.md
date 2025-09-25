# Claude Proxy Architecture Overview v1.0.8

## Purpose

The **Claude Proxy** provides a low‑cost gateway for Claude Code tools by forwarding requests from Claude (via the `ANTHROPIC_BASE_URL` environment variable) to either **xAI** or **GroqCloud** back‑ends. It translates between Anthropic‑style messages and the OpenAI‑style payloads expected by the back‑ends, injects ultra‑simple tool schemas with OS‑aware descriptions, and selects the most appropriate model for the request.

**Key Benefits:**
- 15-20x cost reduction vs direct Anthropic API
- All 15+ Claude Code tools working with proper schemas
- OS-aware command tool selection (Windows/Unix/macOS)
- Non-verbose tool execution (no announcement chatter)
- Automatic environment detection and command wrapping

---

## High‑Level Data Flow

```text
+-----------------+       HTTP POST /v1/messages       +-------------------+
|   Claude Code   | ----------------------------------> |   Proxy Server    |
|   (Claude CLI) |                                      | (Flask app)       |
+-----------------+                                      +-------------------+
                                                             |
               +----------------------+   +--------------------------+
               | BaseClaudeProxy      |   |   Console Thread         |
               | (generic server)     |   |  (R/Q/H commands)        |
               +----------------------+   +--------------------------+
                             |
           +-----------------+-----------------+
           |                                   |
+-------------------+                +--------------------+
|   XAIAdapter      |                |   GroqAdapter      |
| (xAI specific)   |                | (Groq specific)    |
+-------------------+                +--------------------+
           |                                   |
+-------------------+                +--------------------+
|   XAIApiClient    |                |   GroqApiClient    |
+-------------------+                +--------------------+
           |                                   |
+-------------------+                +--------------------+
|   XAIModelSelector|               |   GroqModelSelector|
+-------------------+                +--------------------+
           |                                   |
   External xAI API                  External GroqCloud API
```

---

## Core Components

| Component | Responsibility |
|-----------|----------------|
| **BaseClaudeProxy** (`proxy_core.py`) | Sets up the Flask app, generic `/v1/<path>` route, port conflict detection, and a console thread for runtime commands (R‑restart, Q‑quit, H‑help). Delegates authentication and request handling to an *adapter* implementation. |
| **Adapter Interface** (required methods) | `authenticate() -> bool` – validates the API key.<br>`handle_proxy_request(data: dict) -> Flask response` – processes the incoming payload and returns a response.<br>`name` – human‑readable identifier used in logs. |
| **XAIAdapter** (`xai_adapter.py`) | Implements the adapter for the xAI back‑end. Uses `XAIApiClient` for HTTP calls, `XAIModelSelector` for model choice, and the shared `ClaudeToolMapper` / `MessageTransformer` utilities. |
| **GroqAdapter** (`groq_claude_proxy_enhanced.py`) | Implements the adapter for GroqCloud. Mirrors the XAI flow but includes special handling for web‑search tools (switches to the `groq/compound` model). |
| **Model Selectors** (`XAIModelSelector`, `GroqModelSelector`) | Inspect the user messages to decide which model and reasoning effort to use. Heuristics look for keywords related to reasoning complexity, coding, or explicit web‑search requests. |
| **API Clients** (`XAIApiClient`, `GroqApiClient`) | Retrieve API keys from environment variables (`XAI_API_KEY`, `GROQ_API_KEY`) or the Windows registry. Provide a thin wrapper around `requests.post` with retry/back‑off and optional streaming for xAI. |
| **ClaudeToolMapper** (`proxy_common.py`) | Maps Groq tool names to Claude‑Code tool names, generates ultra‑simple JSON schemas that Groq/​xAI accept, and performs parameter renaming (e.g., `path` → `file_path`). |
| **MessageTransformer** (`proxy_common.py`) | Converts Anthropic‑style messages ↔ OpenAI‑style messages, and translates tool calls/results back into the Claude tool‑use format. |

---

## Request Flow (Step‑by‑Step)

1. **Client Request** – Claude sends a POST to `http://localhost:<port>/v1/messages` with a JSON payload containing `model`, `messages`, optional `tools`, etc.
2. **BaseClaudeProxy** receives the request on the `/v1/<path>` route, checks the API key via the adapter, and forwards the JSON body to `adapter.handle_proxy_request`.
3. **Adapter** extracts the original model name and messages, then:
   - Calls its *Model Selector* to decide which back‑end model to use and the appropriate `reasoning_effort` (if applicable).
   - Uses `MessageTransformer` to convert Anthropic messages into the OpenAI‑style format required by the back‑end.
   - If the client supplied `tools`, the adapter injects ultra‑simple tool schemas generated by `ClaudeToolMapper` and sets `tool_choice: "auto"`.
4. **API Client** sends the assembled request to the external service (`https://api.x.ai/v1/chat/completions` or `https://api.groq.com/openai/v1/chat/completions`).
5. **Response Handling** –
   - For **text‑only** replies, `MessageTransformer` converts the OpenAI response back to Anthropic format.
   - For **tool calls**, `MessageTransformer` maps each Groq tool call to the corresponding Claude tool name and argument shape, returning a `tool_use` block.
   - For **web‑search** tool calls (Groq only), the proxy intercepts the call, re‑issues the request using the `groq/compound` model, and returns the search results as a plain‑text message.
6. **Flask Response** – The transformed payload is returned to Claude, completing the round‑trip.

---

## Model Selection Logic

- **Groq** – `GroqModelSelector.select_model_and_config` chooses:
  - `groq/compound` when a web‑search tool is present.
  - `openai/gpt-oss-120b` with a `reasoning_effort` (`high`/`medium`) derived from keyword analysis of the message content.
- **xAI** – `XAIModelSelector.select_model` evaluates two keyword lists (reasoning vs. coding). It prefers:
  - `grok-4-0709` with high reasoning for complex analytical requests or any Opus model name.
  - `grok-code-fast-1` for coding‑centric tasks.

Both selectors default to the higher‑capacity model when the heuristics indicate a need for deeper reasoning.

---

## Web‑Search Interception (Groq Only)

When a tool call named `web_search` or `browser_search` is detected, the proxy:
1. Extracts the query.
2. Switches to the `groq/compound` model, which has built‑in web‑search capability.
3. Sends a simple user‑message request (`"Search the web for: <query>"`).
4. Returns the raw search results as a plain‑text Claude message.
5. If the secondary request fails, a fallback message informs the user that the search is unavailable.

---

## Configuration & Secrets

- **Environment Variables** –
  - `GROQ_API_KEY` – GroqCloud authentication token.
  - `XAI_API_KEY` – xAI authentication token.
- The proxy also reads these variables from the Windows registry under `HKCU\Environment` for convenience.
- No secrets are logged; only high‑level status messages are printed.

---

## Console Commands (Runtime)

| Command | Action |
|---------|--------|
| `R` | Restart the proxy (re‑executes the Python process). |
| `Q` / `QUIT` | Gracefully shut down the server and exit. |
| `H` / `HELP` | Show the help menu with the above commands. |

These commands are processed in a background thread (`_console_input_handler`).

---

## v1.0.8 Architecture Improvements

**Critical Tool Parameter Fix:**
- **Fixed Edit Tool Parameters**: Resolved parameter mapping for edit_file and multi_edit_file tools
- **Path-to-FilePath Mapping**: Models calling with 'path' parameter now correctly mapped to 'file_path'
- **Tool Validation Success**: Eliminates GroqCloud 400 errors about missing file_path properties
- **File Operations Working**: Edit, MultiEdit, Read, and Write tools now work correctly

## v1.0.7 Architecture Improvements

**Critical Bug Fix:**
- **Fixed Command Execution**: Resolved double cmd /c wrapping that broke git, python, npm and other external commands
- **Smart Command Detection**: Now only wraps Windows internal commands (dir, type, echo) while leaving external programs unwrapped
- **Proper Git Integration**: Git commands now execute correctly without Windows command prompt interference

## v1.0.6 Architecture Improvements

**Tool Schema Enhancements:**
- **OS-Aware Descriptions**: Tools automatically adapt descriptions based on detected OS (Windows/Unix/macOS)
- **Non-Verbose Execution**: Removed "MANDATORY" language that caused announcement chatter
- **Smart Command Wrapping**: `run_cmd` only wraps Windows internal commands (dir, type, echo) with `cmd /c`, leaves external programs (git, python, npm) unwrapped
- **Proper Field Validation**: TodoWrite uses exact 3-field schema (`content`, `status`, `activeForm`)

**Startup & Debugging:**
- **Version Logging**: Displays proxy version on startup for debugging
- **OS Detection Logging**: Shows detected OS and recommended command tools
- **Centralized Versioning**: Single version constant in `proxy_common.py`

**Schema Compliance:**
- **2025 Claude Code Compatible**: All tools match latest official specifications
- **JSON Schema Standards**: Proper `type`, `properties`, `required`, `enum` validation
- **Cross-Provider Tested**: Validated with both xAI Grok and GroqCloud

**Error Elimination:**
- **Fixed TodoWrite Corruption**: No more invalid `id`/`priority` fields
- **Fixed ExitPlanMode Verbosity**: Clean plan execution without announcements
- **Fixed Command Confusion**: Clear OS-specific examples prevent syntax errors

---

## Extending the Proxy

1. **Add a New Back‑End** – Implement a new *Adapter* class that satisfies the three required methods and plug it into `BaseClaudeProxy`.
2. **Custom Tool Schemas** – Extend `ClaudeToolMapper.generate_ultra_simple_tools` with additional tool definitions. Ensure the schema stays ultra‑simple (no `additionalProperties`).
3. **Enhanced Model Selection** – Refine the keyword lists or add a machine‑learning based classifier inside the selector classes.
4. **Metrics & Logging** – Hook into the existing `logging` configuration to emit structured JSON logs for observability.

---

*This document provides a concise developer‑oriented overview of the Claude Proxy architecture, its components, and the request lifecycle.*
