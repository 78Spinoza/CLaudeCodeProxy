@echo off
setlocal enabledelayedexpansion

REM ClaudeProxy Entry Point for Windows
REM Checks setup status, selects provider, runs proxy script with CLI

echo(
echo ============================================================================
echo                      CLAUDECODEPROXY ENTRY POINT
echo ============================================================================
echo(

REM Check for setup flag or provider argument
set FORCE_SETUP=0
set PROVIDER=
if "%1"=="setup" set FORCE_SETUP=1
if "%1"=="xai" set PROVIDER=xai
if "%1"=="groq" set PROVIDER=groq

REM Check if Python 3.8+ is available
echo [CHECK] Looking for Python 3.8+
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.8+ not found in PATH!
    echo To install Python 3.8+:
    echo 1. Visit: https://www.python.org/downloads/
    echo 2. Download Python 3.8 or higher like Python 3.12.
    echo 3. Run the installer and check "Add Python to PATH" during installation.
    echo Alternatively, use the Microsoft Store:
    echo 1. Open Microsoft Store and search for Python.
    echo 2. Install Python 3.8 or higher like Python 3.12.
    echo After installation, restart Command Prompt and try again.
    echo(
    pause
    exit /b 1
)

REM Verify Python version using Python one-liner
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python version too old or invalid - need 3.8+
    echo To install Python 3.8+:
    echo 1. Visit: https://www.python.org/downloads/
    echo 2. Download Python 3.8 or higher like Python 3.12.
    echo 3. Run the installer and check "Add Python to PATH" during installation.
    echo Alternatively, use the Microsoft Store:
    echo 1. Open Microsoft Store and search for Python.
    echo 2. Install Python 3.8 or higher like Python 3.12.
    echo After installation, restart Command Prompt and try again.
    echo(
    pause
    exit /b 1
)
echo [OK] Python 3.8+ is ready.

REM Check if Claude CLI is installed
where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Claude Code CLI not found! Run setup to install.
    echo Run: claudeproxy setup
    pause
    exit /b 1
)

REM Refresh environment variables from registry (in case they were set by setup)
echo [INFO] Refreshing environment variables from registry
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v XAI_API_KEY 2^>nul') do set "XAI_API_KEY=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set "GROQ_API_KEY=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v CLAUDEPROXY_CONFIGURED 2^>nul') do set "CLAUDEPROXY_CONFIGURED=%%b"

REM Check setup status
set SETUP_COMPLETE=0
reg query HKCU\Environment /v CLAUDEPROXY_CONFIGURED >nul 2>&1
if %errorlevel% equ 0 (
    REM Check if at least one API key is valid (not NA)
    reg query HKCU\Environment /v XAI_API_KEY >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=3*" %%a in ('reg query HKCU\Environment /v XAI_API_KEY') do (
            if not "%%a"=="NA" set XAI_VALID=1
        )
    )
    reg query HKCU\Environment /v GROQ_API_KEY >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=3*" %%a in ('reg query HKCU\Environment /v GROQ_API_KEY') do (
            if not "%%a"=="NA" set GROQ_VALID=1
        )
    )
    if defined XAI_VALID set SETUP_COMPLETE=1
    if defined GROQ_VALID set SETUP_COMPLETE=1
)

if %FORCE_SETUP%==1 set SETUP_COMPLETE=0

if %SETUP_COMPLETE%==0 (
    echo [SETUP] Running setup process
    echo(
    python claudeproxysetup.py setup
    if %errorlevel% neq 0 (
        echo [ERROR] Setup failed!
        pause
        exit /b 1
    )
    echo [OK] Setup completed. Restart Command Prompt for changes to take effect.
    pause
    exit /b 0
)

echo [RUN] Setup is complete. Checking providers

REM Check valid providers
set XAI_VALID=0
reg query HKCU\Environment /v XAI_API_KEY >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3*" %%a in ('reg query HKCU\Environment /v XAI_API_KEY') do (
        if not "%%a"=="NA" set XAI_VALID=1
    )
)
set GROQ_VALID=0
reg query HKCU\Environment /v GROQ_API_KEY >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3*" %%a in ('reg query HKCU\Environment /v GROQ_API_KEY') do (
        if not "%%a"=="NA" set GROQ_VALID=1
    )
)

if %XAI_VALID%==0 if %GROQ_VALID%==0 (
    echo [ERROR] No valid API keys configured!
    echo Run: claudeproxy setup
    pause
    exit /b 1
)

REM Determine provider
if defined PROVIDER (
    if "%PROVIDER%"=="xai" if %XAI_VALID%==1 (
        echo Auto-launching xAI Grok
        start_xai_proxy.bat
    ) else if "%PROVIDER%"=="groq" if %GROQ_VALID%==1 (
        echo Auto-launching GroqCloud
        start_groq_proxy.bat
    ) else (
        echo [ERROR] Invalid or unconfigured provider specified!
        pause
        exit /b 1
    )
) else (
    if %XAI_VALID%==1 if %GROQ_VALID%==1 (
        echo Both providers configured. Choose one:
        echo 1. xAI Grok (auto-launch)
        echo 2. GroqCloud (auto-launch)
        echo.
        set /p CHOICE=Enter 1 or 2:
        if "!CHOICE!"=="1" (
            echo Auto-launching xAI Grok
            start_xai_proxy.bat
        ) else if "!CHOICE!"=="2" (
            echo Auto-launching GroqCloud
            start_groq_proxy.bat
        ) else (
            echo [ERROR] Invalid choice! Enter 1 or 2
            pause
            exit /b 1
        )
    ) else if %XAI_VALID%==1 (
        echo Auto-launching xAI Grok - only configured provider
        start_xai_proxy.bat
    ) else if %GROQ_VALID%==1 (
        echo Auto-launching GroqCloud - only configured provider
        start_groq_proxy.bat
    )
)

if %errorlevel% neq 0 (
    echo [ERROR] Failed to run proxy and CLI!
    pause
    exit /b 1
)

pause
exit /b 0