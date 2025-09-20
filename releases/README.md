# Claude Proxy Installer Releases

This folder contains the compiled installer binaries for different architectures.

## Available Downloads

### Windows Installers
- **x64 (64-bit)**: `Claude-Proxy-Installer_1.0.0_x64-setup.exe`
- **x86 (32-bit)**: `Claude-Proxy-Installer_1.0.0_x86-setup.exe`

## Installation Instructions

1. Download the appropriate installer for your system architecture
2. Run the installer as administrator if prompted
3. The installer will:
   - Detect existing dependencies (Python, Node.js, Git, Claude Code)
   - Download and install missing dependencies automatically
   - Install proxy scripts to `~/claude-proxy/`
   - Add claude-proxy to your system PATH
   - Configure API keys for xAI and/or GroqCloud

## System Requirements

- **Windows**: Windows 10 or later
- **RAM**: 4GB minimum
- **Storage**: 500MB free space (plus space for dependencies)
- **Internet**: Required for downloading dependencies and API usage

## After Installation

1. Open Command Prompt
2. Navigate to your project folder: `cd C:\YourProject`
3. Run: `claudeproxy`
4. Follow the interactive setup to choose your AI provider
5. Use Claude Code with 15-20x cost savings!

## Support

- Issues: [GitHub Issues](https://github.com/YourUsername/ClaudeProxy/issues)
- Documentation: See main README.md
- API Keys:
  - xAI: https://console.x.ai
  - GroqCloud: https://console.groq.com

---
*Installers are code-signed and virus-scanned before release*