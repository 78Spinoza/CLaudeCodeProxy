#!/usr/bin/env python3
"""
Adapter for GroqCloud Claude Code Proxy to be used with the shared BaseClaudeProxy.
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
from proxy_common import ClaudeToolMapper, MessageTransformer, BaseApiClient, BaseModelSelector

logger = logging.getLogger(__name__)


class GroqModelSelector(BaseModelSelector):
    """GroqCloud-specific model selector inheriting from BaseModelSelector."""

    OSS_MODEL = "openai/gpt-oss-120b"      # Supports tools + reasoning_effort
    COMPOUND_MODEL = "groq/compound"        # Native web search, no tools

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
        instance = cls()
        if has_web_search:
            logger.info(f"[WEB SEARCH] Using {cls.COMPOUND_MODEL} for web search capability")
            return cls.COMPOUND_MODEL, None, False

        # Detect reasoning complexity for OSS model
        reasoning_level = instance._detect_reasoning_complexity(messages, model_name)
        logger.debug(f"[TOOLS] Using {cls.OSS_MODEL} with {reasoning_level} reasoning")
        return cls.OSS_MODEL, reasoning_level, True

    def _detect_reasoning_complexity(self, messages, model_name):
        """Detect reasoning complexity from messages and model selection."""
        # Upgrade for Opus requests
        if "claude-3-opus" in model_name.lower() or "opus" in model_name.lower():
            logger.info(f"[REASONING] Detected Opus request: {model_name} -> HIGH reasoning")
            return "high"

        # Analyze message content
        text_content = self.extract_text_content(messages)
        reasoning_score, _ = self.calculate_scores(text_content)  # Ignore coding_score for Groq

        if reasoning_score >= 1:
            return "high"
        return "high"  # Default to high level

class GroqApiClient(BaseApiClient):
    """Handles GroqCloud API communication with authentication and error handling."""

    def __init__(self):
        super().__init__(
            base_url="https://api.groq.com/openai/v1/chat/completions",
            env_var_name="GROQ_API_KEY",
            provider_name="GroqCloud", 
            default_test_model="openai/gpt-oss-120b"
        )


class GroqAdapter:
    """Adapter exposing the interface required by BaseClaudeProxy for GroqCloud."""

    def __init__(self):
        self.name = "GroqCloud"  # Required by BaseClaudeProxy
        self.api_client = GroqApiClient()
        self.model_selector = GroqModelSelector()
        self.tool_mapper = ClaudeToolMapper()
        self.message_transformer = MessageTransformer()

    def authenticate(self) -> bool:
        """Validate the API key is present."""
        return self.api_client.authenticate()

    def test_connection(self) -> bool:
        """Test connection to GroqCloud API."""
        return self.api_client.test_connection()

    def handle_proxy_request(self, data: dict):
        """Process an incoming request payload and return a Flask response."""

        # Detect web search requirement
        has_web_search = "tools" in data and any(
            tool.get("function", {}).get("name") in ["web_search", "browser_search"]
            for tool in data.get("tools", [])
        )

        # Select model and configuration
        messages = data.get("messages", [])
        selected_model, reasoning_level, supports_tools = self.model_selector.select_model_and_config(
            messages, has_web_search, data.get("model", "claude-3-5-sonnet")
        )

        # Transform messages
        transformed_messages = self.message_transformer.anthropic_to_openai(messages)

        # Build OpenAI request
        openai_request = {"model": selected_model, "messages": transformed_messages}

        # Add reasoning effort for compatible models
        if reasoning_level:
            openai_request["reasoning_effort"] = reasoning_level

        # Add tools for models that support them
        if "tools" in data and supports_tools:
            openai_request["tools"] = self.tool_mapper.generate_ultra_simple_tools()
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
        anthropic_response = self.message_transformer.groq_to_anthropic_tools(groq_response, data.get("model", "claude-3-5-sonnet"))
        if anthropic_response:
            return jsonify(anthropic_response)

        # Convert regular text response
        anthropic_response = self.message_transformer.groq_to_anthropic_text(groq_response, data.get("model", "claude-3-5-sonnet"))
        if anthropic_response:
            return jsonify(anthropic_response)

        return jsonify({"error": "Invalid response from GroqCloud"}), 500
