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
from getpass import getpass
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
        self.current_dir = Path.cwd()
        
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
        print("\n[1/5] Checking Python...")
        version_info = sys.version_info
        if version_info.major >= 3 and version_info.minor >= 8:
            print(f"[OK] Python {version_info.major}.{version_info.minor}.{version_info.micro} found")
            return True
        else:
            print(f"[ERROR] Python 3.8+ required (found {version_info.major}.{version_info.minor})")
            return False
    
    def install_python_packages(self):
        """Install required Python packages"""
        print("\n[2/5] Installing Python packages...")
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
    
    def check_nodejs(self):
        """Check Node.js and npm"""
        print("\n[3/5] Checking Node.js and npm...")
        
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
            print("\nPlease install Node.js from: https://nodejs.org/")
            if self.system == "Windows":
                print("  Or use: winget install OpenJS.NodeJS")
            elif self.system == "Darwin":
                print("  Or use: brew install node")
            else:
                print("  Or use: sudo apt install nodejs npm (Ubuntu/Debian)")
            return False
    
    def install_claude_cli(self):
        """Install Claude Code CLI"""
        print("\n[4/5] Checking Claude Code CLI...")
        
        if self.check_command("claude"):
            print("[OK] Claude Code CLI already installed")
            return True
        
        print("Installing Claude Code CLI...")
        npm_cmd = ["npm", "install", "-g", "@anthropics/claude-code"]
        success, out, err = self.run_command(npm_cmd)
        
        if not success:
            # Try with sudo for Unix
            if self.system != "Windows" and self.check_command("sudo"):
                print("[INFO] Trying with sudo...")
                npm_cmd = ["sudo"] + npm_cmd
                success, out, err = self.run_command(npm_cmd)
            # Try user prefix
            if not success:
                npm_prefix = self.home / ".npm-global"
                npm_prefix.mkdir(exist_ok=True)
                print(f"Trying user installation to {npm_prefix}...")
                self.run_command(["npm", "config", "set", "prefix", str(npm_prefix)])
                success, out, err = self.run_command(npm_cmd)
                if success:
                    print(f"[OK] Installed to {npm_prefix}/bin")
                    print(f"  Add to PATH: export PATH=$PATH:{npm_prefix}/bin")
                    self.add_to_path(str(npm_prefix / "bin"))
        
        if success or self.check_command("claude"):
            print("[OK] Claude Code CLI installed")
            return True
        else:
            print("[ERROR] Failed to install Claude Code CLI")
            print("  Try: npm install -g @anthropics/claude-code")
            return False
    
    def add_to_path(self, path_to_add):
        """Add a directory to PATH permanently (idempotent)"""
        print(f"\nAdding {path_to_add} to PATH...")
        current_path = os.getenv("PATH", "")
        path_to_add = str(path_to_add).replace("\\", "/")  # Normalize for cross-platform
        
        # Check if already in PATH
        if path_to_add in current_path.split(os.pathsep):
            print(f"[OK] {path_to_add} already in PATH")
            return True
        
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
        print("\n[5/5] Setting up API keys...")
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
            print("\n[WARNING] Warning: Node.js required for Claude CLI")
            cont = input("\nContinue anyway? (y/n): ")
            if cont.lower() != 'y':
                return False
        else:
            self.install_claude_cli()
        
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
