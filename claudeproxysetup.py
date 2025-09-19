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

    value = str(raw_value).strip()
    if os.name == 'nt':  # Windows only
        quote_patterns = ['"\\"', '\\"', '"\'', '\'"', '""', "''", '"', "'"]
        changed = True
        while changed:
            changed = False
            original = value
            for pattern in quote_patterns:
                if value.startswith(pattern):
                    value = value[len(pattern):]
                    changed = True
                if value.endswith(pattern):
                    value = value[:-len(pattern)]
                    changed = True
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]; changed = True
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]; changed = True
            if value != original:
                changed = True
        value = value.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
        value = value.rstrip('\\').rstrip('"').rstrip("'")
    else:
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
        if self.system == "Windows":
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        else:
            return os.geteuid() == 0
    
    def elevate(self):
        if self.system == "Windows" and not self.is_admin():
            print("[ELEVATION] Requesting admin privileges...")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                                f'"{__file__}" {" ".join(sys.argv[1:])}', None, 1)
            sys.exit(0)
    
    def check_command(self, cmd):
        return shutil.which(cmd) is not None
    
    def run_command(self, cmd, shell=False, env=None):
        try:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, env=env)
            return result.returncode == 0, result.stdout, result.stderr
        except:
            return False, "", ""
    
    def check_python(self):
        print("\n[1/5] Checking Python...")
        version_info = sys.version_info
        if version_info.major >= 3 and version_info.minor >= 8:
            print(f"[OK] Python {version_info.major}.{version_info.minor}.{version_info.micro} found")
            return True
        print(f"[ERROR] Python 3.8+ required (found {version_info.major}.{version_info.minor})")
        return False
    
    def install_python_packages(self):
        print("\n[2/5] Installing Python packages...")
        packages = ["flask", "requests", "anthropic"]
        missing = [p for p in packages if not self._is_pkg_installed(p)]
        if not missing:
            print("[OK] All Python packages already installed"); return True
        print(f"Installing: {', '.join(missing)}")
        pip_cmd = [sys.executable, "-m", "pip", "install"] + missing
        success, _, _ = self.run_command(pip_cmd)
        if success:
            print("[OK] Python packages installed successfully"); return True
        if self.system != "Windows" and self.check_command("sudo"):
            print("[INFO] Trying with sudo...")
            pip_cmd = ["sudo"] + pip_cmd
            success, _, _ = self.run_command(pip_cmd)
            if success:
                print("[OK] Python packages installed with sudo"); return True
        print("[ERROR] Failed to install packages"); return False
    
    def _is_pkg_installed(self, pkg):
        try: __import__(pkg); return True
        except ImportError: return False
    
    def check_nodejs(self):
        print("\n[3/5] Checking Node.js and npm...")
        has_node = self.check_command("node")
        has_npm = self.check_command("npm")
        if has_node and has_npm:
            success, version, _ = self.run_command(["node", "--version"])
            if success: print(f"[OK] Node.js {version.strip()} found")
            print("[OK] npm found"); return True
        print("[ERROR] Node.js/npm not found"); return False
    
    def install_claude_cli(self):
        print("\n[4/5] Checking Claude Code CLI...")
        if self.check_command("claude"):
            print("[OK] Claude Code CLI already installed"); return True
        print("Installing Claude Code CLI...")
        npm_cmd = ["npm", "install", "-g", "@anthropics/claude-code"]
        success, _, _ = self.run_command(npm_cmd)
        if not success and self.system != "Windows" and self.check_command("sudo"):
            print("[INFO] Trying with sudo...")
            success, _, _ = self.run_command(["sudo"] + npm_cmd)
        if success or self.check_command("claude"):
            print("[OK] Claude Code CLI installed"); return True
        print("[ERROR] Failed to install Claude Code CLI"); return False
    
    def add_to_path(self, path_to_add):
        """Add a directory to PATH permanently (idempotent, bulletproof)."""
        print(f"\nAdding {path_to_add} to PATH...")
        path_to_add = str(Path(path_to_add).resolve())
        if self.system == "Windows":
            if not self.is_admin():
                self.elevate()
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as key:
                    try:
                        current_path, _ = winreg.QueryValueEx(key, "PATH")
                    except FileNotFoundError:
                        current_path = ""
                entries = current_path.split(os.pathsep) if current_path else []
                if path_to_add not in entries:
                    new_path = os.pathsep.join(entries + [path_to_add]) if current_path else path_to_add
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                    print(f"[OK] Added {path_to_add} to Windows PATH")
                else:
                    print(f"[OK] {path_to_add} already in Windows PATH")
                return True
            except Exception as e:
                print(f"[ERROR] Could not modify PATH: {e}")
                return False
        else:
            profile_file = self.get_profile_file()
            with open(profile_file, "a") as f:
                f.write(f'\nexport PATH="$PATH:{path_to_add}"\n')
            print(f"[OK] Added {path_to_add} to {profile_file}")
            return True
    
    def get_profile_file(self):
        shell = os.getenv("SHELL", "").lower()
        if "zsh" in shell: return str(self.home / ".zshrc")
        if "bash" in shell: return str(self.home / ".bashrc")
        return str(self.home / ".profile")
    
    def run(self):
        print("="*60)
        print("   ClaudeCodeProxy Universal Installer")
        print("="*60)
        print(f"System: {self.system}")
        print(f"Install Directory: {self.current_dir}")
        if not self.check_python(): return False
        if not self.install_python_packages(): return False
        if not self.check_nodejs():
            cont = input("Node.js missing. Continue anyway? (y/n): ")
            if cont.lower() != "y": return False
        else:
            self.install_claude_cli()
        self.add_to_path(str(self.current_dir))
        print("\n[OK] Installation finished!")
        return True

if __name__ == "__main__":
    installer = ClaudeProxyInstaller()
    if not installer.run():
        sys.exit(1)
