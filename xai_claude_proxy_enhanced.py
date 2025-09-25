#!/usr/bin/env python3
"""
xAI Claude Code Proxy - ENHANCED VERSION v1.0.17
===============================================

Clean class-based architecture for xAI Claude Code integration.
Enhanced with robust retry logic and intelligent model selection.

Features:
All 15+ Claude Code tools working (ultra-simple schemas)
Smart model selection (grok-4-0709 vs grok-code-fast-1)
Robust retry logic with exponential backoff for connection stability
Complete bidirectional API translation
Real tool execution through Claude Code backends
15-20x cost savings vs Anthropic direct pricing

Port: 5000 (xAI proxy with enhanced reliability)
"""

from proxy_core import BaseClaudeProxy
from xai_adapter import XAIAdapter

if __name__ == "__main__":
    adapter = XAIAdapter()
    proxy = BaseClaudeProxy(adapter=adapter, port=5000, name="xAI")
    proxy.start()
