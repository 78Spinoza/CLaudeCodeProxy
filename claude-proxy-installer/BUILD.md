# Building the Claude Proxy Smart Installer

## 🎯 Quick Build

```bash
# Navigate to installer directory
cd claude-proxy-installer

# Install Node.js dependencies
npm install

# Build the installer
npm run tauri:build
```

**Result**: Creates platform-specific installer in `src-tauri/target/release/bundle/`

## 📋 Prerequisites

### Required Tools
1. **Rust** - Install from https://rustup.rs/
2. **Node.js 16+** - Install from https://nodejs.org/
3. **Tauri CLI** - Install with `cargo install tauri-cli`

### Windows Additional Requirements
- **Visual Studio Build Tools** or **Visual Studio Community**
- **Windows SDK** (usually included with Visual Studio)

### Linux Additional Requirements
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev build-essential curl wget libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

### macOS Additional Requirements
```bash
xcode-select --install
```

## 🛠️ Development Workflow

### 1. Development Mode (with hot reload)
```bash
npm run tauri:dev
```
- Opens installer window with hot reload
- Changes to Vue.js frontend auto-refresh
- Rust backend requires restart for changes

### 2. Debug Build (faster, includes debug symbols)
```bash
npm run tauri:build-debug
```

### 3. Production Build (optimized, smaller size)
```bash
npm run tauri:build
```

## 📂 Output Files

### Windows
```
src-tauri/target/release/bundle/
├── msi/
│   └── Claude Proxy Installer_1.0.0_x64_en-US.msi  # MSI installer
└── nsis/
    └── Claude Proxy Installer_1.0.0_x64-setup.exe  # NSIS installer
```

### macOS
```
src-tauri/target/release/bundle/
├── dmg/
│   └── Claude Proxy Installer_1.0.0_x64.dmg       # DMG installer
└── macos/
    └── Claude Proxy Installer.app                  # App bundle
```

### Linux
```
src-tauri/target/release/bundle/
├── appimage/
│   └── claude-proxy-installer_1.0.0_amd64.AppImage  # Portable
├── deb/
│   └── claude-proxy-installer_1.0.0_amd64.deb       # Debian
└── rpm/
    └── claude-proxy-installer-1.0.0-1.x86_64.rpm    # Red Hat
```

## 🔍 Troubleshooting

### "Cargo not found"
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

### "Tauri CLI not found"
```bash
cargo install tauri-cli
```

### Windows: "MSVC not found"
- Install Visual Studio Community with C++ build tools
- Or install Visual Studio Build Tools standalone

### Linux: "webkit2gtk not found"
```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.0-dev

# CentOS/RHEL
sudo yum install webkit2gtk3-devel
```

### Build fails with "permission denied"
- Run terminal as administrator (Windows)
- Use `sudo` for package installations (Linux/macOS)
- Check antivirus isn't blocking Rust/Cargo

## 🎨 Customization

### Change App Icon
1. Replace files in `src-tauri/icons/`
2. Supported formats: ICO (Windows), ICNS (macOS), PNG (Linux)
3. Recommended sizes: 32x32, 128x128, 256x256, 512x512

### Modify App Metadata
Edit `src-tauri/tauri.conf.json`:
```json
{
  "package": {
    "productName": "Your App Name",
    "version": "1.0.0"
  },
  "tauri": {
    "bundle": {
      "identifier": "com.yourcompany.yourapp",
      "category": "DeveloperTool"
    }
  }
}
```

### Bundle Additional Files
Add to `src-tauri/tauri.conf.json`:
```json
{
  "tauri": {
    "bundle": {
      "resources": ["../extra-files/*"]
    }
  }
}
```

## 🚀 Release Workflow

### 1. Version Update
```bash
# Update package.json
npm version patch  # or minor, major

# Update Cargo.toml
# Update tauri.conf.json version
```

### 2. Build All Platforms
```bash
# Windows (run on Windows)
npm run tauri:build

# macOS (run on macOS)
npm run tauri:build

# Linux (run on Linux)
npm run tauri:build
```

### 3. GitHub Release
```bash
# Create release with all platform binaries
gh release create v1.0.0 \
  src-tauri/target/release/bundle/msi/*.msi \
  src-tauri/target/release/bundle/nsis/*.exe \
  src-tauri/target/release/bundle/dmg/*.dmg \
  src-tauri/target/release/bundle/appimage/*.AppImage \
  src-tauri/target/release/bundle/deb/*.deb \
  src-tauri/target/release/bundle/rpm/*.rpm
```

## 📊 Size Optimization

### Frontend Optimization
```bash
# Build with size optimization
npm run build

# Analyze bundle size
npm install -D rollup-plugin-analyzer
```

### Rust Optimization
Add to `src-tauri/Cargo.toml`:
```toml
[profile.release]
panic = "abort"
codegen-units = 1
lto = true
opt-level = "s"  # Optimize for size
strip = true     # Remove debug symbols
```

### Expected Sizes
- **Windows EXE**: ~15-25MB
- **macOS DMG**: ~20-30MB
- **Linux AppImage**: ~20-30MB

This creates a professional, single-file installer that users can download and run immediately, with no manual dependency management required!