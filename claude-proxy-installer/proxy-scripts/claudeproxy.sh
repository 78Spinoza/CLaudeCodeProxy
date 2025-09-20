#!/bin/bash
# ClaudeProxy Entry Point for Linux/macOS
# Checks setup status, selects provider, runs proxy script with CLI

set -e  # Exit on any error

echo ""
echo "============================================================================"
echo "                      CLAUDECODEPROXY ENTRY POINT"
echo "============================================================================"
echo ""

# Check for setup flag or provider argument
FORCE_SETUP=0
PROVIDER=""
if [ "$1" = "setup" ]; then
    FORCE_SETUP=1
elif [ "$1" = "xai" ]; then
    PROVIDER="xai"
elif [ "$1" = "groq" ]; then
    PROVIDER="groq"
fi

# Check if Python 3.8+ is available
echo "[CHECK] Looking for Python 3.8+"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >/dev/null 2>&1; then
        echo "[OK] Python 3.8+ is ready."
    else
        echo "[ERROR] Python version too old - need 3.8+"
        echo "To install Python 3.8+:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "  macOS: brew install python3"
        echo "  Or visit: https://www.python.org/downloads/"
        exit 1
    fi
elif command -v python >/dev/null 2>&1; then
    if python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >/dev/null 2>&1; then
        PYTHON_CMD="python"
        echo "[OK] Python 3.8+ is ready."
    else
        echo "[ERROR] Python version too old - need 3.8+"
        echo "To install Python 3.8+:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "  macOS: brew install python3"
        echo "  Or visit: https://www.python.org/downloads/"
        exit 1
    fi
else
    echo "[ERROR] Python 3.8+ not found in PATH!"
    echo "To install Python 3.8+:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo "  Or visit: https://www.python.org/downloads/"
    echo "After installation, restart your terminal and try again."
    exit 1
fi

# Check if Claude CLI is installed
if ! command -v claude >/dev/null 2>&1; then
    echo "[ERROR] Claude Code CLI not found! Run setup to install."
    echo "Run: ./claudeproxy.sh setup"
    exit 1
fi

# Load environment variables from shell profile if they exist
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc" 2>/dev/null || true
fi
if [ -f "$HOME/.zshrc" ] && [ -n "$ZSH_VERSION" ]; then
    source "$HOME/.zshrc" 2>/dev/null || true
fi
if [ -f "$HOME/.profile" ]; then
    source "$HOME/.profile" 2>/dev/null || true
fi

echo "[INFO] Refreshing environment variables from profile"

# Check setup status
SETUP_COMPLETE=0
if [ "$CLAUDEPROXY_CONFIGURED" = "CONFIGURED" ]; then
    # Check if at least one API key is valid (not NA)
    XAI_VALID=0
    GROQ_VALID=0
    if [ "$XAI_API_KEY" != "NA" ] && [ -n "$XAI_API_KEY" ]; then
        XAI_VALID=1
    fi
    if [ "$GROQ_API_KEY" != "NA" ] && [ -n "$GROQ_API_KEY" ]; then
        GROQ_VALID=1
    fi
    if [ $XAI_VALID -eq 1 ] || [ $GROQ_VALID -eq 1 ]; then
        SETUP_COMPLETE=1
    fi
fi

if [ $FORCE_SETUP -eq 1 ]; then
    SETUP_COMPLETE=0
fi

if [ $SETUP_COMPLETE -eq 0 ]; then
    echo "[SETUP] Running setup process"
    echo ""
    $PYTHON_CMD claudeproxysetup.py setup
    if [ $? -ne 0 ]; then
        echo "[ERROR] Setup failed!"
        exit 1
    fi
    echo "[OK] Setup completed. Restart terminal for changes to take effect."
    exit 0
fi

echo "[RUN] Setup is complete. Checking providers"

# Check valid providers
XAI_VALID=0
if [ "$XAI_API_KEY" != "NA" ] && [ -n "$XAI_API_KEY" ]; then
    XAI_VALID=1
fi
GROQ_VALID=0
if [ "$GROQ_API_KEY" != "NA" ] && [ -n "$GROQ_API_KEY" ]; then
    GROQ_VALID=1
fi

if [ $XAI_VALID -eq 0 ] && [ $GROQ_VALID -eq 0 ]; then
    echo "[ERROR] No valid API keys configured!"
    echo "Run: ./claudeproxy.sh setup"
    exit 1
fi

# Function to start xAI proxy
start_xai_proxy() {
    echo "Starting xAI enhanced proxy on port 5000..."
    echo "After proxy starts, use Claude Code with:"
    echo "claude --settings '{\"env\": {\"ANTHROPIC_BASE_URL\": \"http://localhost:5000\", \"ANTHROPIC_API_KEY\": \"dummy_key\"}}' --permission-mode plan"
    echo ""
    echo "Press Ctrl+C to stop the proxy when done."
    echo ""
    $PYTHON_CMD xai_claude_proxy_enhanced.py
}

# Function to start GroqCloud proxy
start_groq_proxy() {
    echo "Starting GroqCloud enhanced proxy on port 5003..."
    echo "After proxy starts, use Claude Code with:"
    echo "claude --settings '{\"env\": {\"ANTHROPIC_BASE_URL\": \"http://localhost:5003\", \"ANTHROPIC_API_KEY\": \"dummy_key\"}}' --permission-mode plan"
    echo ""
    echo "Press Ctrl+C to stop the proxy when done."
    echo ""
    $PYTHON_CMD groq_claude_proxy_enhanced.py
}

# Determine provider and launch
if [ -n "$PROVIDER" ]; then
    if [ "$PROVIDER" = "xai" ] && [ $XAI_VALID -eq 1 ]; then
        echo "Auto-launching xAI Grok"
        start_xai_proxy
    elif [ "$PROVIDER" = "groq" ] && [ $GROQ_VALID -eq 1 ]; then
        echo "Auto-launching GroqCloud"
        start_groq_proxy
    else
        echo "[ERROR] Invalid or unconfigured provider specified!"
        exit 1
    fi
else
    if [ $XAI_VALID -eq 1 ] && [ $GROQ_VALID -eq 1 ]; then
        echo "Both providers configured. Choose one:"
        echo "1. xAI Grok (auto-launch)"
        echo "2. GroqCloud (auto-launch)"
        echo ""
        read -p "Enter 1 or 2: " CHOICE
        if [ "$CHOICE" = "1" ]; then
            echo "Auto-launching xAI Grok"
            start_xai_proxy
        elif [ "$CHOICE" = "2" ]; then
            echo "Auto-launching GroqCloud"
            start_groq_proxy
        else
            echo "[ERROR] Invalid choice! Enter 1 or 2"
            exit 1
        fi
    elif [ $XAI_VALID -eq 1 ]; then
        echo "Auto-launching xAI Grok - only configured provider"
        start_xai_proxy
    elif [ $GROQ_VALID -eq 1 ]; then
        echo "Auto-launching GroqCloud - only configured provider"
        start_groq_proxy
    fi
fi

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to run proxy and CLI!"
    exit 1
fi

exit 0