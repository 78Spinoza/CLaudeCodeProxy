#!/usr/bin/env python3
"""
Adapter for Baseten Claude Code Proxy to be used with the shared BaseClaudeProxy.
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
from proxy_common import ClaudeToolMapper, MessageTransformer, BaseApiClient, BaseModelSelector, PROXY_VERSION

logger = logging.getLogger(__name__)


class BasetenModelSelector(BaseModelSelector):
    """Baseten-specific model selector inheriting from BaseModelSelector."""

    OSS_MODEL = "openai/gpt-oss-120b"      # Only model available on Baseten

    def __init__(self):
        super().__init__(
            reasoning_keywords=[
                "analyze", "complex", "reasoning", "logic", "solve", "algorithm",
                "architecture", "design pattern", "refactor", "optimize", "debug",
                "mathematical", "calculation", "theorem", "proof", "strategy",
                "compare and contrast", "evaluate", "assess", "critique", "review",
                "plan", "implementation", "step by step", "systematic", "methodology"
            ]
        )

    @classmethod
    def select_model_and_config(cls, messages, has_web_search=False, model_name="claude-3-5-sonnet"):
        """Always use GPT-OSS-120B - Baseten doesn't have web search or compound models."""
        logger.debug(f"[BASETEN] Using {cls.OSS_MODEL} for all requests")
        return cls.OSS_MODEL, None, True  # Always support tools


class BasetenApiClient(BaseApiClient):
    """Handles Baseten API communication with authentication and error handling."""

    def __init__(self):
        super().__init__(
            base_url="https://model-gpt-oss-120b.api.baseten.co/production/predict",
            env_var_name="BASETEN_API_KEY",
            provider_name="Baseten",
            default_test_model="openai/gpt-oss-120b"
        )


class BasetenAdapter:
    """Adapter exposing the interface required by BaseClaudeProxy for Baseten."""

    def __init__(self):
        self.name = "Baseten"  # Required by BaseClaudeProxy
        self.api_client = BasetenApiClient()
        self.model_selector = BasetenModelSelector()
        self.tool_mapper = ClaudeToolMapper()
        self.message_transformer = MessageTransformer()

        # Log version and OS detection for debugging
        print(f"[Baseten] Claude Code Proxy v{PROXY_VERSION} ready")
        self.tool_mapper.log_os_detection("Baseten")

    def authenticate(self) -> bool:
        """Validate the API key is present."""
        return self.api_client.authenticate()

    def test_connection(self) -> bool:
        """Test connection to Baseten API."""
        return self.api_client.test_connection()

    def handle_proxy_request(self, data: dict):
        """Process an incoming request payload and return a Flask response."""

        # No web search support on Baseten - just log if requested
        has_web_search = "tools" in data and any(
            tool.get("function", {}).get("name") in ["web_search", "browser_search"]
            for tool in data.get("tools", [])
        )
        if has_web_search:
            logger.warning("[BASETEN] Web search requested but not supported - using standard model")

        # Select model (always GPT-OSS-120B)
        messages = data.get("messages", [])
        selected_model, reasoning_level, supports_tools = self.model_selector.select_model_and_config(
            messages, has_web_search, data.get("model", "claude-3-5-sonnet")
        )

        # Transform messages
        transformed_messages = self.message_transformer.anthropic_to_openai(messages)

        # Build OpenAI request
        openai_request = {"model": selected_model, "messages": transformed_messages}

        # Add tools for models that support them
        if "tools" in data and supports_tools:
            tools_schema = self.tool_mapper.generate_ultra_simple_tools()
            # Debug logging to see what schema is being sent
            for tool in tools_schema:
                if tool["function"]["name"] == "edit_file":
                    logger.debug(f"[BASETEN SCHEMA] edit_file schema: {tool['function']['parameters']}")
            openai_request["tools"] = tools_schema
            openai_request["tool_choice"] = "auto"

        # Send request to Baseten
        baseten_response, error = self.api_client.send_request(openai_request)
        if error:
            return jsonify({"error": "Service temporarily unavailable. The AI service is experiencing high demand. Please try again in a moment."}), 503

        # Handle web search requests by informing user it's not supported
        if ('choices' in baseten_response and baseten_response['choices'] and
            'tool_calls' in baseten_response['choices'][0]['message']):

            tool_calls = baseten_response['choices'][0]['message']['tool_calls']

            for tool_call in tool_calls:
                func_name = tool_call['function']['name']

                # Inform user web search is not supported
                if func_name in ['web_search', 'browser_search']:
                    func_args = json.loads(tool_call['function']['arguments'])
                    search_query = func_args.get('query', '')

                    logger.warning(f"[BASETEN] Web search not supported: {search_query}")
                    return jsonify({
                        "id": baseten_response.get("id"),
                        "type": "message",
                        "content": [{
                            "type": "text",
                            "text": f"I cannot perform web searches through the Baseten provider. The query '{search_query}' would require switching to a provider that supports web search (like Groq compound model)."
                        }],
                        "model": data.get("model", "claude-3-5-sonnet"),
                        "usage": baseten_response.get("usage", {}),
                        "stop_reason": "end_turn"
                    })

        # Check for regular tool calls
        anthropic_response = self.message_transformer.groq_to_anthropic_tools(baseten_response, data.get("model", "claude-3-5-sonnet"))
        if anthropic_response:
            return jsonify(anthropic_response)

        # Convert regular text response
        anthropic_response = self.message_transformer.groq_to_anthropic_text(baseten_response, data.get("model", "claude-3-5-sonnet"))
        if anthropic_response:
            return jsonify(anthropic_response)

        return jsonify({"error": "Invalid response from Baseten"}), 500