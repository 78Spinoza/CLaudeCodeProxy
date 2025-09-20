use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub enum DependencyStatus {
    Found(String),   // Version string
    NotFound,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DetectionResults {
    pub python: DependencyStatus,
    pub nodejs: DependencyStatus,
    pub git: DependencyStatus,
    pub claude: DependencyStatus,
}


pub async fn detect_python() -> DependencyStatus {
    // Try python3 first (preferred on Unix)
    if let Some(version) = check_command_version("python3", "--version").await {
        if is_python_version_sufficient(&version) {
            return DependencyStatus::Found(version);
        }
    }

    // Try python (Windows default)
    if let Some(version) = check_command_version("python", "--version").await {
        if is_python_version_sufficient(&version) {
            return DependencyStatus::Found(version);
        }
    }

    DependencyStatus::NotFound
}

pub async fn detect_nodejs() -> DependencyStatus {
    if let Some(version) = check_command_version("node", "--version").await {
        if is_nodejs_version_sufficient(&version) {
            return DependencyStatus::Found(version);
        }
    }

    DependencyStatus::NotFound
}

pub async fn detect_git() -> DependencyStatus {
    if let Some(version) = check_command_version("git", "--version").await {
        return DependencyStatus::Found(version);
    }

    DependencyStatus::NotFound
}

pub async fn detect_claude() -> DependencyStatus {
    println!("Starting comprehensive Claude Code detection...");

    // BULLETPROOF DETECTION: Try every possible method

    // Method 1: Standard command checks with comprehensive arguments
    let command_checks = [
        ("claude", "--version"),
        ("claude", "--help"),
        ("claude", "-h"),
        ("claude-code", "--version"),
        ("claude-code", "--help"),
        ("claude-code", "-h"),
    ];

    for (cmd, arg) in command_checks.iter() {
        println!("Trying command: {} {}", cmd, arg);
        if let Some(output) = check_command_version(cmd, arg).await {
            let output_lower = output.to_lowercase();
            // Check for ANY Claude Code indicators
            if output_lower.contains("claude") ||
               output_lower.contains("anthropic") ||
               output_lower.contains("code") ||
               output_lower.contains("@anthropics") ||
               output_lower.contains("claude-code") ||
               output_lower.contains("version") {
                println!("✅ Found Claude Code via command: {} {}", cmd, arg);
                return DependencyStatus::Found(format!("Claude Code ({})", cmd));
            }
        }
    }

    // Method 2: Check PATH for executables
    if let Ok(path_var) = std::env::var("PATH") {
        for path in path_var.split(if cfg!(windows) { ';' } else { ':' }) {
            let path_buf = std::path::PathBuf::from(path);

            // Check for claude executable
            let claude_exe = if cfg!(windows) {
                path_buf.join("claude.exe")
            } else {
                path_buf.join("claude")
            };

            if claude_exe.exists() {
                println!("✅ Found Claude Code executable at: {:?}", claude_exe);
                return DependencyStatus::Found("Claude Code (executable found)".to_string());
            }

            // Check for claude.cmd or claude.bat on Windows
            if cfg!(windows) {
                let claude_cmd = path_buf.join("claude.cmd");
                let claude_bat = path_buf.join("claude.bat");

                if claude_cmd.exists() {
                    println!("✅ Found Claude Code script at: {:?}", claude_cmd);
                    return DependencyStatus::Found("Claude Code (claude.cmd)".to_string());
                }

                if claude_bat.exists() {
                    println!("✅ Found Claude Code script at: {:?}", claude_bat);
                    return DependencyStatus::Found("Claude Code (claude.bat)".to_string());
                }
            }
        }
    }

    // Method 3: Check npm global modules
    if let Some(npm_output) = check_command_version("npm", "list -g @anthropics/claude-code").await {
        if npm_output.contains("@anthropics/claude-code") {
            println!("✅ Found Claude Code via npm global list");
            return DependencyStatus::Found("Claude Code (npm global)".to_string());
        }
    }

    // Method 4: Direct node module check
    if let Some(npx_output) = check_command_version("npx", "@anthropics/claude-code --version").await {
        if npx_output.to_lowercase().contains("claude") {
            println!("✅ Found Claude Code via npx");
            return DependencyStatus::Found("Claude Code (npx)".to_string());
        }
    }

    // Method 5: Check common installation directories
    let common_paths = if cfg!(windows) {
        vec![
            "C:\\Users\\%USERNAME%\\AppData\\Roaming\\npm\\claude.cmd",
            "C:\\Program Files\\nodejs\\claude.cmd",
            "C:\\Program Files (x86)\\nodejs\\claude.cmd",
        ]
    } else {
        vec![
            "/usr/local/bin/claude",
            "/usr/bin/claude",
            "~/.npm-global/bin/claude",
        ]
    };

    for path_str in common_paths {
        let expanded_path = if path_str.contains("%USERNAME%") {
            if let Ok(username) = std::env::var("USERNAME") {
                path_str.replace("%USERNAME%", &username)
            } else {
                continue;
            }
        } else if path_str.starts_with("~/") {
            if let Ok(home) = std::env::var("HOME") {
                format!("{}{}", home, &path_str[1..])
            } else {
                continue;
            }
        } else {
            path_str.to_string()
        };

        let path = std::path::PathBuf::from(expanded_path);
        if path.exists() {
            println!("✅ Found Claude Code at common path: {:?}", path);
            return DependencyStatus::Found("Claude Code (common path)".to_string());
        }
    }

    println!("❌ Claude Code not found after comprehensive check");
    DependencyStatus::NotFound
}

async fn check_command_version(command: &str, version_arg: &str) -> Option<String> {
    println!("Checking for command: {}", command);

    let output = Command::new(command)
        .arg(version_arg)
        .output();

    match output {
        Ok(output) => {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                let version = stdout.trim().to_string();
                println!("Found {} with version: {}", command, version);
                if !stderr.is_empty() {
                    println!("Command {} stderr: {}", command, stderr);
                }
                Some(version)
            } else {
                let stderr = String::from_utf8_lossy(&output.stderr);
                println!("Command {} failed with status: {}, stderr: {}", command, output.status, stderr);
                None
            }
        }
        Err(e) => {
            println!("Command {} failed to execute: {}", command, e);
            None
        }
    }
}

fn is_python_version_sufficient(version_string: &str) -> bool {
    // Parse "Python 3.11.0" or similar format
    if let Some(version_part) = version_string.split_whitespace().nth(1) {
        if let Some((major, rest)) = version_part.split_once('.') {
            if let Some((minor, _)) = rest.split_once('.') {
                if let (Ok(maj), Ok(min)) = (major.parse::<u32>(), minor.parse::<u32>()) {
                    return maj > 3 || (maj == 3 && min >= 8);
                }
            }
        }
    }
    false
}

fn is_nodejs_version_sufficient(version_string: &str) -> bool {
    // Parse "v18.17.0" or similar format
    let version_clean = version_string.trim_start_matches('v');
    if let Some((major, _)) = version_clean.split_once('.') {
        if let Ok(maj) = major.parse::<u32>() {
            return maj >= 16; // Node.js 16+ is sufficient
        }
    }
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_python_version_parsing() {
        assert!(is_python_version_sufficient("Python 3.8.0"));
        assert!(is_python_version_sufficient("Python 3.11.5"));
        assert!(!is_python_version_sufficient("Python 3.7.9"));
        assert!(!is_python_version_sufficient("Python 2.7.18"));
    }

    #[test]
    fn test_nodejs_version_parsing() {
        assert!(is_nodejs_version_sufficient("v18.17.0"));
        assert!(is_nodejs_version_sufficient("v16.0.0"));
        assert!(!is_nodejs_version_sufficient("v14.21.3"));
    }
}