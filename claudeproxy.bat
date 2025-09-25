@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM   CLAUDECODEPROXY ENTRY POINT (Windows)
REM   - Works from ANY folder
REM   - Always runs Python + start scripts from this batch file's location
REM ============================================================================

REM Capture user's original working directory
set "CLAUDEPROXY_ORIGINAL_DIR=%CD%"

REM Move to script's directory
pushd "%~dp0"

echo(
echo ============================================================================
echo                      CLAUDECODEPROXY ENTRY POINT
echo ============================================================================
echo(

REM Check for setup flag or provider argument
set FORCE_SETUP=0
set PROVIDER=
if "%~1"=="setup" set FORCE_SETUP=1
if "%~1"=="xai" set PROVIDER=xai
if "%~1"=="groq" set PROVIDER=groq
if "%~1"=="baseten" set PROVIDER=baseten

REM --- Python check ---
echo [CHECK] Looking for Python 3.8 or higher
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.8+ not found in PATH!
    echo Install Python 3.8+ from https://www.python.org/downloads/ and retry.
    pause
    popd
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python version too old - need 3.8+
    pause
    popd
    exit /b 1
)
echo [OK] Python 3.8+ is ready.

REM --- Claude CLI check ---
where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Claude Code CLI not found! Run setup to install.
    echo Run: claudeproxy setup
    pause
    popd
    exit /b 1
)

REM Refresh env vars from registry
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v XAI_API_KEY 2^>nul') do set "XAI_API_KEY=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set "GROQ_API_KEY=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v BASETEN_API_KEY 2^>nul') do set "BASETEN_API_KEY=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v CLAUDEPROXY_CONFIGURED 2^>nul') do set "CLAUDEPROXY_CONFIGURED=%%b"

REM Setup check
set SETUP_COMPLETE=0
reg query HKCU\Environment /v CLAUDEPROXY_CONFIGURED >nul 2>&1
if %errorlevel% equ 0 (
    if defined XAI_API_KEY if not "%XAI_API_KEY%"=="NA" set XAI_VALID=1
    if defined GROQ_API_KEY if not "%GROQ_API_KEY%"=="NA" set GROQ_VALID=1
    if defined XAI_VALID set SETUP_COMPLETE=1
    if defined GROQ_VALID set SETUP_COMPLETE=1
)
if %FORCE_SETUP%==1 set SETUP_COMPLETE=0

if %SETUP_COMPLETE%==0 (
    echo [SETUP] Running setup process...
    python "%~dp0claudeproxysetup.py" setup
    if %errorlevel% neq 0 (
        echo [ERROR] Setup failed!
        pause
        popd
        exit /b 1
    )
    echo [OK] Setup completed. Restart Command Prompt for changes to take effect.
    pause
    popd
    exit /b 0
)

REM --- Provider selection ---
set XAI_VALID=0
set GROQ_VALID=0
set BASETEN_VALID=0
if defined XAI_API_KEY if not "%XAI_API_KEY%"=="NA" set XAI_VALID=1
if defined GROQ_API_KEY if not "%GROQ_API_KEY%"=="NA" set GROQ_VALID=1
if defined BASETEN_API_KEY if not "%BASETEN_API_KEY%"=="NA" set BASETEN_VALID=1

if %XAI_VALID%==0 if %GROQ_VALID%==0 if %BASETEN_VALID%==0 (
    echo [ERROR] No valid API keys configured!
    echo Run: claudeproxy setup
    pause
    popd
    exit /b 1
)

if defined PROVIDER (
    if "%PROVIDER%"=="xai" if %XAI_VALID%==1 (
        echo Auto-launching xAI Grok
        call "%~dp0start_xai_proxy.bat"
    ) else if "%PROVIDER%"=="groq" if %GROQ_VALID%==1 (
        echo Auto-launching GroqCloud
        call "%~dp0start_groq_proxy.bat"
    ) else (
        echo [ERROR] Invalid or unconfigured provider specified!
        pause
        popd
        exit /b 1
    )
) else (
    if %XAI_VALID%==1 if %GROQ_VALID%==1 (
        echo Both providers configured. Choose one:
        echo 1. xAI Grok
        echo 2. GroqCloud
        set /p CHOICE=Enter 1 or 2:
        if "!CHOICE!"=="1" (
            call "%~dp0start_xai_proxy.bat"
        ) else if "!CHOICE!"=="2" (
            call "%~dp0start_groq_proxy.bat"
        ) else (
            echo [ERROR] Invalid choice! Enter 1 or 2
            pause
            popd
            exit /b 1
        )
    ) else if %XAI_VALID%==1 (
        call "%~dp0start_xai_proxy.bat"
    ) else if %GROQ_VALID%==1 (
        call "%~dp0start_groq_proxy.bat"
    )
)

popd
pause
exit /b 0