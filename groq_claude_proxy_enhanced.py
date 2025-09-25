#!/usr/bin/env python3
"""
GroqCloud Claude Code Proxy - ENHANCED VERSION v1.0.6
=====================================================

Clean class-based architecture for GroqCloud Claude Code integration.
Enables all Claude Code tools through ultra-simple schemas with intelligent model selection.

Features:
✓ All 15+ Claude Code tools working (ultra-simple schemas)
✓ Native GroqCloud web search (groq/compound model)
✓ Smart model selection based on capability requirements
✓ Complete bidirectional API translation
✓ Real tool execution through Claude Code backends
✓ 20x cost savings vs Anthropic direct pricing

Port: 5003 (enhanced proxy with clean architecture)
"""

from proxy_core import BaseClaudeProxy
from groq_adapter import GroqAdapter

if __name__ == "__main__":
    adapter = GroqAdapter()
    proxy = BaseClaudeProxy(adapter=adapter, port=5003, name="GroqCloud")
    proxy.start()
