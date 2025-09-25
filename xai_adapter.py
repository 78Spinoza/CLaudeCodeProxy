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
from proxy_common import ClaudeToolMapper, MessageTransformer, BaseApiClient, PROXY_VERSION

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


class XAIApiClient(BaseApiClient):
    """Handles xAI API communication and authentication with robust retry logic."""

    def __init__(self):
        super().__init__(
            base_url="https://api.x.ai/v1/chat/completions",
            env_var_name="XAI_API_KEY", 
            provider_name="xAI",
            default_test_model="grok-code-fast-1"
        )


class XAIAdapter:
    """Adapter exposing the interface required by BaseClaudeProxy for xAI."""

    def __init__(self):
        self.name = "xAI"  # Required by BaseClaudeProxy
        self.api_client = XAIApiClient()
        self.model_selector = XAIModelSelector()
        self.tool_mapper = ClaudeToolMapper()
        self.message_transformer = MessageTransformer()

        # Log version and OS detection for debugging
        print(f"[xAI] Claude Code Proxy v{PROXY_VERSION} ready")
        self.tool_mapper.log_os_detection("xAI")

    def authenticate(self) -> bool:
        """Validate the API key is present."""
        return self.api_client.authenticate()

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
            response, error = self.api_client.send_request(xai_payload, xai_payload.get("stream", False))
            
            # Streaming responses are already a Flask ``Response`` object
            if isinstance(response, Response):
                return response

            if error:
                logger.error(f"xAI API Error: {error}")
                return jsonify({"error": "Service temporarily unavailable. The AI service is experiencing high demand. Please try again in a moment."}), 503

            if response:
                anthropic_resp = self.message_transformer.transform_xai_to_anthropic(
                    response,
                    original_model,
                    self.tool_mapper.TOOL_MAPPING,
                    self.api_client
                )
                return jsonify(anthropic_resp)
            else:
                return jsonify({"error": "Service temporarily unavailable. The AI service is experiencing high demand. Please try again in a moment."}), 503
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({"error": "Service temporarily unavailable. The AI service is experiencing high demand. Please try again in a moment."}), 503
