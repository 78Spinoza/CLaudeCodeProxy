// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::PathBuf;
use std::process::Command;
use tauri::{Emitter, Window};
use serde::{Deserialize, Serialize};

mod dependency_detector;
mod downloader;
mod installer;

use dependency_detector::{DependencyStatus, *};
use downloader::*;
use installer::*;

#[derive(Debug, Serialize, Deserialize)]
struct ProgressUpdate {
    step: String,
    status: String,
    details: String,
    progress: u8,
}


#[derive(Debug, Serialize, Deserialize)]
struct ConfigurationResult {
    #[serde(rename = "installPath")]
    install_path: String,
}

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
async fn detect_dependencies(window: Window) -> Result<DetectionResults, String> {
    println!("Detecting system dependencies...");

    let emit_progress = |step: &str, status: &str, details: &str, progress: u8| {
        let update = ProgressUpdate {
            step: step.to_string(),
            status: status.to_string(),
            details: details.to_string(),
            progress,
        };
        let _ = window.emit("installation-progress", &update);
    };

    // Step 1: Detect system dependencies
    emit_progress("detect", "active", "Scanning system for existing dependencies...", 10);

    // Detect each dependency individually with progress feedback
    emit_progress("python", "active", "Checking for Python...", 11);
    let python_status = detect_python().await;
    match &python_status {
        DependencyStatus::Found(version) => emit_progress("python", "completed", &format!("✓ Found Python {}", version), 12),
        DependencyStatus::NotFound => emit_progress("python", "pending", "✗ Python not found - will install", 12),
    }

    emit_progress("nodejs", "active", "Checking for Node.js...", 13);
    let nodejs_status = detect_nodejs().await;
    match &nodejs_status {
        DependencyStatus::Found(version) => emit_progress("nodejs", "completed", &format!("✓ Found Node.js {}", version), 14),
        DependencyStatus::NotFound => emit_progress("nodejs", "pending", "✗ Node.js not found - will install", 14),
    }

    emit_progress("git", "active", "Checking for Git...", 15);
    let git_status = detect_git().await;
    match &git_status {
        DependencyStatus::Found(version) => emit_progress("git", "completed", &format!("✓ Found Git {}", version), 16),
        DependencyStatus::NotFound => emit_progress("git", "pending", "✗ Git not found - will install", 16),
    }

    emit_progress("claude", "active", "Checking for Claude Code...", 17);
    let claude_status = detect_claude().await;
    match &claude_status {
        DependencyStatus::Found(version) => emit_progress("claude", "completed", &format!("✓ Found {}", version), 18),
        DependencyStatus::NotFound => emit_progress("claude", "pending", "✗ Claude Code not found - will install", 18),
    }

    let detection_results = DetectionResults {
        python: python_status,
        nodejs: nodejs_status,
        git: git_status,
        claude: claude_status,
    };

    emit_progress("detect", "completed", "System scan complete", 19);

    Ok(detection_results)
}

#[tauri::command]
async fn start_installation(window: Window, detection_results: DetectionResults) -> Result<(), String> {
    println!("=== START_INSTALLATION COMMAND INVOKED ===");
    println!("Received detection results: {:?}", detection_results);
    println!("===========================================");

    let emit_progress = |step: &str, status: &str, details: &str, progress: u8| {
        let update = ProgressUpdate {
            step: step.to_string(),
            status: status.to_string(),
            details: details.to_string(),
            progress,
        };
        let _ = window.emit("installation-progress", &update);
    };

    let emit_error = |message: &str| {
        let error = serde_json::json!({ "message": message });
        let _ = window.emit("installation-error", &error);
    };

    // Step 2: Install Python if needed
    match &detection_results.python {
        DependencyStatus::Found(_) => {
            emit_progress("python", "completed", "✓ Python already installed - skipping", 25);
        }
        DependencyStatus::NotFound => {
            emit_progress("python", "active", "Installing Python...", 22);
            match download_python().await {
                Ok(_) => emit_progress("python", "completed", "Python installed successfully", 25),
                Err(e) => {
                    emit_error(&format!("Failed to install Python: {}", e));
                    return Err(format!("Python installation failed: {}", e));
                }
            }
        }
    }

    // Step 3: Install Node.js if needed
    match &detection_results.nodejs {
        DependencyStatus::Found(_) => {
            emit_progress("nodejs", "completed", "✓ Node.js already installed - skipping", 40);
        }
        DependencyStatus::NotFound => {
            emit_progress("nodejs", "active", "Installing Node.js...", 35);
            match download_nodejs().await {
                Ok(_) => emit_progress("nodejs", "completed", "Node.js installed successfully", 40),
                Err(e) => {
                    emit_error(&format!("Failed to install Node.js: {}", e));
                    return Err(format!("Node.js installation failed: {}", e));
                }
            }
        }
    }

    // Step 4: Install Git if needed
    match &detection_results.git {
        DependencyStatus::Found(_) => {
            emit_progress("git", "completed", "✓ Git already installed - skipping", 55);
        }
        DependencyStatus::NotFound => {
            emit_progress("git", "active", "Installing Git...", 50);
            match download_git().await {
                Ok(_) => emit_progress("git", "completed", "Git installed successfully", 55),
                Err(e) => {
                    emit_error(&format!("Failed to install Git: {}", e));
                    return Err(format!("Git installation failed: {}", e));
                }
            }
        }
    }

    // Step 5: Install Claude Code if needed
    match &detection_results.claude {
        DependencyStatus::Found(_) => {
            emit_progress("claude", "completed", "✓ Claude Code already installed - skipping", 75);
        }
        DependencyStatus::NotFound => {
            emit_progress("claude", "active", "Installing Claude Code...", 65);
            match install_claude_cli().await {
                Ok(_) => emit_progress("claude", "completed", "Claude Code installed successfully", 75),
                Err(e) => {
                    emit_error(&format!("Failed to install Claude Code: {}", e));
                    return Err(format!("Claude Code installation failed: {}", e));
                }
            }
        }
    }

    // Step 6: Install proxy scripts
    emit_progress("proxy", "active", "Installing proxy scripts...", 80);
    println!("EMITTING: proxy active");

    match install_proxy_scripts().await {
        Ok(_) => {
            println!("EMITTING: proxy completed");
            emit_progress("proxy", "completed", "Proxy scripts installed successfully", 90);
        },
        Err(e) => {
            emit_error(&format!("Failed to install proxy scripts: {}", e));
            return Err(format!("Proxy scripts installation failed: {}", e));
        }
    }

    // Step 7: Create shortcuts
    emit_progress("shortcuts", "active", "Creating desktop shortcuts...", 95);
    println!("EMITTING: shortcuts active");

    match create_shortcuts().await {
        Ok(_) => {
            println!("EMITTING: shortcuts completed");
            emit_progress("shortcuts", "completed", "Installation complete!", 100);
        },
        Err(e) => {
            emit_error(&format!("Failed to create shortcuts: {}", e));
            return Err(format!("Shortcut creation failed: {}", e));
        }
    }

    println!("Installation completed successfully!");
    Ok(())
}

#[derive(Debug, Serialize, Deserialize)]
struct ExistingKeys {
    xai_key: String,
    groq_key: String,
    has_xai: bool,
    has_groq: bool,
}

#[tauri::command]
async fn check_existing_keys() -> Result<ExistingKeys, String> {
    println!("Checking for existing API keys...");

    // Get existing keys from environment
    let xai_key = std::env::var("XAI_API_KEY").unwrap_or_default();
    let groq_key = std::env::var("GROQ_API_KEY").unwrap_or_default();

    // Clean registry values (remove Windows registry quotes)
    let xai_key_clean = clean_registry_value(&xai_key);
    let groq_key_clean = clean_registry_value(&groq_key);

    // Check if keys are valid (not empty and not "NA")
    let has_xai = !xai_key_clean.is_empty() && xai_key_clean != "NA";
    let has_groq = !groq_key_clean.is_empty() && groq_key_clean != "NA";

    Ok(ExistingKeys {
        xai_key: if has_xai { format!("{}...", &xai_key_clean[..std::cmp::min(10, xai_key_clean.len())]) } else { "".to_string() },
        groq_key: if has_groq { format!("{}...", &groq_key_clean[..std::cmp::min(10, groq_key_clean.len())]) } else { "".to_string() },
        has_xai,
        has_groq,
    })
}

fn clean_registry_value(raw_value: &str) -> String {
    if raw_value.is_empty() {
        return raw_value.to_string();
    }

    let mut value = raw_value.trim().to_string();

    // Windows registry quote cleaning (same logic as Python setup)
    #[cfg(target_os = "windows")]
    {
        let quote_patterns = vec!["\"\\\"", "\\\"", "\"'", "'\"", "\"\"", "''", "\"", "'"];

        let mut changed = true;
        while changed {
            changed = false;
            let original = value.clone();

            // Remove quotes from start and end
            for pattern in &quote_patterns {
                if value.starts_with(pattern) {
                    value = value[pattern.len()..].to_string();
                    changed = true;
                }
                if value.ends_with(pattern) {
                    value = value[..value.len() - pattern.len()].to_string();
                    changed = true;
                }
            }

            // Simple quote removal
            if value.starts_with('"') && value.ends_with('"') {
                value = value[1..value.len()-1].to_string();
                changed = true;
            }
            if value.starts_with('\'') && value.ends_with('\'') {
                value = value[1..value.len()-1].to_string();
                changed = true;
            }

            if value != original {
                changed = true;
            }
        }

        // Remove escape characters
        value = value.replace("\\\"", "\"").replace("\\'", "'").replace("\\\\", "\\");
        value = value.trim_end_matches('\\').trim_end_matches('"').trim_end_matches('\'').to_string();
    }
    #[cfg(not(target_os = "windows"))]
    {
        // Simple quote removal for Unix
        if (value.starts_with('"') && value.ends_with('"')) || (value.starts_with('\'') && value.ends_with('\'')) {
            value = value[1..value.len()-1].to_string();
        }
    }

    value.trim().to_string()
}

#[tauri::command]
async fn save_configuration(
    xai_key: String,
    groq_key: String,
) -> Result<ConfigurationResult, String> {
    println!("Saving configuration...");

    let install_path = get_install_path().map_err(|e| format!("Failed to get install path: {}", e))?;

    // Save environment variables (skip if KEEP_EXISTING)
    if !xai_key.is_empty() && xai_key != "KEEP_EXISTING" {
        set_environment_variable("XAI_API_KEY", &xai_key)?;
    }

    if !groq_key.is_empty() && groq_key != "KEEP_EXISTING" {
        set_environment_variable("GROQ_API_KEY", &groq_key)?;
    }

    // Mark as configured
    set_environment_variable("CLAUDEPROXY_CONFIGURED", "CONFIGURED")?;

    Ok(ConfigurationResult {
        install_path: install_path.to_string_lossy().to_string(),
    })
}

#[tauri::command]
async fn launch_proxy() -> Result<(), String> {
    println!("Opening command prompt with claudeproxy instructions...");

    // Instead of launching a specific proxy, open command prompt and show instructions
    #[cfg(target_os = "windows")]
    {
        // Create a batch file with instructions
        let temp_batch = std::env::temp_dir().join("claudeproxy_instructions.bat");
        let instructions = r#"@echo off
echo ========================================
echo   Claude Proxy is now available globally!
echo ========================================
echo.
echo Usage Instructions:
echo 1. Open Command Prompt (Win+R, type 'cmd')
echo 2. Navigate to your work folder: cd C:\YourProject
echo 3. Run: claudeproxy
echo.
echo Example:
echo   C:\^> cd C:\MyProjects
echo   C:\MyProjects^> claudeproxy
echo.
echo The proxy will start and show available options.
echo Press any key to continue...
pause > nul
"#;

        std::fs::write(&temp_batch, instructions)
            .map_err(|e| format!("Failed to create instructions: {}", e))?;

        Command::new("cmd")
            .args(&["/c", "start", "cmd", "/k", temp_batch.to_str().unwrap()])
            .spawn()
            .map_err(|e| format!("Failed to open command prompt: {}", e))?;
    }

    #[cfg(not(target_os = "windows"))]
    {
        // For Unix systems, try to open terminal with instructions
        println!("claudeproxy has been added to your PATH");
        println!("Usage: Open terminal and run 'claudeproxy' from any directory");
    }

    Ok(())
}

#[tauri::command]
async fn open_url(url: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args(&["/c", "start", &url])
            .spawn()
            .map_err(|e| format!("Failed to open URL: {}", e))?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&url)
            .spawn()
            .map_err(|e| format!("Failed to open URL: {}", e))?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&url)
            .spawn()
            .map_err(|e| format!("Failed to open URL: {}", e))?;
    }

    Ok(())
}

#[tauri::command]
async fn open_install_folder() -> Result<(), String> {
    let install_path = get_install_path().map_err(|e| format!("Failed to get install path: {}", e))?;

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(install_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(install_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(install_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }

    Ok(())
}

fn get_install_path() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let home = dirs::home_dir().ok_or("Unable to find home directory")?;
    Ok(home.join("claude-proxy"))
}

fn set_environment_variable(name: &str, value: &str) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        use std::process::Command;

        // Safety check: Never use setx for PATH variables due to 1024 character truncation risk
        if name.to_uppercase() == "PATH" {
            return Err("ERROR: PATH variables must be set using PowerShell to avoid truncation. Use add_to_path() function instead.".to_string());
        }

        // setx is safe for short values like API keys (under 1024 characters)
        if value.len() > 1000 {
            return Err(format!("WARNING: Value too long ({} chars). Risk of truncation with setx.", value.len()));
        }

        let output = Command::new("setx")
            .args(&[name, value])
            .output()
            .map_err(|e| format!("Failed to set environment variable: {}", e))?;

        if !output.status.success() {
            return Err(format!(
                "Failed to set environment variable: {}",
                String::from_utf8_lossy(&output.stderr)
            ));
        }
    }

    #[cfg(not(target_os = "windows"))]
    {
        // For Unix systems, we'll add to shell profile
        let home = dirs::home_dir().ok_or("Unable to find home directory")?;
        let profile_path = home.join(".bashrc");

        let export_line = format!("export {}=\"{}\"\n", name, value);

        std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(profile_path)
            .map_err(|e| format!("Failed to open profile: {}", e))?
            .write_all(export_line.as_bytes())
            .map_err(|e| format!("Failed to write to profile: {}", e))?;
    }

    Ok(())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            detect_dependencies,
            start_installation,
            check_existing_keys,
            save_configuration,
            launch_proxy,
            open_url,
            open_install_folder
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}