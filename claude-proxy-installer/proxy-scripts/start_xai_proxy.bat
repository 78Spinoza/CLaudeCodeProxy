@echo off
echo Starting xAI Proxy Server and Claude Code...
echo.

REM Get the folder where this batch script is located (always ends with \)
set SCRIPT_DIR=%~dp0

REM Start proxy server in background, using absolute path
echo [1/2] Starting proxy server...
start "xAI Proxy" python "%SCRIPT_DIR%xai_claude_proxy_enhanced.py"

REM Wait a moment for server to start
timeout /t 3 /nobreak >nul

REM Create temporary command file for Claude Code
echo [2/2] Creating Claude Code command...
echo @echo off > "%TEMP%\claude_xai.bat"
echo claude --settings "{\"env\": {\"ANTHROPIC_BASE_URL\": \"http://localhost:5000\", \"ANTHROPIC_API_KEY\": \"dummy_key\"}}" --permission-mode plan >> "%TEMP%\claude_xai.bat"
echo pause >> "%TEMP%\claude_xai.bat"

REM Start Claude Code in new window
echo [2/2] Opening Claude Code in new window...
start "Claude Code - xAI" cmd /k "%TEMP%\claude_xai.bat"

echo.
echo [OK] Both windows opened:
echo   - Proxy server running
echo   - Claude Code ready in new window
echo.
pause
