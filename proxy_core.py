# proxy_core.py
"""
Core infrastructure shared by both xAI and Groq Claude Code proxies.
Provides a generic Flask server, console command handling, and port conflict checking.
Specific provider logic is delegated to an adapter that implements a small interface.
"""

import logging
import threading
import socket
import time
import sys
import os
from flask import Flask, request, jsonify, Response, stream_with_context

# Suppress Flask development server warning (same as original scripts)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


class BaseClaudeProxy:
    """Base proxy that handles the Flask app and generic plumbing.

    An *adapter* instance must implement the following methods:
        - ``authenticate() -> bool``
        - ``handle_proxy_request(data: dict) -> Flask response``
        - ``name`` (string) – used for logging / messages
    """

    def __init__(self, adapter, port: int, name: str):
        self.adapter = adapter
        self.port = port
        self.name = name
        self.app = Flask(__name__)
        self.running = True
        self._setup_routes()

    # ---------------------------------------------------------------------
    # Generic helpers
    # ---------------------------------------------------------------------
    def _check_port_conflict(self):
        """Ensure no other proxy of the same type is already listening on the port.
        If a conflict is detected the process exits after a short countdown.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", self.port))
            sock.close()
            if result == 0:
                logger.warning(f"[WARNING] Another {self.name} proxy is already running on port {self.port}!")
                logger.warning(f"[WARNING] Only one {self.name} proxy can run at a time.")
                logger.warning("[WARNING] Shutting down in 3 seconds...")
                for i in range(3, 0, -1):
                    logger.warning(f"[WARNING] Shutting down in {i}...")
                    time.sleep(1)
                logger.error(f"[ERROR] Exiting - port {self.port} is already in use by another {self.name} proxy")
                sys.exit(1)
        except Exception as e:
            logger.debug(f"Port check exception (ignored): {e}")

    # ---------------------------------------------------------------------
    # Flask route setup
    # ---------------------------------------------------------------------
    def _setup_routes(self):
        @self.app.route('/v1/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def proxy_route(path):
            # Delegates the heavy lifting to the adapter after generic checks.
            if not self.adapter.authenticate():
                return jsonify({"error": f"{self.name.upper()}_API_KEY not configured"}), 400

            if path != "messages":
                return jsonify({"error": "Endpoint not implemented"}), 501

            data = request.get_json()
            return self.adapter.handle_proxy_request(data)

    # ---------------------------------------------------------------------
    # Console command handling (R=restart, Q=quit, H=help)
    # ---------------------------------------------------------------------
    def _console_input_handler(self):
        try:
            while self.running:
                try:
                    user_input = input().strip().upper()
                    if user_input == 'R':
                        logger.info("[RESTART] Restart command received – reloading code")
                        os.execv(sys.executable, ['python'] + sys.argv)
                    elif user_input in ('Q', 'QUIT'):
                        logger.info("[SHUTDOWN] Quit command received – stopping proxy")
                        self.running = False
                        os._exit(0)
                    elif user_input in ('H', 'HELP'):
                        logger.info("[HELP] Available commands: R – restart, Q – quit, H – help")
                    # ignore any other keys
                except (EOFError, KeyboardInterrupt):
                    break
        except Exception as e:
            logger.debug(f"Console handler error: {e}")

    # ---------------------------------------------------------------------
    # Server start
    # ---------------------------------------------------------------------
    def start(self):
        self._check_port_conflict()
        
        # Print banner similar to original scripts with detailed info
        print("=" * 80)
        print(f"        {self.name} Claude Code Proxy - ENHANCED VERSION v1.0.3")
        print("=" * 80)
        print(f"[SUCCESS] Clean class-based architecture with intelligent model selection!")
        
        if self.name == "xAI":
            print("Models: grok-4-0709 (reasoning) + grok-code-fast-1 (coding)")
        else:
            print("Models: Intelligent routing based on request type")
            
        print("All Claude Code tools working with enhanced reliability!")
        print()

        if self.adapter.authenticate():
            print(f"[OK] {self.name.upper()}_API_KEY found")
            print(f"[TESTING] Connecting to {self.name} API...")

            # Test connection if adapter supports it
            if hasattr(self.adapter, 'test_connection'):
                if self.adapter.test_connection():
                    print(f"[SUCCESS] Connected to {self.name} API")
                    print(f"[PROXY] Claude Code -> {self.name} connection ready")
                else:
                    print(f"[WARNING] Could not verify {self.name} connection - continuing anyway")
            else:
                print(f"[INFO] Connection test not available for {self.name}")

            print()
            print(f"Starting enhanced proxy server on http://localhost:{self.port}...")
            print()
            print("[TOOLS] All 15+ Claude Code tools supported")
            print("[MODELS] Intelligent routing based on task complexity")
            print("[COST] 15-20x cheaper than Anthropic with full functionality")
            print("[RETRY] Robust retry logic with exponential backoff")
            print()
            print("[COMMANDS] Console commands:")
            print("  R - Restart proxy (reload code changes)")
            print("  Q - Quit proxy")
            print("  H - Show help")
            print("  Ctrl+C - Force quit")
            print()
            print("Test with:")
            print(f'claude --settings "{{\\"env\\": {{\\"ANTHROPIC_BASE_URL\\": \\"http://localhost:{self.port}\\", \\"ANTHROPIC_API_KEY\\": \\"dummy_key\\"}}}}" -p "What is 2+2?"')
            print()
            print("Press Ctrl+C to stop")
            print("=" * 80)

            # Start console thread
            console_thread = threading.Thread(target=self._console_input_handler, daemon=True)
            console_thread.start()
            
            # Run Flask server (debug disabled as per original scripts)
            self.app.run(host='127.0.0.1', port=self.port, debug=False)
        else:
            print(f"[ERROR] {self.name.upper()}_API_KEY not found")
            print(f"Please set your {self.name} API key:")
            if self.name == "xAI":
                print("1. Get key from: https://console.x.ai/")
                print("2. Set it: set XAI_API_KEY=your_key_here")
            else:
                print("1. Get key from your provider")
                print("2. Set the appropriate environment variable")
