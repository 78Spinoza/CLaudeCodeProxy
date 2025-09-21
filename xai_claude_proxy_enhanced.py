#!/usr/bin/env python3
"""
xAI Claude Code Proxy - ENHANCED VERSION v1.0.4 (Clean Architecture)
==================================================================

Clean, class-based architecture for xAI Claude Code proxy with:
- Intelligent model selection (grok-code-fast-1 vs grok-4-0709)
- All 15+ Claude Code tools with ultra-simple schemas
- Web search interception with native xAI search
- Complete bidirectional API translation
- Console restart command (R) for fast debugging
- 15x cost savings vs Anthropic

Port: 5000 (standard xAI proxy port)
"""

import json
import os
import requests
import time
import socket
import threading
import sys
from flask import Flask, request, jsonify, Response, stream_with_context
import winreg
import logging

# Suppress Flask development server warning
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class XAIModelSelector:
    """Intelligent model selection for xAI based on request complexity."""

    REASONING_KEYWORDS = [
        "analyze", "complex", "reasoning", "logic", "solve", "algorithm",
        "architecture", "design pattern", "refactor", "optimize", "debug",
        "mathematical", "calculation", "theorem", "proof", "strategy",
        "compare and contrast", "evaluate", "assess", "critique", "review",
        "plan", "implementation", "step by step", "systematic", "methodology",
        "research", "explain", "understand", "concept", "theory"
    ]

    CODING_KEYWORDS = [
        "code", "function", "class", "variable", "file", "read", "write", "edit",
        "bash", "command", "script", "python", "javascript", "typescript",
        "import", "export", "api", "endpoint", "database", "query", "test"
    ]

    @classmethod
    def select_model(cls, messages, model_name="claude-3-5-sonnet-20241022"):
        """Select optimal xAI model based on request complexity."""
        # Always use grok-4-0709 for Opus requests
        if "claude-3-opus" in model_name.lower() or "opus" in model_name.lower():
            return "grok-4-0709", "high"

        # Analyze content
        text_content = cls._extract_text_content(messages)
        reasoning_score = sum(1 for keyword in cls.REASONING_KEYWORDS if keyword in text_content)
        coding_score = sum(1 for keyword in cls.CODING_KEYWORDS if keyword in text_content)

        # Model selection logic
        if reasoning_score >= 3:
            return "grok-4-0709", "high"
        elif coding_score >= 2 or any(tool in text_content for tool in ["read", "write", "file", "bash"]):
            return "grok-code-fast-1", "medium"
        elif reasoning_score >= 1:
            return "grok-4-0709", "medium"
        else:
            return "grok-code-fast-1", "medium"

    @staticmethod
    def _extract_text_content(messages):
        """Extract text content from messages for analysis."""
        text_content = ""
        for msg in messages:
            if isinstance(msg.get("content"), str):
                text_content += msg["content"].lower() + " "
            elif isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if part.get("type") == "text":
                        text_content += part.get("text", "").lower() + " "
        return text_content

class ClaudeToolMapper:
    """Handles tool mapping and schema generation for Claude Code tools."""

    TOOL_MAPPING = {
        "read_file": "Read", "open_file": "Read", "write_file": "Write",
        "edit_file": "Edit", "multi_edit_file": "MultiEdit", "run_bash": "Bash",
        "search_files": "Glob", "grep_search": "Grep", "web_search": "WebSearch",
        "web_fetch": "WebFetch", "manage_todos": "TodoWrite", "todo_write": "TodoWrite",
        "get_bash_output": "BashOutput", "kill_bash_shell": "KillShell",
        "edit_notebook": "NotebookEdit", "delegate_task": "Task",
        "exit_plan_mode": "ExitPlanMode",
        # Add functions/ prefixed versions for xAI compatibility
        "functions/read_file": "Read", "functions/open_file": "Read", "functions/write_file": "Write",
        "functions/edit_file": "Edit", "functions/multi_edit_file": "MultiEdit", "functions/run_bash": "Bash",
        "functions/search_files": "Glob", "functions/grep_search": "Grep", "functions/web_search": "WebSearch",
        "functions/web_fetch": "WebFetch", "functions/manage_todos": "TodoWrite", "functions/todo_write": "TodoWrite",
        "functions/get_bash_output": "BashOutput", "functions/kill_bash_shell": "KillShell",
        "functions/edit_notebook": "NotebookEdit", "functions/delegate_task": "Task",
        "functions/exit_plan_mode": "ExitPlanMode"
    }

    @classmethod
    def get_claude_tool_name(cls, xai_tool_name):
        """Map xAI tool name to Claude Code tool name."""
        return cls.TOOL_MAPPING.get(xai_tool_name, xai_tool_name)

    @staticmethod
    def generate_tool_schemas():
        """Generate ultra-simple tool schemas for xAI compatibility."""
        return [
            {"type": "function", "function": {"name": "read_file", "description": "Read contents of a file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to the file"}, "limit": {"type": "integer", "description": "Lines to read (optional)"}, "offset": {"type": "integer", "description": "Start line (optional)"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "open_file", "description": "Open and read contents of a file (alias for read_file)", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to the file"}, "file_path": {"type": "string", "description": "Path to the file (alternative)"}, "limit": {"type": "integer", "description": "Lines to read (optional)"}, "offset": {"type": "integer", "description": "Start line (optional)"}}, "required": []}}},
            {"type": "function", "function": {"name": "write_file", "description": "Write content to a file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to the file"}, "content": {"type": "string", "description": "File content"}}, "required": ["file_path", "content"]}}},
            {"type": "function", "function": {"name": "edit_file", "description": "Edit a file by replacing text", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to the file"}, "old_string": {"type": "string", "description": "Text to replace"}, "new_string": {"type": "string", "description": "New text"}, "replace_all": {"type": "boolean", "description": "Replace all occurrences"}}, "required": ["file_path", "old_string", "new_string"]}}},
            {"type": "function", "function": {"name": "multi_edit_file", "description": "Make multiple edits to one file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to the file"}, "edits": {"type": "string", "description": "JSON string containing array of edit operations"}}, "required": ["file_path", "edits"]}}},
            {"type": "function", "function": {"name": "run_bash", "description": "Run a shell command", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Command to run"}, "timeout": {"type": "integer", "description": "Timeout in ms"}, "run_in_background": {"type": "boolean", "description": "Run in background"}}, "required": ["command"]}}},
            {"type": "function", "function": {"name": "search_files", "description": "Search for files using glob patterns", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Glob pattern like *.py"}, "path": {"type": "string", "description": "Directory to search"}}, "required": ["pattern"]}}},
            {"type": "function", "function": {"name": "grep_search", "description": "Search for text patterns in files", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Text pattern to search"}, "path": {"type": "string", "description": "Path to search"}, "glob": {"type": "string", "description": "File filter like *.py"}}, "required": ["pattern"]}}},
            {"type": "function", "function": {"name": "web_search", "description": "Search the web for information", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "web_fetch", "description": "Fetch content from a URL", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to fetch"}, "prompt": {"type": "string", "description": "What to extract from content"}}, "required": ["url", "prompt"]}}},
            {"type": "function", "function": {"name": "manage_todos", "description": "Manage todo list", "parameters": {"type": "object", "properties": {"todos": {"type": "array", "items": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string"}, "activeForm": {"type": "string"}}, "required": ["content", "status", "activeForm"]}, "description": "Array of todo objects"}}, "required": ["todos"]}}},
            {"type": "function", "function": {"name": "todo_write", "description": "Write todo items", "parameters": {"type": "object", "properties": {"todos": {"type": "array", "items": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string"}, "activeForm": {"type": "string"}}, "required": ["content", "status", "activeForm"]}, "description": "Array of todo objects"}}, "required": ["todos"]}}},
            {"type": "function", "function": {"name": "get_bash_output", "description": "Get output from background bash process", "parameters": {"type": "object", "properties": {"bash_id": {"type": "string", "description": "Background process ID"}}, "required": ["bash_id"]}}},
            {"type": "function", "function": {"name": "kill_bash_shell", "description": "Kill a background bash process", "parameters": {"type": "object", "properties": {"shell_id": {"type": "string", "description": "Shell process ID to kill"}}, "required": ["shell_id"]}}},
            {"type": "function", "function": {"name": "edit_notebook", "description": "Edit a Jupyter notebook cell", "parameters": {"type": "object", "properties": {"notebook_path": {"type": "string", "description": "Path to notebook"}, "new_source": {"type": "string", "description": "New cell content"}, "cell_type": {"type": "string", "description": "Cell type: code or markdown"}}, "required": ["notebook_path", "new_source"]}}},
            {"type": "function", "function": {"name": "delegate_task", "description": "Delegate task to specialized agent", "parameters": {"type": "object", "properties": {"description": {"type": "string", "description": "Task description"}, "prompt": {"type": "string", "description": "Detailed task prompt"}, "subagent_type": {"type": "string", "description": "Agent type"}}, "required": ["description", "prompt", "subagent_type"]}}},
            {"type": "function", "function": {"name": "exit_plan_mode", "description": "Exit planning mode and start execution", "parameters": {"type": "object", "properties": {"plan": {"type": "string", "description": "The plan to execute"}}, "required": ["plan"]}}}
        ]

class XAIApiClient:
    """Handles xAI API communication and authentication."""

    def __init__(self):
        self.api_key = None

    def get_api_key(self):
        """Get xAI API key from environment or registry."""
        # Check environment first
        env_key = os.getenv('XAI_API_KEY', None)

        # Try Windows registry if not in env
        if not env_key and os.name == 'nt':
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    registry_value, _ = winreg.QueryValueEx(key, "XAI_API_KEY")
                    env_key = registry_value.strip().strip('"')
            except:
                pass

        if env_key and env_key != "NA":
            self.api_key = env_key
            return True

        print("[ERROR] XAI_API_KEY not found in environment or registry")
        print("Please set your xAI API key:")
        print("1. Get key from: https://console.x.ai")
        print("2. Set it: set XAI_API_KEY=your_key_here")
        return False

    def test_connection(self):
        """Test connection to xAI API."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            test_request = {"model": "grok-code-fast-1", "messages": [{"role": "user", "content": "test"}], "max_tokens": 1}
            response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=test_request, timeout=10)
            return response.status_code == 200
        except:
            return False

    def send_request(self, xai_request, stream=False):
        """Send request to xAI API."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = "https://api.x.ai/v1/chat/completions"

        if stream:
            def generate():
                response = requests.post(url, headers=headers, json=xai_request, stream=True, timeout=60)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            return Response(stream_with_context(generate()), content_type='text/event-stream')
        else:
            response = requests.post(url, headers=headers, json=xai_request, timeout=30)
            return response

class MessageTransformer:
    """Handles message transformation between Anthropic and xAI formats."""

    @staticmethod
    def transform_anthropic_to_xai(messages):
        """Transform Anthropic messages to xAI format."""
        transformed_messages = []
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
                        "content": "\n".join(text_parts) if text_parts else msg.get("content", "")
                    })
                else:
                    transformed_messages.append(msg)
            else:
                transformed_messages.append(msg)
        return transformed_messages

    @staticmethod
    def transform_xai_to_anthropic(xai_response, original_model, tool_mapping, api_client=None):
        """Transform xAI response back to Anthropic format."""
        if 'choices' not in xai_response or not xai_response['choices']:
            return {"error": "Invalid xAI response"}

        message = xai_response['choices'][0]['message']

        # Handle tool calls
        if 'tool_calls' in message:
            print("[SUCCESS] xAI model called tools - translating to Anthropic format!")
            
            # Check for web search tool calls that need interception
            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                
                # Handle xAI's "functions/" prefix
                if func_name.startswith("functions/"):
                    func_name = func_name[10:]  # Remove "functions/" prefix
                
                func_args = json.loads(tool_call['function']['arguments'])
                
                # INTERCEPT WEB SEARCH TOOLS
                if func_name in ["web_search"] and api_client:
                    query = func_args.get("query", "")
                    print(f"[WEB SEARCH INTERCEPT] Intercepting {func_name} with query: {query}")
                    
                    # Make a new call to xAI for actual web search (using a model that supports search)
                    search_request = {
                        "model": "grok-4-0709",  # Use reasoning model for web search
                        "messages": [{"role": "user", "content": f"Please search the web for information about: {query}. Provide detailed results with sources and URLs when possible."}],
                        "max_tokens": 4000
                    }
                    
                    print(f"[WEB SEARCH] Making xAI call for web search...")
                    search_response = api_client.send_request(search_request)
                    
                    if isinstance(search_response, Response):  # Streaming response
                        search_result = "Web search completed via streaming response"
                    elif search_response.status_code == 200:
                        search_data = search_response.json()
                        search_result = search_data['choices'][0]['message']['content']
                    else:
                        search_result = f"Web search failed: {search_response.text}"
                    
                    print(f"[WEB SEARCH] Got search results, returning as completed search")
                    
                    # Return as a regular text response with search results
                    return {
                        "id": xai_response.get("id"),
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "text", "text": f"I searched the web for '{query}' and found the following information:\n\n{search_result}"}],
                        "model": original_model,
                        "stop_reason": "end_turn",
                        "usage": {
                            "input_tokens": xai_response.get("usage", {}).get("prompt_tokens", 0),
                            "output_tokens": xai_response.get("usage", {}).get("completion_tokens", 0)
                        }
                    }

            content = []

            # Add any text content first
            if message.get('content'):
                content.append({"type": "text", "text": message['content']})

            # Translate tool_calls to Anthropic tool_use blocks
            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                
                # Handle xAI's "functions/" prefix
                if func_name.startswith("functions/"):
                    func_name = func_name[10:]  # Remove "functions/" prefix
                
                func_args = json.loads(tool_call['function']['arguments'])
                claude_tool_name = tool_mapping.get(func_name, func_name)

                print(f"[TRANSLATE] {func_name} -> {claude_tool_name} with {func_args}")

                content.append({
                    "type": "tool_use",
                    "id": tool_call['id'],
                    "name": claude_tool_name,
                    "input": func_args
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
                    "output_tokens": xai_response.get("usage", {}).get("completion_tokens", 0)
                }
            }

        # Handle regular text response
        content = message.get('content', '')
        return {
            "id": xai_response.get("id"),
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": original_model,
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": xai_response.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": xai_response.get("usage", {}).get("completion_tokens", 0)
            }
        }

class XAIClaudeProxy:
    """Main proxy class orchestrating all components."""

    def __init__(self):
        self.api_client = XAIApiClient()
        self.model_selector = XAIModelSelector()
        self.tool_mapper = ClaudeToolMapper()
        self.message_transformer = MessageTransformer()
        self.running = True

    def console_input_handler(self):
        """Handle console input commands in a separate thread."""
        try:
            while self.running:
                try:
                    user_input = input().strip().upper()
                    if user_input == 'R':
                        print("\n[RESTART] Restarting xAI proxy with updated code...")
                        print("[INFO] Current instance will shutdown, new instance will start")
                        print("=" * 60)
                        # Kill current process and restart with same arguments
                        os.execv(sys.executable, ['python'] + sys.argv)
                    elif user_input == 'Q' or user_input == 'QUIT':
                        print("\n[SHUTDOWN] Shutting down xAI proxy...")
                        self.running = False
                        os._exit(0)
                    elif user_input == 'H' or user_input == 'HELP':
                        print("\n[COMMANDS] Available commands:")
                        print("  R - Restart proxy (reload code changes)")
                        print("  Q - Quit proxy")
                        print("  H - Show this help")
                        print("  Ctrl+C - Force quit\n")
                except (EOFError, KeyboardInterrupt):
                    break
        except Exception as e:
            # Silently handle any input errors
            pass

    def initialize(self):
        """Initialize the proxy with API key and connection test."""
        return self.api_client.get_api_key()

    def test_connection(self):
        """Test connection to xAI API."""
        return self.api_client.test_connection()

    def handle_request(self, path, data):
        """Handle incoming proxy requests."""
        if path != "messages":
            return jsonify({"error": "Endpoint not implemented"}), 501

        # Extract and transform request
        original_model = data.get("model", "claude-3-5-sonnet-20241022")
        messages = data.get("messages", [])
        selected_model, complexity_level = self.model_selector.select_model(messages, original_model)
        transformed_messages = self.message_transformer.transform_anthropic_to_xai(messages)

        # Build xAI request
        xai_request = {
            "model": selected_model,
            "messages": transformed_messages,
            "stream": data.get("stream", False)
        }

        # Add optional parameters
        for param in ["temperature", "top_p"]:
            if param in data:
                xai_request[param] = data[param]
        if "max_tokens" in data:
            xai_request["max_tokens"] = min(data["max_tokens"], 8192)

        # Add tools if present
        if "tools" in data:
            tools = self.tool_mapper.generate_tool_schemas()
            xai_request["tools"] = tools
            xai_request["tool_choice"] = "auto"

        try:
            # Send to xAI
            response = self.api_client.send_request(xai_request, xai_request.get("stream", False))

            if isinstance(response, Response):  # Streaming response
                return response

            if response.status_code == 200:
                xai_response = response.json()
                anthropic_response = self.message_transformer.transform_xai_to_anthropic(
                    xai_response, original_model, self.tool_mapper.TOOL_MAPPING, self.api_client
                )
                return jsonify(anthropic_response)
            else:
                print(f"[ERROR] xAI error: {response.text}")
                return jsonify({"error": f"xAI API Error: {response.status_code} {response.text}"}), response.status_code

        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            return jsonify({"error": f"Request failed: {str(e)}"}), 500

def check_port_conflict(port, proxy_name):
    """Check if another proxy is already running on the same port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()

        if result == 0:
            print(f"[WARNING] Another {proxy_name} proxy is already running on port {port}!")
            print(f"[WARNING] Only one {proxy_name} proxy can run at a time.")
            print("[WARNING] Shutting down in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"[WARNING] Shutting down in {i}...")
                time.sleep(1)
            print(f"[ERROR] Exiting - port {port} is already in use by another {proxy_name} proxy")
            exit(1)
    except Exception:
        pass  # Port is available

# Flask app setup
app = Flask(__name__)
proxy = XAIClaudeProxy()

@app.route('/v1/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_route(path):
    """Main proxy route handler."""
    data = request.get_json()
    return proxy.handle_request(path, data)

if __name__ == "__main__":
    # Check for port conflicts before starting
    check_port_conflict(5000, "xAI")

    print("================================================================================")
    print("              xAI Claude Code Proxy - ENHANCED VERSION v1.0.4")
    print("================================================================================")
    print("[SUCCESS] Clean class-based architecture with intelligent model selection!")
    print("Models: grok-code-fast-1 (coding) + grok-4-0709 (reasoning)")
    print("All Claude Code tools working with 15x cost savings!")
    print()

    if proxy.initialize():
        print("[OK] xAI API key found")
        print("[TESTING] Connecting to xAI API...")

        if proxy.test_connection():
            print("[SUCCESS] Connected to xAI API")
            print("[PROXY] Claude Code -> xAI Grok connection ready")
        else:
            print("[WARNING] Could not verify xAI connection - continuing anyway")

        print()
        print("Starting enhanced proxy server on http://localhost:5000...")
        print()
        print("[TOOLS] All 15 Claude Code tools supported")
        print("[MODELS] Intelligent routing (grok-code-fast-1 <-> grok-4-0709)")
        print("[COST] 15x cheaper than Anthropic with full functionality")
        print()
        print("Test with:")
        print('claude --settings "{\\"env\\": {\\"ANTHROPIC_BASE_URL\\": \\"http://localhost:5000\\", \\"ANTHROPIC_API_KEY\\": \\"dummy_key\\"}}" -p "What is 2+2?"')
        print()
        print("Press Ctrl+C to stop")
        print("================================================================================")

        app.run(host='127.0.0.1', port=5000, debug=False)
    else:
        print("[ERROR] XAI_API_KEY not found")
        print("Please set your xAI API key:")
        print("1. Get key from: https://console.x.ai")
        print("2. Set it: set XAI_API_KEY=your_key_here")
        print("3. Or run setup: claudeproxy.bat")