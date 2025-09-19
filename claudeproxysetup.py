#!/usr/bin/env python3
"""
ClaudeCodeProxy Universal Installer (Simplified - No JSON Config)
Works on Windows, Linux, and macOS. Sets environment variables and PATH permanently.
Automatically elevates for Windows registry changes or Unix sudo.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import ctypes

def clean_registry_value(raw_value):
    """Cross-platform registry value cleaner - handles Windows registry quotes."""
    if not raw_value:
        return raw_value

    # Convert to string and strip whitespace
    value = str(raw_value).strip()

    # Only do aggressive quote cleaning on Windows (where registry causes issues)
    if os.name == 'nt':  # Windows
        # Remove all the crazy quote combinations Windows registry creates
        quote_patterns = [
            '"\\"', '\\"',  # Escaped quotes
            '"\'', '\'"',   # Mixed quotes
            '""', "''",     # Double quotes
            '"', "'",       # Single quotes
        ]

        # Keep removing quotes until none are left at the edges
        changed = True
        while changed:
            changed = False
            original = value

            # Remove quotes from start and end
            for pattern in quote_patterns:
                if value.startswith(pattern):
                    value = value[len(pattern):]
                    changed = True
                if value.endswith(pattern):
                    value = value[:-len(pattern)]
                    changed = True

            # Simple quote removal
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
                changed = True
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
                changed = True

            # If we made changes, continue cleaning
            if value != original:
                changed = True

        # Remove escape characters
        value = value.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')

        # Final cleanup - remove any remaining trailing escapes
        value = value.rstrip('\\').rstrip('"').rstrip("'")
    else:  # Linux/macOS - just basic cleaning
        # Simple quote removal for Unix environment variables
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

    return value.strip()

class ClaudeProxyInstaller:
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        # ✅ FIX: Use the directory of the script itself, not the working directory
        self.current_dir = Path(__file__).resolve().parent

    def is_admin(self):
        """Check if running with admin privileges"""
        if self.system == "Windows":
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        else:
            return os.geteuid() == 0

    def elevate(self):
        """Relaunch script with admin privileges if needed"""
        if self.system == "Windows" and not self.is_admin():
            print("[ELEVATION] Admin privileges required for setting PATH/env vars. Requesting elevation...")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}" {" ".join(sys.argv[1:])}', None, 1)
            sys.exit(0)

    def check_command(self, cmd):
        """Check if a command exists"""
        return shutil.which(cmd) is not None

    def run_command(self, cmd, shell=False, env=None):
        """Run a command and return success status"""
        try:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, env=env)
            return result.returncode == 0, result.stdout, result.stderr
        except:
            return False, "", ""

    def check_python(self):
        """Check Python version"""
        print("\n[1/7] Checking Python...")
        version_info = sys.version_info
        if version_info.major >= 3 and version_info.minor >= 8:
            print(f"[OK] Python {version_info.major}.{version_info.minor}.{version_info.micro} found")
            return True
        else:
            print(f"[ERROR] Python 3.8+ required (found {version_info.major}.{version_info.minor})")
            return False

    def install_python_packages(self):
        """Install required Python packages"""
        print("\n[2/7] Installing Python packages...")
        packages = ["flask", "requests", "anthropic"]

        # Check if packages are already installed
        missing = []
        for pkg in packages:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)

        if not missing:
            print("[OK] All Python packages already installed")
            return True

        print(f"Installing: {', '.join(missing)}")
        pip_cmd = [sys.executable, "-m", "pip", "install"] + missing
        success, out, err = self.run_command(pip_cmd)

        if success:
            print("[OK] Python packages installed successfully")
            return True

        # Try with sudo on Unix
        if self.system != "Windows" and self.check_command("sudo"):
            print("[INFO] Trying with sudo...")
            pip_cmd = ["sudo"] + pip_cmd
            success, out, err = self.run_command(pip_cmd)
            if success:
                print("[OK] Python packages installed with sudo")
                return True

        print("[ERROR] Failed to install packages")
        print("  Try running: pip install flask requests anthropic")
        if self.system == "Windows":
            print("  Or run as Administrator.")
        else:
            print("  Or use: sudo pip install flask requests anthropic")
        return False

    def install_nodejs(self):
        """Install Node.js automatically if possible"""
        print("\n[AUTO-INSTALL] Attempting to install Node.js...")

        if self.system == "Windows":
            # Try winget first (Windows 10+ with App Installer)
            if self.check_command("winget"):
                print("Using winget to install Node.js...")
                success, _, _ = self.run_command(["winget", "install", "OpenJS.NodeJS", "--accept-package-agreements", "--accept-source-agreements"])
                if success and self.check_command("node"):
                    print("[OK] Node.js installed via winget")
                    return True

            # Try chocolatey
            if self.check_command("choco"):
                print("Using Chocolatey to install Node.js...")
                success, _, _ = self.run_command(["choco", "install", "nodejs", "-y"])
                if success and self.check_command("node"):
                    print("[OK] Node.js installed via Chocolatey")
                    return True

        elif self.system == "Darwin":
            # Try Homebrew
            if self.check_command("brew"):
                print("Using Homebrew to install Node.js...")
                success, _, _ = self.run_command(["brew", "install", "node"])
                if success and self.check_command("node"):
                    print("[OK] Node.js installed via Homebrew")
                    return True

        else:  # Linux
            # Try apt (Debian/Ubuntu)
            if self.check_command("apt"):
                print("Using apt to install Node.js...")
                success, _, _ = self.run_command(["sudo", "apt", "update"])
                if success:
                    success, _, _ = self.run_command(["sudo", "apt", "install", "-y", "nodejs", "npm"])
                    if success and self.check_command("node"):
                        print("[OK] Node.js installed via apt")
                        return True

            # Try yum (Red Hat/CentOS)
            if self.check_command("yum"):
                print("Using yum to install Node.js...")
                success, _, _ = self.run_command(["sudo", "yum", "install", "-y", "nodejs", "npm"])
                if success and self.check_command("node"):
                    print("[OK] Node.js installed via yum")
                    return True

        print("[ERROR] Automatic installation failed")
        return False

    def check_nodejs(self):
        """Check Node.js and npm, attempt installation if missing"""
        print("\n[3/7] Checking Node.js and npm...")

        has_node = self.check_command("node")
        has_npm = self.check_command("npm")

        if has_node and has_npm:
            success, version, _ = self.run_command(["node", "--version"])
            if success:
                print(f"[OK] Node.js {version.strip()} found")
            print("[OK] npm found")
            return True
        else:
            print("[ERROR] Node.js/npm not found")

            # Attempt automatic installation
            install_attempt = input("Would you like to try automatic installation? (y/n): ")
            if install_attempt.lower() == 'y':
                if self.install_nodejs():
                    return True

            # Manual installation instructions
            print("\nManual installation options:")
            print("  Download from: https://nodejs.org/")
            if self.system == "Windows":
                print("  Or use: winget install OpenJS.NodeJS")
                print("  Or use: choco install nodejs (if Chocolatey installed)")
            elif self.system == "Darwin":
                print("  Or use: brew install node")
            else:
                print("  Or use: sudo apt install nodejs npm (Ubuntu/Debian)")
                print("  Or use: sudo yum install nodejs npm (Red Hat/CentOS)")
            return False

    def install_git(self):
        """Install Git automatically if possible"""
        print("\n[AUTO-INSTALL] Attempting to install Git...")

        if self.system == "Windows":
            # Try winget first
            if self.check_command("winget"):
                print("Using winget to install Git...")
                success, _, _ = self.run_command(["winget", "install", "Git.Git", "--accept-package-agreements", "--accept-source-agreements"])
                if success and self.check_command("git"):
                    print("[OK] Git installed via winget")
                    return True

            # Try chocolatey
            if self.check_command("choco"):
                print("Using Chocolatey to install Git...")
                success, _, _ = self.run_command(["choco", "install", "git", "-y"])
                if success and self.check_command("git"):
                    print("[OK] Git installed via Chocolatey")
                    return True

        elif self.system == "Darwin":
            # Try Homebrew
            if self.check_command("brew"):
                print("Using Homebrew to install Git...")
                success, _, _ = self.run_command(["brew", "install", "git"])
                if success and self.check_command("git"):
                    print("[OK] Git installed via Homebrew")
                    return True

        else:  # Linux
            # Try apt (Debian/Ubuntu)
            if self.check_command("apt"):
                print("Using apt to install Git...")
                success, _, _ = self.run_command(["sudo", "apt", "install", "-y", "git"])
                if success and self.check_command("git"):
                    print("[OK] Git installed via apt")
                    return True

            # Try yum (Red Hat/CentOS)
            if self.check_command("yum"):
                print("Using yum to install Git...")
                success, _, _ = self.run_command(["sudo", "yum", "install", "-y", "git"])
                if success and self.check_command("git"):
                    print("[OK] Git installed via yum")
                    return True

        print("[ERROR] Automatic Git installation failed")
        return False

    def check_git(self):
        """Check Git installation (needed for Claude Code)"""
        print("\n[4/7] Checking Git...")

        if self.check_command("git"):
            success, version, _ = self.run_command(["git", "--version"])
            if success:
                print(f"[OK] {version.strip()} found")
            return True
        else:
            print("[WARNING] Git not found (required for Claude Code)")

            # Attempt automatic installation
            install_attempt = input("Would you like to try automatic installation? (y/n): ")
            if install_attempt.lower() == 'y':
                if self.install_git():
                    return True

            print("\nManual installation options:")
            print("  Download from: https://git-scm.com/")
            if self.system == "Windows":
                print("  Or use: winget install Git.Git")
                print("  Or use: choco install git (if Chocolatey installed)")
            elif self.system == "Darwin":
                print("  Or use: brew install git")
            else:
                print("  Or use: sudo apt install git (Ubuntu/Debian)")
                print("  Or use: sudo yum install git (Red Hat/CentOS)")
            return False

    def install_github_cli(self):
        """Install GitHub CLI automatically if possible"""
        print("\n[AUTO-INSTALL] Attempting to install GitHub CLI...")

        if self.system == "Windows":
            # Try winget first
            if self.check_command("winget"):
                print("Using winget to install GitHub CLI...")
                success, _, _ = self.run_command(["winget", "install", "GitHub.cli", "--accept-package-agreements", "--accept-source-agreements"])
                if success and self.check_command("gh"):
                    print("[OK] GitHub CLI installed via winget")
                    return True

            # Try chocolatey
            if self.check_command("choco"):
                print("Using Chocolatey to install GitHub CLI...")
                success, _, _ = self.run_command(["choco", "install", "gh", "-y"])
                if success and self.check_command("gh"):
                    print("[OK] GitHub CLI installed via Chocolatey")
                    return True

        elif self.system == "Darwin":
            # Try Homebrew
            if self.check_command("brew"):
                print("Using Homebrew to install GitHub CLI...")
                success, _, _ = self.run_command(["brew", "install", "gh"])
                if success and self.check_command("gh"):
                    print("[OK] GitHub CLI installed via Homebrew")
                    return True

        else:  # Linux
            # Try apt (Debian/Ubuntu)
            if self.check_command("apt"):
                print("Using apt to install GitHub CLI...")
                # Add GitHub CLI repository
                success, _, _ = self.run_command(["sudo", "apt", "update"])
                if success:
                    success, _, _ = self.run_command(["sudo", "apt", "install", "-y", "curl"])
                    if success:
                        success, _, _ = self.run_command(["curl", "-fsSL", "https://cli.github.com/packages/githubcli-archive-keyring.gpg", "|", "sudo", "dd", "of=/usr/share/keyrings/githubcli-archive-keyring.gpg"])
                        if success:
                            success, _, _ = self.run_command(["echo", '"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main"', "|", "sudo", "tee", "/etc/apt/sources.list.d/github-cli.list"], shell=True)
                            if success:
                                success, _, _ = self.run_command(["sudo", "apt", "update"])
                                if success:
                                    success, _, _ = self.run_command(["sudo", "apt", "install", "-y", "gh"])
                                    if success and self.check_command("gh"):
                                        print("[OK] GitHub CLI installed via apt")
                                        return True

        print("[ERROR] Automatic GitHub CLI installation failed")
        return False

    def check_github_cli(self):
        """Check GitHub CLI installation (helpful for Claude Code workflows)"""
        print("\n[5/7] Checking GitHub CLI...")

        if self.check_command("gh"):
            success, version, _ = self.run_command(["gh", "--version"])
            if success:
                print(f"[OK] GitHub CLI {version.split()[2]} found")
            return True
        else:
            print("[INFO] GitHub CLI not found (recommended for Claude Code)")
            print("  GitHub CLI helps with repository operations, PR creation, etc.")

            # Attempt automatic installation
            install_attempt = input("Would you like to install GitHub CLI? (y/n): ")
            if install_attempt.lower() == 'y':
                if self.install_github_cli():
                    return True

            print("\nManual installation options:")
            print("  Download from: https://cli.github.com/")
            if self.system == "Windows":
                print("  Or use: winget install GitHub.cli")
                print("  Or use: choco install gh (if Chocolatey installed)")
            elif self.system == "Darwin":
                print("  Or use: brew install gh")
            else:
                print("  Or use: Follow instructions at https://github.com/cli/cli/blob/trunk/docs/install_linux.md")

            skip = input("Continue without GitHub CLI? (y/n): ")
            return skip.lower() == 'y'

    def install_claude_cli(self):
        """Install Claude Code CLI with enhanced error handling and admin elevation"""
        print("\n[6/7] Checking Claude Code CLI...")

        if self.check_command("claude"):
            print("[OK] Claude Code CLI already installed")
            # Verify it works
            success, version, _ = self.run_command(["claude", "--version"])
            if success:
                print(f"[OK] Claude CLI version: {version.strip()}")
            return True

        print("\n[INSTALL] Installing Claude Code CLI...")
        print("  This may require admin privileges on some systems.")

        # Prepare npm install command
        npm_cmd = ["npm", "install", "-g", "@anthropics/claude-code"]
        installation_attempts = []

        # Method 1: Try standard global installation
        print("\n[ATTEMPT 1] Standard global installation...")
        success, out, err = self.run_command(npm_cmd)
        installation_attempts.append(("Standard", success, err))

        if success and self.check_command("claude"):
            print("[OK] Claude Code CLI installed successfully")
            return True

        # Method 2: Try with elevated privileges (Windows) or sudo (Unix)
        if not success:
            if self.system == "Windows":
                print("\n[ATTEMPT 2] Trying with elevated privileges...")
                print("  You may see a UAC prompt - please approve it.")
                try:
                    # Try to elevate current process if not already admin
                    if not self.is_admin():
                        # Create a batch file to run npm with elevated privileges
                        batch_content = f'@echo off\ncd /d "{self.current_dir}"\nnpm install -g @anthropics/claude-code\npause'
                        batch_file = self.current_dir / "install_claude_elevated.bat"
                        with open(batch_file, 'w') as f:
                            f.write(batch_content)

                        # Run batch file as admin
                        import ctypes
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", str(batch_file), None, None, 1)

                        # Wait a moment and check if it worked
                        import time
                        time.sleep(3)
                        success = self.check_command("claude")
                        batch_file.unlink(missing_ok=True)  # Clean up
                    else:
                        # Already admin, just try again
                        success, out, err = self.run_command(npm_cmd)
                except Exception as e:
                    print(f"[WARNING] Elevation attempt failed: {e}")
                    success = False

                installation_attempts.append(("Elevated Windows", success, ""))
            else:
                # Unix systems - try with sudo
                if self.check_command("sudo"):
                    print("\n[ATTEMPT 2] Trying with sudo...")
                    sudo_cmd = ["sudo"] + npm_cmd
                    success, out, err = self.run_command(sudo_cmd)
                    installation_attempts.append(("Sudo", success, err))

        if success and self.check_command("claude"):
            print("[OK] Claude Code CLI installed with elevated privileges")
            return True

        # Method 3: Try user-local installation
        if not success:
            print("\n[ATTEMPT 3] Trying user-local installation...")
            npm_prefix = self.home / ".npm-global"
            npm_prefix.mkdir(exist_ok=True)

            # Set npm prefix for user installation
            success, _, _ = self.run_command(["npm", "config", "set", "prefix", str(npm_prefix)])
            if success:
                success, out, err = self.run_command(npm_cmd)
                installation_attempts.append(("User-local", success, err))

                if success:
                    bin_path = npm_prefix / "bin"
                    print(f"[OK] Installed to {bin_path}")
                    self.add_to_path(str(bin_path))

                    # Verify claude is now available
                    if self.check_command("claude"):
                        print("[OK] Claude Code CLI installed in user directory")
                        return True

        # Method 4: Try npx as fallback
        if not success and self.check_command("npx"):
            print("\n[ATTEMPT 4] Trying with npx...")
            npx_cmd = ["npx", "-g", "@anthropics/claude-code"]
            success, out, err = self.run_command(npx_cmd)
            installation_attempts.append(("npx", success, err))

            if success and self.check_command("claude"):
                print("[OK] Claude Code CLI installed via npx")
                return True

        # All methods failed - provide detailed error information
        print("\n[ERROR] All Claude Code CLI installation methods failed!")
        print("\nInstallation attempts:")
        for i, (method, succeeded, error) in enumerate(installation_attempts, 1):
            status = "✓" if succeeded else "✗"
            print(f"  {i}. {method}: {status}")
            if error and not succeeded:
                print(f"     Error: {error.strip()}")

        print("\n[MANUAL INSTALLATION] Please try one of these:")
        print("  1. Run Command Prompt as Administrator (Windows) or use sudo (Unix)")
        print("  2. npm install -g @anthropics/claude-code")
        print("  3. Or install Node.js with admin privileges first")
        print("  4. Check npm permissions: npm config get prefix")

        if self.system == "Windows":
            print("  5. Windows-specific: npm config set prefix \"%APPDATA%\\npm\"")
        else:
            print("  5. Unix-specific: sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}")

        return False

    def add_to_path(self, path_to_add):
        """Add a directory to PATH permanently (idempotent)"""
        print(f"\nAdding {path_to_add} to PATH...")
        path_to_add = str(Path(path_to_add).resolve())

        if self.system == "Windows":
            # Elevate if not admin
            if not self.is_admin():
                self.elevate()

            try:
                import winreg

                # Get current user PATH using proper registry access
                current_path = ""
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                        current_path, _ = winreg.QueryValueEx(key, "PATH")
                except (FileNotFoundError, OSError):
                    # PATH doesn't exist yet, that's fine
                    current_path = ""

                # Check if already in PATH using proper path separator
                path_entries = current_path.split(os.pathsep) if current_path else []
                if path_to_add not in path_entries:
                    new_path = os.pathsep.join(path_entries + [path_to_add]) if current_path else path_to_add

                    # Set new PATH using proper registry access
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)

                    print(f"[OK] Added {path_to_add} to Windows PATH")
                    return True
                else:
                    print(f"[OK] {path_to_add} already in Windows PATH")
                    return True

            except Exception as e:
                print(f"[ERROR] Failed to add {path_to_add} to PATH: {e}")
                print("Set manually in System Properties.")
                return False
        else:
            profile_file = self.get_profile_file()
            with open(profile_file, 'a') as f:
                f.write(f'\nexport PATH="$PATH:{path_to_add}"\n')
            print(f"[OK] Added {path_to_add} to {profile_file}")
            print("  Run: source ~/.bashrc (or equivalent) to apply changes.")
            return True

    def clean_existing_registry_keys(self):
        """Fix any existing corrupted registry keys from old setup method."""
        if self.system != "Windows":
            return

        print("\n[CLEANUP] Checking for corrupted registry keys...")

        try:
            import winreg
            keys_to_clean = ["XAI_API_KEY", "GROQ_API_KEY"]

            for key_name in keys_to_clean:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                        current_value, _ = winreg.QueryValueEx(key, key_name)

                    # Check if the value has the corrupted quote pattern
                    if current_value and ('"' in current_value or '\\' in current_value):
                        print(f"[CLEANUP] Fixing corrupted {key_name}...")

                        # Clean the value using our cleaning function
                        cleaned_value = clean_registry_value(current_value)

                        # Re-store it properly
                        if cleaned_value and cleaned_value != "NA":
                            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as reg_key:
                                winreg.SetValueEx(reg_key, key_name, 0, winreg.REG_SZ, cleaned_value)
                            print(f"[OK] Fixed {key_name}")

                except FileNotFoundError:
                    # Key doesn't exist, that's fine
                    continue
                except Exception as e:
                    print(f"[WARNING] Could not clean {key_name}: {e}")
                    continue

        except Exception as e:
            print(f"[WARNING] Registry cleanup failed: {e}")

    def setup_api_keys(self, force_setup=False):
        """Setup API keys and set as environment variables"""
        print("\n[7/7] Setting up API keys...")
        print("=" * 60)

        # Check existing keys
        xai_key = os.getenv("XAI_API_KEY", "NA")
        groq_key = os.getenv("GROQ_API_KEY", "NA")

        has_xai = xai_key != "NA" and xai_key
        has_groq = groq_key != "NA" and groq_key

        # xAI Setup if not set OR if force_setup is True
        if not has_xai or force_setup:
            if force_setup and has_xai:
                print(f"\n[SETUP] xAI Grok Setup (Current key: {xai_key[:10]}...)")
            else:
                print("\n[SETUP] xAI Grok Setup")
            print("  1. Visit: https://console.x.ai")
            print("  2. Create API key in 'API Keys' section")
            print("  3. Set spending limits in 'Billing' section!")
            print("\n  Cost: $0.20/$1.50 per million tokens (15x cheaper)")

            if force_setup and has_xai:
                key = input(f"\nEnter NEW xAI API key (or press Enter to keep current): ").strip()
                xai_key = key if key else xai_key  # Keep existing if no input
            else:
                key = input("\nEnter xAI API key (or press Enter to skip): ").strip()
                xai_key = key if key else "NA"

        # GroqCloud Setup if not set OR if force_setup is True
        if not has_groq or force_setup:
            if force_setup and has_groq:
                print(f"\n[SETUP] GroqCloud Setup (Current key: {groq_key[:10]}...)")
            else:
                print("\n[SETUP] GroqCloud Setup")
            print("  1. Visit: https://console.groq.com")
            print("  2. Create API key in 'API Keys' section")
            print("  3. Set spending limits in 'Billing' section!")
            print("\n  Cost: $0.15/$0.75 per million tokens (20x cheaper)")
            print("  Features: Web search, code execution tools")

            if force_setup and has_groq:
                key = input(f"\nEnter NEW GroqCloud API key (or press Enter to keep current): ").strip()
                groq_key = key if key else groq_key  # Keep existing if no input
            else:
                key = input("\nEnter GroqCloud API key (or press Enter to skip): ").strip()
                groq_key = key if key else "NA"

        # Check if at least one key is configured
        has_xai = xai_key != "NA" and xai_key
        has_groq = groq_key != "NA" and groq_key

        # Set environment variables permanently
        self.set_env_var("XAI_API_KEY", xai_key)
        self.set_env_var("GROQ_API_KEY", groq_key)

        # Only mark as configured if at least one valid key is set
        if has_xai or has_groq:
            self.set_env_var("CLAUDEPROXY_CONFIGURED", "CONFIGURED")
            print("\n[OK] API keys configured successfully!")
            return True
        else:
            print("\n[ERROR] No valid API keys configured!")
            return False

    def set_env_var(self, key, value):
        """Set environment variable permanently based on OS"""
        if self.system == "Windows":
            # Elevate if not admin
            if not self.is_admin():
                self.elevate()

            # Use proper winreg module instead of command line
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as reg_key:
                    winreg.SetValueEx(reg_key, key, 0, winreg.REG_SZ, value)
                print(f"[OK] Set {key} in Windows registry")
            except Exception as e:
                print(f"[ERROR] Failed to set {key} in registry: {e}")
                print("Set manually in System Properties.")
        else:
            profile_file = self.get_profile_file()
            # Remove existing entry to avoid duplicates
            with open(profile_file, 'r') as f:
                lines = f.readlines()
            with open(profile_file, 'w') as f:
                for line in lines:
                    if not line.startswith(f'export {key}='):
                        f.write(line)
                f.write(f'export {key}="{value}"\n')
            print(f"[OK] Set {key} in {profile_file}")
            print("  Run: source ~/.bashrc (or equivalent) to apply changes.")

    def get_profile_file(self):
        """Get appropriate shell profile file"""
        shell = os.getenv("SHELL", "").lower()
        if "zsh" in shell:
            return str(self.home / ".zshrc")
        elif "bash" in shell:
            return str(self.home / ".bashrc")
        else:
            return str(self.home / ".profile")

    def print_usage_instructions(self):
        """Print usage instructions"""
        print("\n" + "=" * 60)
        print("[SUCCESS] SETUP COMPLETE!")
        print("=" * 60)

        print("\n[GUIDE] Quick Start Guide:")
        print("-" * 40)

        if self.system == "Windows":
            print("\n1. Run the proxy and Claude CLI:")
            print("   claudeproxy          # Use configured provider(s)")
            print("   claudeproxy xai      # Force xAI Grok (port 5000)")
            print("   claudeproxy groq     # Force GroqCloud (port 5001)")
        else:
            print("\n1. Run the proxy and Claude CLI:")
            print("   ./claudeproxy.sh     # Use configured provider(s)")
            print("   ./claudeproxy.sh xai # Force xAI Grok (port 5000)")
            print("   ./claudeproxy.sh groq # Force GroqCloud (port 5001)")

        print("\n2. The proxy starts and runs a test Claude CLI command.")
        print("   Claude models (e.g., claude-3-5-sonnet, claude-3-opus) are mapped to:")
        print("   - xAI: grok-code-fast-1")
        print("   - Groq: groq/compound (with tools)")
        print("   Example output: A Python quicksort function.")

        print("\n3. For ongoing use, start proxy in one terminal:")
        print("   - Windows: python xai_claude_proxy.py (or groq_claude_proxy.py)")
        print("   - Unix: python3 xai_claude_proxy.py (or groq_claude_proxy.py)")
        print("   Then in another terminal, run Claude CLI:")
        print('   claude --settings \'{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5000/v1", "ANTHROPIC_API_KEY": "dummy_key"}}\' -p "Your prompt"')
        print("   Use port 5001 for GroqCloud.")

        print("\n📊 Cost Savings:")
        print("  • xAI: 15x cheaper than Claude Sonnet")
        print("  • GroqCloud: 20x cheaper with tools (web search, code execution)")

        print("\n[WARNING] Remember to set spending limits in provider consoles!")
        print("\n[WARNING] Troubleshooting:")
        print("  • If models fail, check xAI/Groq consoles for updated model names.")
        print("  • Ensure proxy is running before CLI commands.")
        print("  • Run 'claudeproxy setup' to reconfigure.")
        print("-" * 40)

    def run(self, force_setup=False):
        """Run the installer"""
        print("=" * 60)
        print("   ClaudeCodeProxy Universal Installer")
        print("=" * 60)
        print(f"System: {self.system}")
        print(f"Directory: {self.current_dir}")

        # Clean up any corrupted registry keys from previous installs
        self.clean_existing_registry_keys()

        # Check prerequisites
        if not self.check_python():
            print("\n[FAILED] Installation failed: Python 3.8+ required")
            return False

        if not self.install_python_packages():
            print("\n[FAILED] Installation failed: Python packages required")
            return False

        if not self.check_nodejs():
            print("\n[FAILED] Installation failed: Node.js required for Claude CLI")
            return False

        if not self.check_git():
            print("\n[WARNING] Warning: Git recommended for Claude Code")
            cont = input("\nContinue anyway? (y/n): ")
            if cont.lower() != 'y':
                return False

        if not self.check_github_cli():
            print("\n[WARNING] Warning: GitHub CLI recommended but not required")

        if not self.install_claude_cli():
            print("\n[FAILED] Installation failed: Claude Code CLI required")
            return False

        # Add current directory to PATH
        self.add_to_path(str(self.current_dir))

        # Setup API keys (force if requested)
        if force_setup or os.getenv("CLAUDEPROXY_CONFIGURED") != "CONFIGURED":
            if not self.setup_api_keys(force_setup=force_setup):
                print("\n[FAILED] Installation failed: At least one API key required")
                return False

        # Print usage instructions
        self.print_usage_instructions()

        return True

if __name__ == "__main__":
    installer = ClaudeProxyInstaller()
    force_setup = "setup" in sys.argv
    success = installer.run(force_setup=force_setup)

    if not success:
        sys.exit(1)

    # Offer to run test
    print("\n" + "=" * 60)
    test = input("Would you like to test the proxy and CLI now? (y/n): ")
    if test.lower() == 'y':
        if platform.system() == "Windows":
            subprocess.run(["claudeproxy"])
        else:
            subprocess.run(["./claudeproxy.sh"])