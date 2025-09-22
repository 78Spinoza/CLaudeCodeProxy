# proxy_common.py
"""
Shared utilities for Claude proxy implementations (Groq and xAI).
Provides:
- ClaudeToolMapper: mapping of tool names to Claude tool names and ultra‑simple tool schema generation.
- MessageTransformer: functions for converting between Anthropic, OpenAI (Groq), and xAI message formats.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

def _format_todos(todos: List[Dict[str, Any]]) -> str:
    """Format a list of todo dictionaries into a readable string.

    Each todo is rendered on its own line with a preceding checkbox:
    - ``[ ]`` for pending/in‑progress tasks (status not ``completed``)
    - ``[x]`` for completed tasks
    A blank line is added after each entry for readability.
    """
    if not isinstance(todos, list):
        return ""
    lines = []
    for todo in todos:
        status = str(todo.get("status", "")).lower()
        checkbox = "[x]" if status == "completed" else "[ ]"
        content = str(todo.get("content", ""))
        lines.append(f"{checkbox} {content}")
        lines.append("")  # extra blank line
    return "\n".join(lines).strip()


def _format_plan(plan_data: Any) -> str:
    """Format plan data into readable markdown for ExitPlanMode.
    
    Handles various plan formats:
    - String: Return as-is
    - Dict with 'steps' array: Format as numbered list
    - Dict with other structure: Format as readable text
    - List: Format as numbered steps
    """
    if isinstance(plan_data, str):
        return plan_data
    
    if isinstance(plan_data, dict):
        if "steps" in plan_data:
            steps = plan_data["steps"]
            if isinstance(steps, list):
                formatted_steps = []
                for i, step in enumerate(steps, 1):
                    formatted_steps.append(f"{i}. {step}")
                return "\n".join(formatted_steps)
        else:
            # Generic dict formatting
            lines = []
            for key, value in plan_data.items():
                if isinstance(value, list):
                    lines.append(f"**{key.title()}:**")
                    for item in value:
                        lines.append(f"- {item}")
                else:
                    lines.append(f"**{key.title()}:** {value}")
            return "\n".join(lines)
    
    if isinstance(plan_data, list):
        formatted_steps = []
        for i, step in enumerate(plan_data, 1):
            formatted_steps.append(f"{i}. {step}")
        return "\n".join(formatted_steps)
    
    # Fallback: convert to string
    return str(plan_data)


import os

class BaseModelSelector:
    """Base class for intelligent model selection based on task complexity."""

    def __init__(self, reasoning_keywords: List[str], coding_keywords: List[str] = None):
        self.reasoning_keywords = reasoning_keywords
        self.coding_keywords = coding_keywords or []

    @staticmethod
    def extract_text_content(messages: List[Dict[str, Any]]) -> str:
        """Extract lowercase text content from messages for keyword analysis."""
        text = []
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, str):
                text.append(content.lower())
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text":
                        text.append(part.get("text", "").lower())
        return " ".join(text)

    def calculate_scores(self, text_content: str) -> Tuple[int, int]:
        """Calculate reasoning and coding scores based on keyword presence."""
        reasoning_score = sum(1 for kw in self.reasoning_keywords if kw in text_content)
        coding_score = sum(1 for kw in self.coding_keywords if kw in text_content)
        return reasoning_score, coding_score

# ... (rest of proxy_common.py)

class ClaudeToolMapper:
    """Handles tool mapping and schema generation for Claude Code tools.

    The mapping covers both the plain tool names used by the providers and the
    ``functions/``‑prefixed variants that some back‑ends emit.
    """

    # Tool name mappings from provider to Claude Code
    TOOL_MAPPING = {
        "read_file": "Read",
        "open_file": "Read",
        "write_file": "Write",
        "edit_file": "Edit",
        "multi_edit_file": "MultiEdit",
        "run_bash": "Bash",
        "run_cmd": "Bash",
        "search_files": "Glob",
        "grep_search": "Grep",
        "web_search": "WebSearch",
        "browser_search": "WebSearch",
        "web_fetch": "WebFetch",
        "manage_todos": "TodoWrite",
        "todo_write": "TodoWrite",
        "get_bash_output": "BashOutput",
        "kill_bash_shell": "KillShell",
        "edit_notebook": "NotebookEdit",
        "delegate_task": "Task",
        "exit_plan_mode": "ExitPlanMode",
        # Functions/ prefixed versions
        "functions/read_file": "Read",
        "functions/open_file": "Read",
        "functions/write_file": "Write",
        "functions/edit_file": "Edit",
        "functions/multi_edit_file": "MultiEdit",
        "functions/run_bash": "Bash",
        "functions/run_cmd": "Bash",
        "functions/search_files": "Glob",
        "functions/grep_search": "Grep",
        "functions/web_search": "WebSearch",
        "functions/browser_search": "WebSearch",
        "functions/web_fetch": "WebFetch",
        "functions/manage_todos": "TodoWrite",
        "functions/todo_write": "TodoWrite",
        "functions/get_bash_output": "BashOutput",
        "functions/kill_bash_shell": "KillShell",
        "functions/edit_notebook": "NotebookEdit",
        "functions/delegate_task": "Task",
        "functions/exit_plan_mode": "ExitPlanMode",
    }

    @classmethod
    def _file_tool(
        cls,
        name: str,
        description: str,
        properties: Dict[str, Any],
        required: List[str],
    ) -> Dict[str, Any]:
        """Helper to create a tool schema with a consistent format, enforcing strict schema compliance."""
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
            },
        }

    @classmethod
    def generate_ultra_simple_tools(cls) -> List[Dict[str, Any]]:
        """Generate ultra‑simple tool schemas accepted by Groq and xAI.

        The schemas are deliberately minimal – they contain only the fields that
        the back‑ends require. This keeps the proxy lightweight and avoids the
        ``Tools should have a name!`` errors that some providers emit when extra
        properties are present.
        """
        return [
            # File Operations
            cls._file_tool(
                "read_file",
                "Read contents of a file",
                {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "path": {"type": "string", "description": "Path to the file (alternative)"},
                    "limit": {"type": "integer", "description": "Lines to read (optional)"},
                    "offset": {"type": "integer", "description": "Start line (optional)"},
                },
                [],
            ),
            cls._file_tool(
                "open_file",
                "Open and read contents of a file (alias for read_file)",
                {
                    "path": {"type": "string", "description": "Path to the file"},
                    "file_path": {"type": "string", "description": "Path to the file (alternative)"},
                    "limit": {"type": "integer", "description": "Lines to read (optional)"},
                    "offset": {"type": "integer", "description": "Start line (optional)"},
                },
                [],
            ),
            cls._file_tool(
                "write_file",
                "Write content to a file",
                {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "File content"},
                },
                ["file_path", "content"],
            ),
            cls._file_tool(
                "edit_file",
                "Edit a file by replacing text",
                {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "old_string": {"type": "string", "description": "Text to replace"},
                    "new_string": {"type": "string", "description": "New text"},
                    "replace_all": {"type": "boolean", "description": "Replace all occurrences"},
                },
                ["file_path", "old_string", "new_string"],
            ),
            cls._file_tool(
                "multi_edit_file",
                "Make multiple edits to one file",
                {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "edits": {
                        "type": "array",
                        "description": "Array of edit operations",
                        "items": {"type": "object"},
                    },
                },
                ["file_path", "edits"],
            ),
            # System Operations
            cls._file_tool(
                "run_bash",
                "Execute shell commands on Windows system. IMPORTANT: Use Windows syntax - forward slashes for paths, 'cd /d' for directory changes, %CD% for current directory, && for command chaining. Examples: 'cd /d C:\\UMAP && echo Current: %CD%', 'dir', 'type filename.txt'.",
                {
                    "command": {"type": "string", "description": "Windows shell command using Windows syntax (e.g., 'cd /d C:\\UMAP && dir', 'echo %CD%', 'type file.txt')"},
                    "timeout": {"type": "integer", "description": "Timeout in milliseconds (default: 120000)"},
                    "run_in_background": {"type": "boolean", "description": "Run command in background (default: false)"},
                },
                ["command"],
            ),
            cls._file_tool(
                "run_cmd",
                "Execute Windows Command Prompt commands for native Windows operations. Use Windows path syntax with backslashes, %CD% for current directory, && for command chaining.",
                {
                    "command": {"type": "string", "description": "The Windows command to execute (e.g., 'cd /d C:\\UMAP && dir', 'echo %CD%', 'type file.txt')"},
                    "timeout": {"type": "integer", "description": "Timeout in milliseconds (default: 120000)"},
                },
                ["command"],
            ),
            # Search Operations
            cls._file_tool(
                "search_files",
                "Search for files using glob patterns",
                {
                    "pattern": {"type": "string", "description": "Glob pattern like *.py"},
                    "path": {"type": "string", "description": "Directory to search"},
                },
                ["pattern"],
            ),
            cls._file_tool(
                "grep_search",
                "Search for text patterns in files",
                {
                    "pattern": {"type": "string", "description": "Text pattern to search"},
                    "path": {"type": "string", "description": "Path to search"},
                    "glob": {"type": "string", "description": "File filter like *.py"},
                },
                ["pattern"],
            ),
            # Todo Operations - Pure translation, no special handling
            cls._file_tool(
                "manage_todos",
                "MANDATORY: Create and manage task lists for structured development workflow - USE VERY FREQUENTLY",
                {
                    "todos": {
                        "type": "array",
                        "description": "Complete todo list (replaces entire list each time)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string", "description": "Task description in imperative form"},
                                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Current task status"},
                                "activeForm": {"type": "string", "description": "Present continuous form for in_progress tasks"},
                                "id": {"type": "string", "description": "Unique task identifier"},
                                "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "Task priority (optional, defaults to medium)"}
                            },
                            "required": ["content", "status", "activeForm"],
                            "additionalProperties": False
                        },
                    }
                },
                ["todos"],
            ),
            cls._file_tool(
                "todo_write",
                "MANDATORY: Write todo items for task tracking - USE VERY FREQUENTLY",
                {
                    "todos": {
                        "type": "array",
                        "description": "Complete todo list (replaces entire list each time)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string", "description": "Task description in imperative form"},
                                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Current task status"},
                                "activeForm": {"type": "string", "description": "Present continuous form for in_progress tasks"},
                                "id": {"type": "string", "description": "Unique task identifier"},
                                "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "Task priority (optional, defaults to medium)"}
                            },
                            "required": ["content", "status", "activeForm"],
                            "additionalProperties": False
                        },
                    }
                },
                ["todos"],
            ),
            # Advanced Tools
            cls._file_tool(
                "get_bash_output",
                "Get output from background bash process",
                {"bash_id": {"type": "string", "description": "Background process ID"}},
                ["bash_id"],
            ),
            cls._file_tool(
                "kill_bash_shell",
                "Kill a background bash process",
                {"shell_id": {"type": "string", "description": "Shell process ID to kill"}},
                ["shell_id"],
            ),
            cls._file_tool(
                "edit_notebook",
                "Edit a Jupyter notebook cell",
                {
                    "notebook_path": {"type": "string", "description": "Path to notebook"},
                    "new_source": {"type": "string", "description": "New cell content"},
                    "cell_type": {"type": "string", "description": "Cell type: code or markdown"},
                },
                ["notebook_path", "new_source"],
            ),
            cls._file_tool(
                "delegate_task",
                "Delegate task to specialized agent",
                {
                    "description": {"type": "string", "description": "Task description"},
                    "prompt": {"type": "string", "description": "Detailed task prompt"},
                    "subagent_type": {"type": "string", "description": "Agent type: general-purpose etc"},
                },
                ["description", "prompt", "subagent_type"],
            ),
            cls._file_tool(
                "browser_search",
                "Search the web for current information using GroqCloud's native browser search (powered by Exa).",
                {"query": {"type": "string", "description": "Search query"}},
                ["query"],
            ),
            cls._file_tool(
                "web_search",
                "Search the web for current information",
                {"query": {"type": "string", "description": "Search query"}},
                ["query"],
            ),
            cls._file_tool(
                "web_fetch",
                "Fetch content from a web URL",
                {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "prompt": {"type": "string", "description": "Prompt for processing content"},
                },
                ["url", "prompt"],
            ),
            cls._file_tool(
                "exit_plan_mode",
                "Exit planning mode and start execution",
                {"plan": {"type": "string", "description": "The plan to execute"}},
                ["plan"],
            ),
        ]


import os
import winreg
import requests
import time
import logging
from typing import Any, Dict, List, Optional, Union
from flask import Response, stream_with_context

logger = logging.getLogger(__name__)

class BaseApiClient:
    """Shared base class for API clients with common retry logic and authentication."""

    def __init__(self, base_url: str, env_var_name: str, provider_name: str, default_test_model: str):
        self.base_url = base_url
        self.env_var_name = env_var_name
        self.provider_name = provider_name
        self.default_test_model = default_test_model
        self.api_key = None

    def authenticate(self) -> bool:
        """Get and validate API key from environment or Windows registry."""
        env_key = os.getenv(self.env_var_name)
        if not env_key and os.name == 'nt':
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    registry_value, _ = winreg.QueryValueEx(key, self.env_var_name)
                    env_key = registry_value.strip().strip('"')
            except Exception:
                pass
        if env_key and env_key != "NA":
            self.api_key = env_key
            return True
        logger.error(f"[ERROR] {self.env_var_name} not found in environment or registry")
        return False

    def test_connection(self) -> bool:
        """Test a minimal request to verify the key works."""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            test_req = {"model": self.default_test_model, "messages": [{"role": "user", "content": "test"}], "max_tokens": 1}
            resp = requests.post(self.base_url, headers=headers, json=test_req, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False

    def send_request(self, request_data: Dict[str, Any], stream: bool = False) -> Union[Dict[str, Any], Response, None]:
        """Send request to API endpoint with robust retry logic and error handling."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        if stream:
            def generate():
                response = requests.post(self.base_url, headers=headers, json=request_data, stream=True, timeout=60)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            return Response(stream_with_context(generate()), content_type='text/event-stream')

        # Non-streaming requests with retry logic
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=request_data, timeout=60)

                if response.status_code == 200:
                    logger.debug(f"{self.provider_name} request successful on attempt {attempt + 1}")
                    return response.json(), None
                elif response.status_code == 429:
                    # Rate limit handling
                    wait_time = min(2 ** attempt, 30)
                    if attempt < max_retries - 1:
                        logger.warning(f"{self.provider_name} rate limit hit on attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"{self.provider_name} rate limit exceeded after {max_retries} attempts")
                else:
                    error_msg = f"{self.provider_name} API Error: {response.status_code} {response.text}"
                    logger.error(error_msg)
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** attempt, 15)
                        logger.warning(f"Request failed on attempt {attempt + 1}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return None, error_msg

            except Exception as e:
                error_msg = f"Request failed: {str(e)}"
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 15)
                    logger.warning(f"{self.provider_name} request failed on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(error_msg)
                    return None, error_msg

        return None, "All retry attempts failed"

# ... (rest of proxy_common.py remains unchanged)

import os
import winreg
import requests
import time
from flask import Response, stream_with_context

class BaseApiClient:
    """Base class for API clients with shared retry logic and authentication."""

    def __init__(self, provider_name, base_url, api_key_env_var):
        self.provider_name = provider_name
        self.base_url = base_url
        self.api_key_env_var = api_key_env_var
        self.api_key = None

    def authenticate(self):
        """Get and validate API key from environment or Windows registry."""
        env_key = os.getenv(self.api_key_env_var, None)

        if not env_key and os.name == 'nt':
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    registry_value, _ = winreg.QueryValueEx(key, self.api_key_env_var)
                    env_key = registry_value.strip().strip('"')
            except Exception:
                pass

        if env_key and env_key != "NA":
            self.api_key = env_key
            return True
        logger.error(f"[ERROR] {self.api_key_env_var} not found in environment or registry")
        return False

    def test_connection(self):
        """Test a minimal request to verify the key works."""
        if not self.api_key:
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            test_req = {"model": "test-model", "messages": [{"role": "user", "content": "test"}], "max_tokens": 1}
            resp = requests.post(self.base_url, headers=headers, json=test_req, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"{self.provider_name} connection test failed: {e}")
            return False

    def send_request(self, request_data, stream=False):
        """Send request to API endpoint with robust retry logic and error handling."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        if stream:
            def generate():
                response = requests.post(self.base_url, headers=headers, json=request_data, stream=True, timeout=60)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            return Response(stream_with_context(generate()), content_type='text/event-stream')

        # Non-streaming requests with retry logic
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=request_data, timeout=60)

                if response.status_code == 200:
                    logger.debug(f"{self.provider_name} request successful on attempt {attempt + 1}")
                    return response
                elif response.status_code == 429:
                    wait_time = min(2 ** attempt, 30)
                    if attempt < max_retries - 1:
                        logger.warning(f"{self.provider_name} rate limit hit on attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"{self.provider_name} rate limit exceeded after {max_retries} attempts")
                        return response
                elif response.status_code >= 500:
                    wait_time = min(2 ** attempt, 15)
                    if attempt < max_retries - 1:
                        logger.warning(f"{self.provider_name} server error {response.status_code} on attempt {attempt + 1}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"{self.provider_name} server error persists after {max_retries} attempts: {response.status_code}")
                        return response
                else:
                    logger.error(f"{self.provider_name} client error: {response.status_code} {response.text}")
                    return response
            except requests.exceptions.ConnectionError as e:
                wait_time = min(2 ** attempt, 15)
                if attempt < max_retries - 1:
                    logger.warning(f"{self.provider_name} connection dropped on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"{self.provider_name} connection failed after {max_retries} attempts: {e}")
                    raise
            except requests.exceptions.Timeout as e:
                wait_time = min(2 ** attempt, 15)
                if attempt < max_retries - 1:
                    logger.warning(f"{self.provider_name} timeout on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"{self.provider_name} timeout after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                wait_time = min(2 ** attempt, 15)
                if attempt < max_retries - 1:
                    logger.warning(f"{self.provider_name} request failed on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"{self.provider_name} request failed after {max_retries} attempts: {e}")
                    raise

        raise Exception("All retry attempts failed")

class MessageTransformer:
    """Utility class for translating messages between the different provider schemas.

    The class implements static methods for:
    * Converting Anthropic messages to the OpenAI‑style payload expected by Groq.
    * Translating Groq tool calls back into Anthropic ``tool_use`` blocks.
    * Translating xAI messages to/from Anthropic format.
    """

    @staticmethod
    def anthropic_to_openai(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform Anthropic messages to OpenAI format for GroqCloud.

        The transformation collapses any ``tool_result`` parts into plain text so
        that Groq receives a simple string payload.
        """
        transformed_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", [])
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if part.get("type") == "tool_result":
                            tool_id = part.get("tool_use_id", "unknown")
                            result = part.get("content", "")
                            text_parts.append(f"Tool {tool_id} result: {result}")
                        elif part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    transformed_messages.append({
                        "role": "user",
                        "content": "\n".join(text_parts) if text_parts else msg.get("content", ""),
                    })
                else:
                    transformed_messages.append(msg)
            elif msg.get("role") == "assistant":
                content = msg.get("content", [])
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if part.get("type") == "tool_use":
                            tool_name = part.get("name", "unknown")
                            tool_input = part.get("input", {})
                            text_parts.append(f"I need to use the {tool_name} tool with: {json.dumps(tool_input)}")
                        elif part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    transformed_messages.append({
                        "role": "assistant",
                        "content": "\n".join(text_parts) if text_parts else msg.get("content", ""),
                    })
                else:
                    transformed_messages.append(msg)
            else:
                transformed_messages.append(msg)
        return transformed_messages

    @staticmethod
    def groq_to_anthropic_tools(groq_response: Dict[str, Any], original_model: str) -> Optional[Dict[str, Any]]:
        """Convert GroqCloud tool calls to Anthropic tool_use format."""
        if not ("choices" in groq_response and groq_response["choices"]):
            return None
        message = groq_response["choices"][0]["message"]
        if "tool_calls" not in message:
            return None
        
        tool_use_blocks = []
        
        for tool_call in message["tool_calls"]:
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])
            claude_tool_name = ClaudeToolMapper.TOOL_MAPPING.get(func_name, func_name)
            
            # Special formatting for ExitPlanMode and TodoWrite
            if func_name == "exit_plan_mode" and "plan" in func_args:
                plan_raw = func_args["plan"]
                # Try to parse as JSON if it's a string
                if isinstance(plan_raw, str):
                    try:
                        plan_parsed = json.loads(plan_raw)
                        func_args["plan"] = _format_plan(plan_parsed)
                    except json.JSONDecodeError:
                        func_args["plan"] = _format_plan(plan_raw)
                else:
                    func_args["plan"] = _format_plan(plan_raw)
            
            # Special formatting for TodoWrite
            elif func_name in ["manage_todos", "todo_write"] and "todos" in func_args:
                todos = func_args["todos"]
                if isinstance(todos, list):
                    # Ensure proper todo format and add formatted display
                    formatted_todos = []
                    for todo in todos:
                        if isinstance(todo, dict):
                            # Ensure required fields exist
                            formatted_todo = {
                                "content": todo.get("content", ""),
                                "status": todo.get("status", "pending"),
                                "activeForm": todo.get("activeForm", todo.get("content", "")),
                                "id": todo.get("id", f"task_{len(formatted_todos)+1}"),
                                "priority": todo.get("priority", "medium")
                            }
                            formatted_todos.append(formatted_todo)
                    func_args["todos"] = formatted_todos
            
            tool_use_blocks.append({
                "type": "tool_use",
                "id": tool_call["id"],
                "name": claude_tool_name,
                "input": func_args,
            })
        
        return {
            "id": groq_response.get("id"),
            "type": "message",
            "content": tool_use_blocks,
            "model": original_model,
            "usage": groq_response.get("usage", {}),
            "stop_reason": "tool_use",
        }

    @staticmethod
    def groq_to_anthropic_text(groq_response: Dict[str, Any], original_model: str) -> Optional[Dict[str, Any]]:
        """Convert a regular Groq text response to Anthropic format."""
        if not ("choices" in groq_response and groq_response["choices"]):
            return None
        message = groq_response["choices"][0]["message"]
        content = message.get("content", "")
        return {
            "id": groq_response.get("id"),
            "type": "message",
            "content": [{"type": "text", "text": content}],
            "model": original_model,
            "usage": groq_response.get("usage", {}),
        }

    @staticmethod
    def transform_anthropic_to_xai(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform Anthropic messages to xAI format.

        This mirrors the logic used for Groq but targets the xAI endpoint.
        """
        transformed_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", [])
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if part.get("type") == "tool_result":
                            tool_id = part.get("tool_use_id", "unknown")
                            result = part.get("content", "")
                            text_parts.append(f"Tool {tool_id} result: {result}")
                        elif part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    transformed_messages.append({
                        "role": "user",
                        "content": "\n".join(text_parts) if text_parts else msg.get("content", ""),
                    })
                else:
                    transformed_messages.append(msg)
            else:
                transformed_messages.append(msg)
        return transformed_messages

    @staticmethod
    def transform_xai_to_anthropic(
        xai_response: Dict[str, Any],
        original_model: str,
        tool_mapping: Dict[str, str],
        api_client: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Transform an xAI response back into Anthropic format.

        Handles both regular text responses and tool calls. For web‑search tools the
        function performs a secondary xAI request to retrieve the actual search
        results and returns them as a plain text block.
        """
        if "choices" not in xai_response or not xai_response["choices"]:
            return {"error": "Invalid xAI response"}
        message = xai_response["choices"][0]["message"]
        if "tool_calls" in message:
            # Convert tool calls
            content = []
            
            # Add any direct text first
            if message.get("content"):
                content.append({"type": "text", "text": message["content"]})
            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                # Strip functions/ prefix if present
                if func_name.startswith("functions/"):
                    func_name = func_name[10:]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                # Intercept web search
                if func_name in ["web_search", "browser_search"] and api_client:
                    query = func_args.get("query", "")
                    logger.info(f"[WEB SEARCH INTERCEPT] Intercepting {func_name} with query: {query}")
                    search_request = {
                        "model": "grok-4-0709",
                        "messages": [{"role": "user", "content": f"Please search the web for information about: {query}. Provide detailed results with sources and URLs when possible."}],
                        "max_tokens": 4000,
                    }
                    search_response = api_client.send_request(search_request)
                    if isinstance(search_response, Any) and hasattr(search_response, "status_code") and search_response.status_code == 200:
                        search_data = search_response.json()
                        search_result = search_data["choices"][0]["message"]["content"]
                    else:
                        search_result = f"Web search failed: {getattr(search_response, 'text', str(search_response))}"
                    # Return as a regular text response
                    return {
                        "id": xai_response.get("id"),
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "text", "text": f"I searched the web for '{query}' and found the following information:\n\n{search_result}"}],
                        "model": original_model,
                        "stop_reason": "end_turn",
                        "usage": {
                            "input_tokens": xai_response.get("usage", {}).get("prompt_tokens", 0),
                            "output_tokens": xai_response.get("usage", {}).get("completion_tokens", 0),
                        },
                    }
                # Normal tool mapping with special handling for plan formatting
                claude_tool_name = tool_mapping.get(func_name, func_name)
                
                # Special formatting for ExitPlanMode and TodoWrite
                if func_name == "exit_plan_mode" and "plan" in func_args:
                    plan_raw = func_args["plan"]
                    # Try to parse as JSON if it's a string
                    if isinstance(plan_raw, str):
                        try:
                            plan_parsed = json.loads(plan_raw)
                            func_args["plan"] = _format_plan(plan_parsed)
                        except json.JSONDecodeError:
                            func_args["plan"] = _format_plan(plan_raw)
                    else:
                        func_args["plan"] = _format_plan(plan_raw)
                
                # Special formatting for TodoWrite
                elif func_name in ["manage_todos", "todo_write"] and "todos" in func_args:
                    todos = func_args["todos"]
                    if isinstance(todos, list):
                        # Ensure proper todo format
                        formatted_todos = []
                        for todo in todos:
                            if isinstance(todo, dict):
                                # Ensure required fields exist
                                formatted_todo = {
                                    "content": todo.get("content", ""),
                                    "status": todo.get("status", "pending"),
                                    "activeForm": todo.get("activeForm", todo.get("content", "")),
                                    "id": todo.get("id", f"task_{len(formatted_todos)+1}"),
                                    "priority": todo.get("priority", "medium")
                                }
                                formatted_todos.append(formatted_todo)
                        func_args["todos"] = formatted_todos
                
                content.append({
                    "type": "tool_use",
                    "id": tool_call["id"],
                    "name": claude_tool_name,
                    "input": func_args,
                })
            return {
                "id": xai_response.get("id"),
                "type": "message",
                "role": "assistant",
                "content": content,
                "model": original_model,
                "stop_reason": "tool_use",
                "usage": {
                    "input_tokens": xai_response.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": xai_response.get("usage", {}).get("completion_tokens", 0),
                },
            }
        # Regular text response
        content = message.get("content", "")
        return {
            "id": xai_response.get("id"),
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": original_model,
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": xai_response.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": xai_response.get("usage", {}).get("completion_tokens", 0),
            },
        }
