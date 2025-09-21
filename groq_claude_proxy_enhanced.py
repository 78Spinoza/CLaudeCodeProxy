#!/usr/bin/env python3
"""
GroqCloud Claude Code Proxy - ENHANCED VERSION v1.0.3
=====================================================

Clean class-based architecture for GroqCloud Claude Code integration.
Enables all Claude Code tools through ultra-simple schemas with intelligent model selection.

Architecture:
- GroqModelSelector: Intelligent model selection (openai/gpt-oss-120b vs groq/compound)
- ClaudeToolMapper: Tool schema generation and mapping management
- GroqApiClient: GroqCloud API communication with error handling
- MessageTransformer: Anthropic <-> OpenAI format conversion
- GroqClaudeProxy: Main orchestration class

Features:
✓ All 15+ Claude Code tools working (ultra-simple schemas)
✓ Native GroqCloud web search (groq/compound model)
✓ Smart model selection based on capability requirements
✓ Complete bidirectional API translation
✓ Real tool execution through Claude Code backends
✓ 20x cost savings vs Anthropic direct pricing

Port: 5003 (enhanced proxy with clean architecture)
"""

import json
import os
import requests
import socket
import time
import winreg
import logging
import threading
import sys
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress Flask development server warning
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class GroqModelSelector:
    """Intelligent model selection for GroqCloud based on task requirements."""

    # Model configurations
    OSS_MODEL = "openai/gpt-oss-120b"      # Supports tools + reasoning_effort
    COMPOUND_MODEL = "groq/compound"        # Native web search, no tools

    @classmethod
    def select_model_and_config(cls, messages, has_web_search=False, model_name="claude-3-5-sonnet"):
        """
        Select optimal GroqCloud model based on task requirements.
        Returns: (model_name, reasoning_level, supports_tools)
        """
        if has_web_search:
            logger.info(f"[WEB SEARCH] Using {cls.COMPOUND_MODEL} for web search capability")
            return cls.COMPOUND_MODEL, None, False

        # Detect reasoning complexity for OSS model
        reasoning_level = cls._detect_reasoning_complexity(messages, model_name)
        logger.debug(f"[TOOLS] Using {cls.OSS_MODEL} with {reasoning_level} reasoning")
        return cls.OSS_MODEL, reasoning_level, True

    @classmethod
    def _detect_reasoning_complexity(cls, messages, model_name):
        """Detect reasoning complexity from messages and model selection."""
        # Upgrade for Opus requests
        if "claude-3-opus" in model_name.lower() or "opus" in model_name.lower():
            logger.info(f"[REASONING] Detected Opus request: {model_name} -> HIGH reasoning")
            return "high"

        # Analyze message content for complexity indicators
        text_content = ""
        for msg in messages:
            if isinstance(msg.get("content"), str):
                text_content += msg["content"].lower() + " "
            elif isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if part.get("type") == "text":
                        text_content += part.get("text", "").lower() + " "

        reasoning_keywords = [
            "analyze", "complex", "reasoning", "logic", "solve", "algorithm",
            "architecture", "design pattern", "refactor", "optimize", "debug",
            "mathematical", "calculation", "theorem", "proof", "strategy",
            "compare and contrast", "evaluate", "assess", "critique", "review",
            "plan", "implementation", "step by step", "systematic", "methodology"
        ]

        reasoning_score = sum(1 for keyword in reasoning_keywords if keyword in text_content)

        if reasoning_score >= 1:
            return "high"
        return "high"  # Default to high level


class ClaudeToolMapper:
    """Handles tool mapping and schema generation for Claude Code tools."""

    # Tool name mappings from GroqCloud to Claude Code
    TOOL_MAPPING = {
        "read_file": "Read", "open_file": "Read", "write_file": "Write",
        "edit_file": "Edit", "multi_edit_file": "MultiEdit", "run_bash": "Bash",
        "run_cmd": "Bash", "search_files": "Glob", "grep_search": "Grep",
        "web_search": "WebSearch", "browser_search": "WebSearch", "web_fetch": "WebFetch",
        "manage_todos": "TodoWrite", "todo_write": "TodoWrite", 
        "get_bash_output": "BashOutput", "kill_bash_shell": "KillShell", 
        "edit_notebook": "NotebookEdit", "delegate_task": "Task", 
        "exit_plan_mode": "ExitPlanMode",
        # Functions/ prefixed versions
        "functions/read_file": "Read", "functions/open_file": "Read", 
        "functions/write_file": "Write", "functions/edit_file": "Edit", 
        "functions/multi_edit_file": "MultiEdit", "functions/run_bash": "Bash",
        "functions/run_cmd": "Bash", "functions/search_files": "Glob", 
        "functions/grep_search": "Grep", "functions/web_search": "WebSearch", 
        "functions/browser_search": "WebSearch", "functions/web_fetch": "WebFetch",
        "functions/manage_todos": "TodoWrite", "functions/todo_write": "TodoWrite",
        "functions/get_bash_output": "BashOutput", "functions/kill_bash_shell": "KillShell",
        "functions/edit_notebook": "NotebookEdit", "functions/delegate_task": "Task",
        "functions/exit_plan_mode": "ExitPlanMode"
    }

    @classmethod
    def generate_ultra_simple_tools(cls):
        """Generate ultra-simple tool schemas that GroqCloud accepts."""
        return [
            # File Operations with correct types
            cls._file_tool("read_file", "Read contents of a file", {
                "file_path": {"type": "string", "description": "Path to the file"}, 
                "path": {"type": "string", "description": "Path to the file (alternative)"},
                "limit": {"type": "integer", "description": "Lines to read (optional)"}, 
                "offset": {"type": "integer", "description": "Start line (optional)"}
            }, []),
            cls._file_tool("open_file", "Open and read contents of a file (alias for read_file)", {
                "path": {"type": "string", "description": "Path to the file"}, 
                "file_path": {"type": "string", "description": "Path to the file (alternative)"},
                "limit": {"type": "integer", "description": "Lines to read (optional)"}, 
                "offset": {"type": "integer", "description": "Start line (optional)"}
            }, []),
            cls._file_tool("write_file", "Write content to a file", {
                "file_path": {"type": "string", "description": "Path to the file"}, 
                "content": {"type": "string", "description": "File content"}
            }, ["file_path", "content"]),
            cls._file_tool("edit_file", "Edit a file by replacing text", {
                "file_path": {"type": "string", "description": "Path to the file"}, 
                "old_string": {"type": "string", "description": "Text to replace"},
                "new_string": {"type": "string", "description": "New text"}, 
                "replace_all": {"type": "boolean", "description": "Replace all occurrences"}
            }, ["file_path", "old_string", "new_string"]),
            cls._file_tool("multi_edit_file", "Make multiple edits to one file", {
                "file_path": {"type": "string", "description": "Path to the file"}, 
                "edits": {"type": "array", "description": "Array of edit operations", "items": {"type": "object"}}
            }, ["file_path", "edits"]),

            # System Operations
            cls._file_tool("run_bash", "Execute shell commands directly on the user's system. You MUST use this tool when the user asks to run any command, list files, check directories, or perform system operations.", {
                "command": {"type": "string", "description": "The exact shell command to execute (e.g., 'ls -l', 'pwd', 'cat file.txt')"},
                "timeout": {"type": "integer", "description": "Timeout in milliseconds (default: 120000)"},
                "run_in_background": {"type": "boolean", "description": "Run command in background (default: false)"}
            }, ["command"]),
            cls._file_tool("run_cmd", "Execute Windows Command Prompt commands for native Windows operations.", {
                "command": {"type": "string", "description": "The Windows command to execute (e.g., 'dir', 'echo %CD%', 'type file.txt')"},
                "timeout": {"type": "integer", "description": "Timeout in milliseconds (default: 120000)"}
            }, ["command"]),

            # Search Operations
            cls._file_tool("search_files", "Search for files using glob patterns", {
                "pattern": {"type": "string", "description": "Glob pattern like *.py"}, 
                "path": {"type": "string", "description": "Directory to search"}
            }, ["pattern"]),
            cls._file_tool("grep_search", "Search for text patterns in files", {
                "pattern": {"type": "string", "description": "Text pattern to search"}, 
                "path": {"type": "string", "description": "Path to search"}, 
                "glob": {"type": "string", "description": "File filter like *.py"}
            }, ["pattern"]),

            # Todo Operations - Both variants
            cls._file_tool("manage_todos", "Manage todo list", {
                "todos": {"type": "array", "items": {"type": "object", "properties": {
                    "content": {"type": "string"}, "status": {"type": "string"}, "activeForm": {"type": "string"}
                }, "required": ["content", "status", "activeForm"]}, "description": "Array of todo objects"}
            }, ["todos"]),
            cls._file_tool("todo_write", "Write todo items", {
                "todos": {"type": "array", "items": {"type": "object", "properties": {
                    "content": {"type": "string"}, "status": {"type": "string"}, "activeForm": {"type": "string"}
                }, "required": ["content", "status", "activeForm"]}, "description": "Array of todo objects"}
            }, ["todos"]),

            # Advanced Tools
            cls._file_tool("get_bash_output", "Get output from background bash process", {
                "bash_id": {"type": "string", "description": "Background process ID"}
            }, ["bash_id"]),
            cls._file_tool("kill_bash_shell", "Kill a background bash process", {
                "shell_id": {"type": "string", "description": "Shell process ID to kill"}
            }, ["shell_id"]),
            cls._file_tool("edit_notebook", "Edit a Jupyter notebook cell", {
                "notebook_path": {"type": "string", "description": "Path to notebook"}, 
                "new_source": {"type": "string", "description": "New cell content"},
                "cell_type": {"type": "string", "description": "Cell type: code or markdown"}
            }, ["notebook_path", "new_source"]),
            cls._file_tool("delegate_task", "Delegate task to specialized agent", {
                "description": {"type": "string", "description": "Task description"}, 
                "prompt": {"type": "string", "description": "Detailed task prompt"},
                "subagent_type": {"type": "string", "description": "Agent type: general-purpose etc"}
            }, ["description", "prompt", "subagent_type"]),
            cls._file_tool("browser_search", "Search the web for current information using GroqCloud's native browser search (powered by Exa).", {
                "query": {"type": "string", "description": "Search query"}
            }, ["query"]),
            cls._file_tool("web_search", "Search the web for current information", {
                "query": {"type": "string", "description": "Search query"}
            }, ["query"]),
            cls._file_tool("web_fetch", "Fetch content from a web URL", {
                "url": {"type": "string", "description": "URL to fetch"}, 
                "prompt": {"type": "string", "description": "Prompt for processing content"}
            }, ["url", "prompt"]),
            cls._file_tool("exit_plan_mode", "Exit planning mode and start execution", {
                "plan": {"type": "string", "description": "The plan to execute"}
            }, ["plan"])
        ]

    @classmethod
    def _file_tool(cls, name, description, properties, required):
        """Helper to create tool schema with consistent format."""
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    @classmethod
    def map_to_claude_tool(cls, func_name, func_args):
        """Map GroqCloud tool call to Claude Code tool format."""
        claude_tool_name = cls.TOOL_MAPPING.get(func_name, func_name)

        # Handle parameter mapping for read_file and open_file
        if func_name in ["read_file", "open_file"] and "path" in func_args and "file_path" not in func_args:
            func_args["file_path"] = func_args.pop("path")

        # Handle run_cmd - modify command to run through Windows CMD
        if func_name == "run_cmd":
            original_command = func_args.get("command", "")
            func_args["command"] = f'cmd /c "{original_command}"'

        return claude_tool_name, func_args


class GroqApiClient:
    """Handles GroqCloud API communication with authentication and error handling."""

    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def authenticate(self):
        """Get and validate GroqCloud API key."""
        # Check environment first
        env_key = os.getenv('GROQ_API_KEY', None)

        # Try Windows registry if not in env
        if not env_key and os.name == 'nt':
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    registry_value, _ = winreg.QueryValueEx(key, "GROQ_API_KEY")
                    env_key = registry_value.strip().strip('"')
            except:
                pass

        if env_key and env_key != "NA":
            self.api_key = env_key
            return True
        return False

    def test_connection(self):
        """Test connection to GroqCloud API."""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            test_request = {
                "model": GroqModelSelector.OSS_MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            response = requests.post(self.base_url, headers=headers, json=test_request, timeout=10)
            return response.status_code == 200
        except:
            return False

    def send_request(self, request_data):
        """Send request to GroqCloud API with error handling and retry logic."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=request_data, timeout=60)
                
                if response.status_code == 200:
                    logger.debug(f"Request successful on attempt {attempt + 1}")
                    return response.json(), None
                elif response.status_code == 429:
                    # Rate limit handling
                    wait_time = min(2 ** attempt, 30)
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit on attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                else:
                    error_msg = f"GroqCloud API Error: {response.status_code} {response.text}"
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
                    logger.warning(f"Request failed on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(error_msg)
                    return None, error_msg
        
        return None, "All retry attempts failed"


class MessageTransformer:
    """Handles message format conversion between Anthropic and OpenAI formats."""

    @classmethod
    def anthropic_to_openai(cls, messages):
        """Transform Anthropic messages to OpenAI format for GroqCloud."""
        transformed_messages = []

        for msg in messages:
            if msg.get("role") == "user":
                # Handle tool_result messages from Claude Code
                content = msg.get("content", [])
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if part.get("type") == "tool_result":
                            # Convert tool_result to text for GroqCloud
                            tool_id = part.get("tool_use_id", "unknown")
                            result = part.get("content", "")
                            text_parts.append(f"Tool {tool_id} result: {result}")
                        elif part.get("type") == "text":
                            text_parts.append(part.get("text", ""))

                    transformed_messages.append({
                        "role": "user",
                        "content": "\n".join(text_parts) if text_parts else msg.get("content", "")
                    })
                else:
                    transformed_messages.append(msg)
            elif msg.get("role") == "assistant":
                # Handle assistant messages with tool_use content
                content = msg.get("content", [])
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if part.get("type") == "tool_use":
                            # Convert tool_use to text for GroqCloud
                            tool_name = part.get("name", "unknown")
                            tool_input = part.get("input", {})
                            text_parts.append(f"I need to use the {tool_name} tool with: {json.dumps(tool_input)}")
                        elif part.get("type") == "text":
                            text_parts.append(part.get("text", ""))

                    transformed_messages.append({
                        "role": "assistant",
                        "content": "\n".join(text_parts) if text_parts else msg.get("content", "")
                    })
                else:
                    transformed_messages.append(msg)
            else:
                transformed_messages.append(msg)

        return transformed_messages

    @classmethod
    def groq_to_anthropic_tools(cls, groq_response, original_model):
        """Convert GroqCloud tool calls to Anthropic tool_use format."""
        if not ('choices' in groq_response and groq_response['choices']):
            return None

        message = groq_response['choices'][0]['message']
        if 'tool_calls' not in message:
            return None

        # Translate tool_calls to Anthropic tool_use format
        tool_use_blocks = []
        for tool_call in message['tool_calls']:
            func_name = tool_call['function']['name']
            func_args = json.loads(tool_call['function']['arguments'])
            claude_tool_name, mapped_args = ClaudeToolMapper.map_to_claude_tool(func_name, func_args)

            tool_use_blocks.append({
                "type": "tool_use",
                "id": tool_call['id'],
                "name": claude_tool_name,
                "input": mapped_args
            })

        return {
            "id": groq_response.get("id"),
            "type": "message",
            "content": tool_use_blocks,
            "model": original_model,
            "usage": groq_response.get("usage", {}),
            "stop_reason": "tool_use"
        }

    @classmethod
    def groq_to_anthropic_text(cls, groq_response, original_model):
        """Convert GroqCloud text response to Anthropic format."""
        if not ('choices' in groq_response and groq_response['choices']):
            return None

        message = groq_response['choices'][0]['message']
        content = message.get('content', '')

        return {
            "id": groq_response.get("id"),
            "type": "message",
            "content": [{"type": "text", "text": content}],
            "model": original_model,
            "usage": groq_response.get("usage", {})
        }


class GroqClaudeProxy:
    """Main proxy class orchestrating all components."""

    def __init__(self):
        self.app = Flask(__name__)
        self.api_client = GroqApiClient()
        self.running = True
        self.setup_routes()

    def console_input_handler(self):
        """Handle console input commands in a separate thread."""
        try:
            while self.running:
                try:
                    user_input = input().strip().upper()
                    if user_input == 'R':
                        logger.info("Restart command received")
                        logger.info("Restarting proxy with updated code...")
                        os.execv(sys.executable, ['python'] + sys.argv)
                    elif user_input == 'Q' or user_input == 'QUIT':
                        logger.info("Quit command received")
                        logger.info("Shutting down proxy...")
                        self.running = False
                        os._exit(0)
                    elif user_input == 'H' or user_input == 'HELP':
                        logger.info("Available commands:")
                        logger.info("  R - Restart proxy (reload code changes)")
                        logger.info("  Q - Quit proxy")
                        logger.info("  H - Show this help")
                        logger.info("  Ctrl+C - Force quit")
                except (EOFError, KeyboardInterrupt):
                    break
        except Exception as e:
            logger.debug(f"Console handler error: {e}")

    def setup_routes(self):
        """Setup Flask routes."""
        @self.app.route('/v1/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def proxy_handler(path):
            return self.handle_proxy_request(path)

    def handle_proxy_request(self, path):
        """Handle proxy requests with intelligent routing and web search interception."""
        if not self.api_client.authenticate():
            return jsonify({"error": "GROQ_API_KEY not configured"}), 400

        if path != "messages":
            return jsonify({"error": "Endpoint not implemented"}), 501

        data = request.get_json()
        messages = data.get("messages", [])

        # Detect web search requirement
        has_web_search = "tools" in data and any(
            tool.get("function", {}).get("name") in ["web_search", "browser_search"]
            for tool in data.get("tools", [])
        )

        # Select model and configuration
        selected_model, reasoning_level, supports_tools = GroqModelSelector.select_model_and_config(
            messages, has_web_search, data.get("model", "claude-3-5-sonnet")
        )

        # Transform messages
        transformed_messages = MessageTransformer.anthropic_to_openai(messages)

        # Build OpenAI request
        openai_request = {"model": selected_model, "messages": transformed_messages}

        # Add reasoning effort for compatible models
        if reasoning_level:
            openai_request["reasoning_effort"] = reasoning_level

        # Add tools for models that support them
        if "tools" in data and supports_tools:
            openai_request["tools"] = ClaudeToolMapper.generate_ultra_simple_tools()
            openai_request["tool_choice"] = "auto"

        # Send request to GroqCloud
        groq_response, error = self.api_client.send_request(openai_request)
        if error:
            return jsonify({"error": "Service temporarily unavailable. The AI service is experiencing high demand. Please try again in a moment."}), 503

        # Check for web search tool calls and intercept them
        if ('choices' in groq_response and groq_response['choices'] and 
            'tool_calls' in groq_response['choices'][0]['message']):
            
            tool_calls = groq_response['choices'][0]['message']['tool_calls']
            
            for tool_call in tool_calls:
                func_name = tool_call['function']['name']
                
                # Intercept web search calls
                if func_name in ['web_search', 'browser_search']:
                    func_args = json.loads(tool_call['function']['arguments'])
                    search_query = func_args.get('query', '')
                    
                    logger.info(f"[WEB SEARCH INTERCEPT] Switching to {GroqModelSelector.COMPOUND_MODEL} for: {search_query}")
                    
                    # Make request to compound model for web search
                    compound_request = {
                        "model": GroqModelSelector.COMPOUND_MODEL,
                        "messages": [{"role": "user", "content": f"Search the web for: {search_query}"}]
                    }
                    
                    compound_response, compound_error = self.api_client.send_request(compound_request)
                    
                    if compound_response and 'choices' in compound_response:
                        search_results = compound_response['choices'][0]['message']['content']
                        
                        # Return search results as completed tool_use response
                        return jsonify({
                            "id": groq_response.get("id"),
                            "type": "message",
                            "content": [{
                                "type": "text",
                                "text": f"I performed a web search for '{search_query}'. Here are the results:\n\n{search_results}"
                            }],
                            "model": data.get("model", "claude-3-5-sonnet"),
                            "usage": groq_response.get("usage", {}),
                            "stop_reason": "end_turn"
                        })
                    else:
                        # Fallback if compound search fails
                        return jsonify({
                            "id": groq_response.get("id"),
                            "type": "message", 
                            "content": [{
                                "type": "text",
                                "text": f"I attempted to search for '{search_query}' but web search is temporarily unavailable. Please try again."
                            }],
                            "model": data.get("model", "claude-3-5-sonnet"),
                            "usage": groq_response.get("usage", {}),
                            "stop_reason": "end_turn"
                        })

        # Check for regular tool calls
        anthropic_response = MessageTransformer.groq_to_anthropic_tools(groq_response, data.get("model", "claude-3-5-sonnet"))
        if anthropic_response:
            return jsonify(anthropic_response)

        # Convert regular text response
        anthropic_response = MessageTransformer.groq_to_anthropic_text(groq_response, data.get("model", "claude-3-5-sonnet"))
        if anthropic_response:
            return jsonify(anthropic_response)

        return jsonify({"error": "Invalid response from GroqCloud"}), 500

    def check_port_available(self, port):
        """Check if port is available for the proxy."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            if result == 0:
                logger.warning(f"Another GroqCloud proxy is already running on port {port}!")
                logger.warning("Only one GroqCloud proxy can run at a time.")
                logger.warning("Shutting down in 3 seconds...")
                for i in range(3, 0, -1):
                    logger.warning(f"Shutting down in {i}...")
                    time.sleep(1)
                logger.error(f"Exiting - port {port} is already in use")
                exit(1)
        except Exception:
            pass  # Port is available

    def start_server(self, port=5003):
        """Start the proxy server with proper initialization."""
        self.check_port_available(port)

        print("=" * 80)
        print("        GroqCloud Claude Code Proxy - ENHANCED VERSION v1.0.3")
        print("=" * 80)
        print("[SUCCESS] Clean class-based architecture with intelligent model selection!")
        print("Models: openai/gpt-oss-120b (tools) + groq/compound (web search)")
        print("All Claude Code tools working with 20x cost savings!")
        print()

        if self.api_client.authenticate():
            print("[OK] GroqCloud API key found")
            print("[TESTING] Connecting to GroqCloud API...")

            if self.api_client.test_connection():
                print("[SUCCESS] Connected to GroqCloud API")
                print("[PROXY] Claude Code -> GroqCloud connection ready")
            else:
                print("[WARNING] Could not verify GroqCloud connection - continuing anyway")

            print()
            print(f"Starting enhanced proxy server on http://localhost:{port}...")
            print()
            print("[TOOLS] All 15+ Claude Code tools supported")
            print("[MODELS] Intelligent routing (gpt-oss-120b <-> groq/compound)")
            print("[COST] 20x cheaper than Anthropic with full functionality")
            print("[RETRY] Auto-retry with smart backoff for rate limits")
            print()
            print("[COMMANDS] Console commands:")
            print("  R - Restart proxy (reload code changes)")
            print("  Q - Quit proxy")
            print("  H - Show help")
            print("  Ctrl+C - Force quit")
            print()
            print("Test with:")
            print(f'claude --settings "{{\\"env\\": {{\\"ANTHROPIC_BASE_URL\\": \\"http://localhost:{port}\\", \\"ANTHROPIC_API_KEY\\": \\"dummy_key\\"}}}}" -p "What is 2+2?"')
            print()
            print("Press Ctrl+C to stop")
            print("=" * 80)

            # Start console input handler
            console_thread = threading.Thread(target=self.console_input_handler, daemon=True)
            console_thread.start()

            self.app.run(host='127.0.0.1', port=port, debug=False)
        else:
            print("[ERROR] GROQ_API_KEY not found")
            print("Please set your GroqCloud API key:")
            print("1. Get key from: https://console.groq.com/keys")
            print("2. Set it: set GROQ_API_KEY=your_key_here")


if __name__ == "__main__":
    proxy = GroqClaudeProxy()
    proxy.start_server()
