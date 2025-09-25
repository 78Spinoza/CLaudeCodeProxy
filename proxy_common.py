# proxy_common.py
"""
Shared utilities for Claude proxy implementations (Groq and xAI) v1.0.6
Provides:
- ClaudeToolMapper: mapping of tool names to Claude tool names and ultra‑simple tool schema generation.
- MessageTransformer: functions for converting between Anthropic, OpenAI (Groq), and xAI message formats.
"""

import json
import logging
import platform
from typing import Any, Dict, List, Optional, Tuple

# Version information
PROXY_VERSION = "1.0.11"
PROXY_BUILD_DATE = "2025-01-25"

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
    - String: Try parsing as JSON first, if fails return as-is with special markers
    - Dict with 'steps' array: Format as numbered list
    - Dict with other structure: Format as readable text
    - List: Format as numbered steps
    """
    # If it's a string, try to parse as JSON first
    if isinstance(plan_data, str):
        # Fix HTML entity encoding issues first
        plan_data = plan_data.replace("&amp;&amp;", "&&").replace("&lt;", "<").replace("&gt;", ">")
        
        # Try to parse as JSON in case it's a JSON string
        try:
            parsed_data = json.loads(plan_data)
            # Recursively call _format_plan with the parsed data
            return _format_plan(parsed_data)
        except (json.JSONDecodeError, TypeError):
            # If JSON parsing fails, it's already formatted markdown
            # Add special markers to prevent JSON wrapping in UI
            if plan_data.startswith("##") or plan_data.startswith("#"):
                # It's already markdown, add formatting hints
                return f"\n\n{plan_data}\n\n"
            return plan_data
    
    if isinstance(plan_data, dict):
        if "steps" in plan_data:
            steps = plan_data["steps"]
            if isinstance(steps, list):
                formatted_steps = []
                for i, step in enumerate(steps, 1):
                    formatted_steps.append(f"{i}. {step}")
                return "\n\n" + "\n".join(formatted_steps) + "\n\n"
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
            return "\n\n" + "\n".join(lines) + "\n\n"
    
    if isinstance(plan_data, list):
        formatted_steps = []
        for i, step in enumerate(plan_data, 1):
            formatted_steps.append(f"{i}. {step}")
        return "\n\n" + "\n".join(formatted_steps) + "\n\n"
    
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

    @classmethod
    def get_current_os(cls) -> str:
        """Detect the current operating system."""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system in ["linux", "darwin"]:  # darwin = macOS
            return "unix"
        else:
            return "unix"  # Default to unix for unknown systems

    @classmethod
    def get_os_specific_examples(cls) -> Dict[str, Any]:
        """Get OS-specific command examples and descriptions."""
        current_os = cls.get_current_os()

        if current_os == "windows":
            return {
                "primary_tool": "run_cmd",
                "primary_desc": f"Execute Windows CMD commands (RECOMMENDED for {platform.system()})",
                "primary_examples": ["dir", "cd /d C:\\project", "echo %CD%", "type file.txt"],
                "secondary_tool": "run_bash",
                "secondary_desc": "Execute cross-platform commands (converted automatically)",
                "secondary_examples": ["ls", "cd project", "pwd", "cat file.txt"],
                "current_system": platform.system(),
                "shell_info": "Commands run in Windows Command Prompt (cmd.exe)"
            }
        else:
            return {
                "primary_tool": "run_bash",
                "primary_desc": f"Execute shell commands (RECOMMENDED for {platform.system()})",
                "primary_examples": ["ls", "cd project", "pwd", "cat file.txt"],
                "secondary_tool": "run_cmd",
                "secondary_desc": "Execute Windows-style commands (not recommended on this system)",
                "secondary_examples": ["dir", "cd /d C:\\project", "echo %CD%"],
                "current_system": platform.system(),
                "shell_info": "Commands run in bash/sh shell"
            }

    @classmethod
    def _generate_os_aware_command_tools(cls) -> List[Dict[str, Any]]:
        """Generate OS-aware command tool descriptions."""
        os_info = cls.get_os_specific_examples()

        # Primary tool (recommended for current OS)
        primary_tool = cls._file_tool(
            os_info["primary_tool"],
            f"Run {os_info['current_system']} commands. Examples: {', '.join(os_info['primary_examples'][:3])}",
            {
                "command": {
                    "type": "string",
                    "description": f"{os_info['current_system']} command syntax"
                },
                "timeout": {"type": "integer", "description": "Timeout in milliseconds (default: 120000)"},
                "run_in_background": {"type": "boolean", "description": "Run command in background (default: false)"},
            },
            ["command"],
        )

        # Secondary tool (alternative)
        secondary_tool = cls._file_tool(
            os_info["secondary_tool"],
            f"Cross-platform commands. Examples: {', '.join(os_info['secondary_examples'][:3])}",
            {
                "command": {
                    "type": "string",
                    "description": "Cross-platform command syntax"
                },
                "timeout": {"type": "integer", "description": "Timeout in milliseconds (default: 120000)"},
                "run_in_background": {"type": "boolean", "description": "Run command in background (default: false)"},
            },
            ["command"],
        )

        return [primary_tool, secondary_tool]

    @classmethod
    def log_os_detection(cls, provider_name: str):
        """Log OS detection information for debugging."""
        os_info = cls.get_os_specific_examples()
        logger.info(f"[{provider_name}] OS Detection - System: {os_info['current_system']}")
        logger.info(f"[{provider_name}] Primary tool: {os_info['primary_tool']} ({os_info['primary_desc']})")
        logger.info(f"[{provider_name}] Shell environment: {os_info['shell_info']}")
        print(f"[{provider_name}] OS-aware tool registration: {os_info['current_system']} detected")
        print(f"[{provider_name}] Recommended command tool: {os_info['primary_tool']}")

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
                    "limit": {"type": "integer", "description": "Lines to read (optional)"},
                    "offset": {"type": "integer", "description": "Start line (optional)"},
                },
                ["file_path"],
            ),
            cls._file_tool(
                "open_file",
                "Open and read contents of a file (alias for read_file)",
                {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "limit": {"type": "integer", "description": "Lines to read (optional)"},
                    "offset": {"type": "integer", "description": "Start line (optional)"},
                },
                ["file_path"],
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
                "Make multiple edits to a file",
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
            # System Operations with OS-aware descriptions
            *cls._generate_os_aware_command_tools(),
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
            # Todo Operations - MANDATORY usage, no alternatives allowed
            cls._file_tool(
                "manage_todos",
                "Create and manage task lists for project tracking",
                {
                    "todos": {
                        "type": "array",
                        "description": "The updated todo list",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "minLength": 1,
                                    "description": "Task description (imperative form)"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                    "description": "Task status"
                                },
                                "activeForm": {
                                    "type": "string",
                                    "minLength": 1,
                                    "description": "Present continuous form of task"
                                }
                            },
                            "required": ["content", "status", "activeForm"],
                            "additionalProperties": False
                        }
                    }
                },
                ["todos"],
            ),
            cls._file_tool(
                "todo_write",
                "Create and manage task lists for project tracking (alternative name)",
                {
                    "todos": {
                        "type": "array",
                        "description": "The updated todo list",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "minLength": 1,
                                    "description": "Task description (imperative form)"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                    "description": "Task status"
                                },
                                "activeForm": {
                                    "type": "string",
                                    "minLength": 1,
                                    "description": "Present continuous form of task"
                                }
                            },
                            "required": ["content", "status", "activeForm"],
                            "additionalProperties": False
                        }
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
                "Search the web for information",
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
                "Exit planning mode with implementation plan",
                {"plan": {"type": "string", "description": "Implementation plan details"}},
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

            # Handle command environment detection and preprocessing
            if func_name == "run_cmd" and "command" in func_args:
                original_command = func_args.get("command", "").strip()

                # Detect Windows-style commands and paths
                windows_indicators = [
                    "\\", "/d", "C:", "D:", "E:", "F:",  # Windows paths and cd flags
                    "dir ", "type ", "copy ", "move ", "del ", "cls", "where "  # Windows commands
                ]

                # Check if this looks like a Windows command
                is_windows_command = any(indicator in original_command for indicator in windows_indicators)

                # On Windows, if command has Windows indicators, wrap it (but avoid double wrapping)
                if ClaudeToolMapper.get_current_os() == "windows" and is_windows_command and not original_command.startswith('cmd /c'):
                    func_args["command"] = f'cmd /c "{original_command}"'
                    logger.debug(f"[Groq] Wrapped Windows-style command: {original_command} -> cmd /c \"{original_command}\"")
                else:
                    # Leave Unix-style, external commands, or already-wrapped commands unwrapped
                    logger.debug(f"[Groq] Keeping command unwrapped: {original_command}")
            elif func_name in ["read_file", "open_file", "edit_file", "multi_edit_file"] and "path" in func_args and "file_path" not in func_args:
                # Handle parameter mapping for file operations
                logger.debug(f"[GROQ PARAM MAP] {func_name} - mapping 'path' to 'file_path': {func_args['path']}")
                func_args["file_path"] = func_args.pop("path")
                logger.debug(f"[GROQ PARAM MAP] {func_name} - after mapping: {list(func_args.keys())}")

            # Remove null values from parameters (causes schema validation errors)
            if func_name in ["read_file", "open_file", "edit_file", "multi_edit_file", "write_file"]:
                func_args = {k: v for k, v in func_args.items() if v is not None}
                logger.debug(f"[GROQ PARAM CLEAN] {func_name} - removed null parameters: {list(func_args.keys())}")

            # Special formatting for ExitPlanMode - minimal processing
            if func_name == "exit_plan_mode" and "plan" in func_args:
                plan_raw = func_args["plan"]
                logger.debug(f"[Groq] ExitPlanMode plan type: {type(plan_raw)}")
                # Pass plan through with minimal processing - only fix common encoding issues
                if isinstance(plan_raw, str):
                    # Only fix the most common HTML entities that definitely shouldn't be in plans
                    plan_raw = plan_raw.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                func_args["plan"] = plan_raw
            
            # Special formatting for TodoWrite - ONLY preserve Claude Code fields
            elif func_name in ["manage_todos", "todo_write"] and "todos" in func_args:
                todos = func_args["todos"]
                if isinstance(todos, list):
                    # Ensure proper todo format - ONLY the 3 required Claude Code fields
                    formatted_todos = []
                    for todo in todos:
                        if isinstance(todo, dict):
                            # Only keep the 3 required Claude Code fields
                            formatted_todo = {
                                "content": todo.get("content", ""),
                                "status": todo.get("status", "pending"),
                                "activeForm": todo.get("activeForm", todo.get("content", ""))
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

                # Handle command environment detection and preprocessing
                if func_name == "run_cmd" and "command" in func_args:
                    original_command = func_args.get("command", "").strip()

                    # Detect Windows-style commands and paths
                    windows_indicators = [
                        "\\", "/d", "C:", "D:", "E:", "F:",  # Windows paths and cd flags
                        "dir ", "type ", "copy ", "move ", "del ", "cls", "where "  # Windows commands
                    ]

                    # Check if this looks like a Windows command
                    is_windows_command = any(indicator in original_command for indicator in windows_indicators)

                    # On Windows, if command has Windows indicators, wrap it (but avoid double wrapping)
                    if ClaudeToolMapper.get_current_os() == "windows" and is_windows_command and not original_command.startswith('cmd /c'):
                        func_args["command"] = f'cmd /c "{original_command}"'
                        logger.debug(f"[xAI] Wrapped Windows-style command: {original_command} -> cmd /c \"{original_command}\"")
                    else:
                        # Leave Unix-style, external commands, or already-wrapped commands unwrapped
                        logger.debug(f"[xAI] Keeping command unwrapped: {original_command}")
                elif func_name in ["read_file", "open_file", "edit_file", "multi_edit_file"] and "path" in func_args and "file_path" not in func_args:
                    # Handle parameter mapping for file operations
                    logger.debug(f"[XAI PARAM MAP] {func_name} - mapping 'path' to 'file_path': {func_args['path']}")
                    func_args["file_path"] = func_args.pop("path")
                    logger.debug(f"[XAI PARAM MAP] {func_name} - after mapping: {list(func_args.keys())}")

                # Remove null values from parameters (causes schema validation errors)
                if func_name in ["read_file", "open_file", "edit_file", "multi_edit_file", "write_file"]:
                    func_args = {k: v for k, v in func_args.items() if v is not None}
                    logger.debug(f"[XAI PARAM CLEAN] {func_name} - removed null parameters: {list(func_args.keys())}")

                # Special formatting for ExitPlanMode - minimal processing
                if func_name == "exit_plan_mode" and "plan" in func_args:
                    plan_raw = func_args["plan"]
                    logger.debug(f"[xAI] ExitPlanMode plan type: {type(plan_raw)}")
                    # Pass plan through with minimal processing - only fix common encoding issues
                    if isinstance(plan_raw, str):
                        # Only fix the most common HTML entities that definitely shouldn't be in plans
                        plan_raw = plan_raw.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                    func_args["plan"] = plan_raw
                
                # Special formatting for TodoWrite - ONLY preserve Claude Code fields
                elif func_name in ["manage_todos", "todo_write"] and "todos" in func_args:
                    todos = func_args["todos"]
                    if isinstance(todos, list):
                        # Ensure proper todo format - ONLY the 3 required Claude Code fields
                        formatted_todos = []
                        for todo in todos:
                            if isinstance(todo, dict):
                                # Only keep the 3 required Claude Code fields
                                formatted_todo = {
                                    "content": todo.get("content", ""),
                                    "status": todo.get("status", "pending"),
                                    "activeForm": todo.get("activeForm", todo.get("content", ""))
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
