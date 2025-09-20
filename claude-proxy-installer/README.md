# Claude Proxy Smart Installer

**One-click installer for Claude Code Proxy with automatic dependency management**

## 🚀 Features

- **Smart Detection**: Automatically detects existing Python, Node.js, Git installations
- **Download-on-Demand**: Only downloads missing dependencies (~15MB installer vs ~400MB bundle)
- **Cross-Platform**: Windows, macOS, Linux support
- **Professional UI**: Progress bars, step-by-step installation tracking
- **API Configuration**: Built-in GUI for xAI and GroqCloud API key setup
- **Desktop Integration**: Creates shortcuts for easy proxy launching
- **Auto-Updates**: Built-in updater for future releases

## 📦 What It Installs

| Dependency | Auto-Detection | Download Source | Size |
|------------|----------------|-----------------|------|
| **Python 3.8+** | ✅ Version check | Python Build Standalone | ~50MB |
| **Node.js 16+** | ✅ Version check | Node.js Official | ~40MB |
| **Git** | ✅ Version check | Git for Windows / Package Manager | ~300MB |
| **Claude CLI** | ✅ Command check | npm registry | ~5MB |
| **Proxy Scripts** | ✅ Always installs | Bundled | ~1MB |

**Total Download**: Only what's missing (typically 15-100MB vs full 400MB bundle)

## 🛠️ Development

### Prerequisites
- Rust (for Tauri backend)
- Node.js (for frontend)

### Build & Run

```bash
# Install dependencies
npm install

# Development mode
npm run tauri dev

# Build installer
npm run tauri build
```

### Project Structure
```
claude-proxy-installer/
├── src/                    # Vue.js frontend
│   ├── App.vue            # Main installer UI
│   └── main.js            # App entry point
├── src-tauri/             # Rust backend
│   ├── src/
│   │   ├── main.rs        # Tauri commands
│   │   ├── dependency_detector.rs  # System dependency detection
│   │   ├── downloader.rs  # Smart download system
│   │   └── installer.rs   # Installation logic
│   └── Cargo.toml         # Rust dependencies
├── proxy-scripts/         # Bundled proxy scripts
└── package.json           # Node.js config
```

## 🎯 Installation Process

1. **Launch Installer**: Run single executable
2. **System Scan**: Detect existing dependencies
3. **Smart Downloads**: Download only missing components
4. **Claude CLI**: Install via npm with fallback methods
5. **Proxy Setup**: Copy and configure proxy scripts
6. **Shortcuts**: Create desktop shortcuts for each proxy
7. **Configuration**: Optional API key setup via GUI
8. **Launch**: Start using proxies immediately

## 🔧 Technical Details

### Dependency Detection
- **Python**: Checks `python3 --version` and `python --version`, validates >= 3.8
- **Node.js**: Checks `node --version`, validates >= 16.0
- **Git**: Checks `git --version`, any version accepted
- **Claude CLI**: Checks `claude --version` for existing installation

### Download Strategy
- **Windows**: Uses official portable/standalone distributions
- **macOS**: Prefers Homebrew, falls back to manual downloads
- **Linux**: Uses system package managers (apt, yum) with manual fallbacks

### Smart Path Management
- **Windows**: Uses `setx` to modify user PATH permanently
- **Unix**: Appends to shell profile (.bashrc/.zshrc) for persistence

## 🚦 Usage After Installation

```bash
# Launch xAI proxy (desktop shortcut or manual)
cd ~/claude-proxy && python xai_claude_proxy_enhanced.py

# Launch GroqCloud proxy
cd ~/claude-proxy && python groq_claude_proxy_enhanced.py

# Use with Claude Code
claude --settings '{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5000"}}' -p "Your prompt"
```

## 📋 Requirements

### System Requirements
- **Windows**: Windows 10+ (64-bit)
- **macOS**: macOS 10.14+
- **Linux**: Ubuntu 18.04+, CentOS 7+, or equivalent

### Permissions
- **Windows**: Admin rights for PATH modification (auto-requested)
- **Unix**: `sudo` access for system package installation (fallback to user-local)

## 🐛 Troubleshooting

### Common Issues

**"Claude CLI installation failed"**
- Ensure Node.js is installed and in PATH
- Try running installer as administrator (Windows)
- Check internet connection for npm registry access

**"Permission denied"**
- Run installer with elevated privileges
- On Unix: ensure user has sudo access or use user-local installation

**"Proxy scripts not found"**
- Verify installer bundle includes `proxy-scripts/` directory
- Check antivirus isn't blocking file extraction

**"API keys not saving"**
- Check environment variable permissions
- Verify user profile write access

## 🎉 Benefits vs Manual Installation

| Aspect | Manual Setup | Smart Installer |
|--------|-------------|-----------------|
| **Steps** | 15+ manual steps | 1 click |
| **Time** | 30-60 minutes | 5-10 minutes |
| **Errors** | High (PATH, versions, etc.) | Very low |
| **Updates** | Manual re-setup | Auto-updater |
| **Dependencies** | Manual detection | Auto-detection |
| **User Experience** | Technical | Consumer-friendly |

The smart installer reduces Claude Code Proxy setup from a complex multi-step process to a single executable that handles everything automatically.