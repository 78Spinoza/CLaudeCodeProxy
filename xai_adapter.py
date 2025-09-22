#!/usr/bin/env python3
"""
Adapter for xAI Claude Code Proxy to be used with the shared BaseClaudeProxy.
"""

import json
import os
import sys
import logging
import winreg
import requests
import time
from flask import jsonify, Response, stream_with_context

# Import shared utilities
from proxy_common import ClaudeToolMapper, MessageTransformer

logger = logging.getLogger(__name__)


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
        "code", "function", "class", "variable", "file", "read", "write",
        "edit", "bash", "command", "script", "python", "javascript",
        "typescript", "import", "export", "api", "endpoint", "database",
        "query", "test"
    ]

    @classmethod
    def select_model(cls, messages, model_name="claude-3-5-sonnet-20241022"):
        """Select optimal xAI model based on request complexity."""
        # Always use grok-4-0709 for Opus requests
        if "claude-3-opus" in model_name.lower() or "opus" in model_name.lower():
            logger.info(f"[REASONING] Detected Opus request: {model_name} -> grok-4-0709")
            return "grok-4-0709", "high"

        # Analyze content
        text_content = cls._extract_text_content(messages)
        reasoning_score = sum(1 for kw in cls.REASONING_KEYWORDS if kw in text_content)
        coding_score = sum(1 for kw in cls.CODING_KEYWORDS if kw in text_content)

        if reasoning_score >= 3:
            logger.debug(f"[MODEL] High reasoning complexity detected -> grok-4-0709")
            return "grok-4-0709", "high"
        elif coding_score >= 2 or any(tool in text_content for tool in ["read", "write", "file", "bash"]):
            logger.debug(f"[MODEL] Coding task detected -> grok-code-fast-1")
            return "grok-code-fast-1", "medium"
        elif reasoning_score >= 1:
            logger.debug(f"[MODEL] Medium reasoning complexity -> grok-4-0709")
            return "grok-4-0709", "medium"
        else:
            logger.debug(f"[MODEL] Standard task -> grok-code-fast-1")
            return "grok-code-fast-1", "medium"

    @staticmethod
    def _extract_text_content(messages):
        """Extract text content from messages for analysis."""
        text = ""
        for msg in messages:
            if isinstance(msg.get("content"), str):
                text += msg["content"].lower() + " "
            elif isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if part.get("type") == "text":
                        text += part.get("text", "").lower() + " "
        return text


class XAIApiClient(BaseApiClient):\n    def __init__(self):\n        super().__init__('xAI', 'XAI_API_KEY', 'https://api.x.ai/v1/chat/completions')\n\n    def send_request(self, request_data, stream=False):\n        # Use base class but customize model if needed\n        return super().send_request(request_data, stream)
    """Handles xAI API communication and authentication with robust retry logic."""

    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.x.ai/v1/chat/completions"

            """Get xAI API key from environment or Windows registry."""
        env_key = os.getenv('XAI_API_KEY')
        if not env_key and os.name == 'nt':
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    registry_value, _ = winreg.QueryValueEx(key, "XAI_API_KEY")
                    env_key = registry_value.strip().strip('"')
            except Exception:
                pass
        if env_key and env_key != "NA":
            self.api_key = env_key
            return True
        logger.error("[ERROR] XAI_API_KEY not found in environment or registry")
        return False

            """Test a minimal request to verify the key works."""
        if not self.api_key:
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            test_req = {"model": "grok-code-fast-1", "messages": [{"role": "user", "content": "test"}], "max_tokens": 1}
            resp = requests.post(self.base_url, headers=headers, json=test_req, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False

            """Send request to xAI endpoint with robust retry logic and error handling."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        if stream:
            def generate():
                response = requests.post(self.base_url, headers=headers, json=xai_request, stream=True, timeout=60)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            return Response(stream_with_context(generate()), content_type='text/event-stream')

        # Non-streaming requests with retry logic
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=xai_request, timeout=60)
                
                if response.status_code == 200:
                    logger.debug(f"xAI request successful on attempt {attempt + 1}")
                    return response
                elif response.status_code == 429:
                    # Rate limit handling
                    wait_time = min(2 ** attempt, 30)
                    if attempt < max_retries - 1:
                        logger.warning(f"xAI rate limit hit on attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"xAI rate limit exceeded after {max_retries} attempts")
                        return response
                elif response.status_code >= 500:
                    # Server errors - retry
                    wait_time = min(2 ** attempt, 15)
                    if attempt < max_retries - 1:
                        logger.warning(f"xAI server error {response.status_code} on attempt {attempt + 1}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"xAI server error persists after {max_retries} attempts: {response.status_code}")
                        return response
                else:
                    # Client errors (4xx) - don't retry
                    logger.error(f"xAI client error: {response.status_code} {response.text}")
                    return response
                    
            except requests.exceptions.ConnectionError as e:
                wait_time = min(2 ** attempt, 15)
                if attempt < max_retries - 1:
                    logger.warning(f"xAI connection dropped on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"xAI connection failed after {max_retries} attempts: {e}")
                    raise
            except requests.exceptions.Timeout as e:
                wait_time = min(2 ** attempt, 15)
                if attempt < max_retries - 1:
                    logger.warning(f"xAI timeout on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"xAI timeout after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                wait_time = min(2 ** attempt, 15)
                if attempt < max_retries - 1:
                    logger.warning(f"xAI request failed on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"xAI request failed after {max_retries} attempts: {e}")
                    raise
        
        raise Exception("All retry attempts failed")


class XAIAdapter:
    """Adapter exposing the interface required by BaseClaudeProxy for xAI."""

    def __init__(self):
        self.api_client = XAIApiClient()
        self.model_selector = XAIModelSelector()
        self.tool_mapper = ClaudeToolMapper()
        self.message_transformer = MessageTransformer()

    def authenticate(self) -> bool:
        """Validate the API key is present."""
        return self.api_client.get_api_key()

    def test_connection(self) -> bool:
        """Test connection to xAI API."""
        return self.api_client.test_connection()

    def handle_proxy_request(self, data: dict):
        """Process an incoming request payload and return a Flask response.

        This mirrors the logic previously found in ``XAIClaudeProxy.handle_request``.
        """
        # Original model name from the caller (defaults to a Claude model name)
        original_model = data.get("model", "claude-3-5-sonnet-20241022")
        messages = data.get("messages", [])

        # Choose the appropriate xAI model based on content
        selected_model, _ = self.model_selector.select_model(messages, original_model)
        transformed_messages = self.message_transformer.transform_anthropic_to_xai(messages)

        # Build the request payload for xAI
        xai_payload = {
            "model": selected_model,
            "messages": transformed_messages,
            "stream": data.get("stream", False)
        }
        # Copy through any standard parameters the user supplied
        for param in ["temperature", "top_p"]:
            if param in data:
                xai_payload[param] = data[param]
        if "max_tokens" in data:
            xai_payload["max_tokens"] = min(data["max_tokens"], 8192)
        
        # Attach tool schemas if the caller requested tools
        if "tools" in data:
            tools = self.tool_mapper.generate_ultra_simple_tools()  # FIXED: Use correct method name
            xai_payload["tools"] = tools
            xai_payload["tool_choice"] = "auto"

        try:
            logger.info(f"Sending request to xAI using model: {selected_model}")
            response = self.api_client.send_request(xai_payload, xai_payload.get("stream", False))
            
            # Streaming responses are already a Flask ``Response`` object
            if isinstance(response, Response):
                return response

            if response.status_code == 200:
                xai_response = response.json()
                anthropic_resp = self.message_transformer.transform_xai_to_anthropic(
                    xai_response,
                    original_model,
                    self.tool_mapper.TOOL_MAPPING,
                    self.api_client
                )
                return jsonify(anthropic_resp)
            else:
                error_msg = f"xAI API Error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return jsonify({"error": "Service temporarily unavailable. The AI service is experiencing high demand. Please try again in a moment."}), 503
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({"error": "Service temporarily unavailable. The AI service is experiencing high demand. Please try again in a moment."}), 503
