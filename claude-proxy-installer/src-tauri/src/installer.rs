use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

pub async fn install_claude_cli() -> Result<(), Box<dyn std::error::Error>> {
    println!("Installing Claude Code...");

    // First try to find npm in common installation paths
    let npm_paths = get_npm_paths();

    for npm_path in &npm_paths {
        println!("Trying npm at: {:?}", npm_path);

        if npm_path.exists() {
            let mut command = Command::new(npm_path);
            command.args(&["install", "-g", "@anthropics/claude-code"]);

            match command.status() {
                Ok(status) if status.success() => {
                    println!("Claude Code installed successfully via npm at {:?}", npm_path);

                    // Verify installation
                    if verify_claude_cli().await? {
                        return Ok(());
                    } else {
                        println!("Installation succeeded but verification failed");
                    }
                }
                Ok(status) => {
                    println!("npm installation failed with status: {}", status);
                }
                Err(e) => {
                    println!("npm installation failed with error: {}", e);
                }
            }
        }
    }

    // Fallback: try system PATH npm (might work if already installed)
    println!("Trying system PATH npm...");
    let mut command = Command::new("npm");
    command.args(&["install", "-g", "@anthropics/claude-code"]);

    match command.status() {
        Ok(status) if status.success() => {
            println!("Claude Code installed successfully via system npm");
            if verify_claude_cli().await? {
                return Ok(());
            }
        }
        Ok(_) | Err(_) => {
            println!("System npm installation failed, trying local installation...");
        }
    }

    // If all methods fail, try user-local installation
    println!("Trying user-local installation...");
    install_claude_cli_local().await
}

fn get_npm_paths() -> Vec<PathBuf> {
    let mut paths = Vec::new();

    // Common npm installation locations on Windows
    if cfg!(windows) {
        if let Some(program_files) = std::env::var_os("PROGRAMFILES") {
            paths.push(PathBuf::from(&program_files).join("nodejs").join("npm.cmd"));
            paths.push(PathBuf::from(&program_files).join("nodejs").join("npm.exe"));
        }

        if let Some(appdata) = std::env::var_os("APPDATA") {
            paths.push(PathBuf::from(&appdata).join("npm").join("npm.cmd"));
        }

        if let Some(home) = dirs::home_dir() {
            paths.push(home.join("AppData").join("Local").join("Programs").join("nodejs").join("npm.cmd"));
            paths.push(home.join("AppData").join("Roaming").join("npm").join("npm.cmd"));
        }
    }

    // Unix-like systems
    if cfg!(unix) {
        paths.push(PathBuf::from("/usr/bin/npm"));
        paths.push(PathBuf::from("/usr/local/bin/npm"));
        paths.push(PathBuf::from("/opt/nodejs/bin/npm"));

        if let Some(home) = dirs::home_dir() {
            paths.push(home.join(".nvm").join("versions").join("node").join("latest").join("bin").join("npm"));
        }
    }

    paths
}

async fn verify_claude_cli() -> Result<bool, Box<dyn std::error::Error>> {
    // Try multiple common Claude Code command patterns
    let commands_to_try = [
        ("claude", "--version"),
        ("claude", "--help"),
        ("claude-code", "--version"),
        ("claude-code", "--help"),
    ];

    for (cmd, arg) in commands_to_try.iter() {
        let output = Command::new(cmd)
            .arg(arg)
            .output();

        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                let combined = format!("{} {}", stdout, stderr);

                // Check if output contains Claude Code indicators
                if combined.to_lowercase().contains("claude") ||
                   combined.to_lowercase().contains("anthropic") {
                    println!("Claude Code verified with command: {} {}", cmd, arg);
                    return Ok(true);
                }
            }
            Ok(_) => println!("Command {} {} returned non-zero exit code", cmd, arg),
            Err(e) => println!("Command {} {} failed: {}", cmd, arg, e),
        }
    }

    println!("Claude Code verification failed - no working command found");
    Ok(false)
}

async fn install_claude_cli_local() -> Result<(), Box<dyn std::error::Error>> {
    let home = dirs::home_dir().ok_or("Unable to find home directory")?;
    let npm_global = home.join(".npm-global");

    // Create npm global directory
    fs::create_dir_all(&npm_global)?;

    // Set npm prefix
    let status = Command::new("npm")
        .args(["config", "set", "prefix", npm_global.to_str().unwrap()])
        .status()?;

    if !status.success() {
        return Err("Failed to set npm prefix".into());
    }

    // Install Claude Code locally
    let status = Command::new("npm")
        .args(["install", "-g", "@anthropics/claude-code"])
        .status()?;

    if !status.success() {
        return Err("Failed to install Claude Code locally".into());
    }

    // Add to PATH
    let bin_path = npm_global.join("bin");
    add_to_path(&bin_path)?;

    println!("Claude Code installed to user directory: {:?}", bin_path);
    Ok(())
}

pub async fn install_proxy_scripts() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== STARTING PROXY SCRIPTS INSTALLATION ===");

    let install_dir = get_install_directory()?;
    println!("Install directory: {:?}", install_dir);

    // Embed actual proxy files from main directory using include_str!
    let scripts = vec![
        ("xai_claude_proxy_enhanced.py", include_str!("../../../xai_claude_proxy_enhanced.py")),
        ("groq_claude_proxy_enhanced.py", include_str!("../../../groq_claude_proxy_enhanced.py")),
        ("proxy_core.py", include_str!("../../../proxy_core.py")),
        ("proxy_common.py", include_str!("../../../proxy_common.py")),
        ("xai_adapter.py", include_str!("../../../xai_adapter.py")),
        ("groq_adapter.py", include_str!("../../../groq_adapter.py")),
        ("claudeproxy.bat", include_str!("../../../claudeproxy.bat")),
        ("claudeproxy.sh", include_str!("../../../claudeproxy.sh")),
        ("start_xai_proxy.bat", include_str!("../../../start_xai_proxy.bat")),
        ("start_groq_proxy.bat", include_str!("../../../start_groq_proxy.bat")),
        ("claudeproxysetup.py", include_str!("../../../claudeproxysetup.py")),
    ];

    println!("Installing {} proxy scripts from embedded sources...", scripts.len());

    for (i, (filename, content)) in scripts.iter().enumerate() {
        let dest_path = install_dir.join(filename);
        println!("[{}/{}] Writing {} ({} bytes)", i+1, scripts.len(), filename, content.len());

        match fs::write(&dest_path, content) {
            Ok(_) => println!("✓ Successfully wrote {}", filename),
            Err(e) => {
                println!("✗ Failed to write {}: {}", filename, e);
                return Err(e.into());
            }
        }
    }

    // Check and add install directory to PATH so claudeproxy works globally
    println!("Checking if claude-proxy folder is in system PATH...");

    if is_in_path(&install_dir)? {
        println!("✓ claude-proxy folder already in PATH: {:?}", install_dir);
    } else {
        println!("Adding claude-proxy folder to system PATH...");
        match add_to_path(&install_dir) {
            Ok(_) => {
                println!("✓ Added claude-proxy folder to PATH: {:?}", install_dir);

                // Verify it was actually added
                if is_in_path(&install_dir)? {
                    println!("✓ PATH addition verified successfully");
                } else {
                    println!("⚠ WARNING: PATH addition may not have taken effect immediately");
                    println!("  You may need to restart your command prompt or reboot");
                }
            },
            Err(e) => {
                println!("✗ Failed to add claude-proxy folder to PATH: {}", e);
                return Err(format!("PATH addition failed: {}", e).into());
            }
        }
    }

    println!("=== PROXY SCRIPTS INSTALLATION COMPLETE ===");
    Ok(())
}

pub async fn create_shortcuts() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== STARTING SHORTCUTS CREATION ===");

    let install_dir = get_install_directory()?;
    println!("Install directory for shortcuts: {:?}", install_dir);

    // Simplified shortcut creation - just create basic batch files
    #[cfg(target_os = "windows")]
    {
        let desktop = match dirs::desktop_dir() {
            Some(dir) => dir,
            None => {
                println!("⚠ Could not find desktop directory, skipping shortcuts");
                return Ok(());
            }
        };

        let install_dir = get_install_directory()?;
        let shortcuts = vec![
            ("xAI Claude Proxy.bat", format!("@echo off\ncd /d \"{}\"\ncall start_xai_proxy.bat", install_dir.display())),
            ("GroqCloud Claude Proxy.bat", format!("@echo off\ncd /d \"{}\"\ncall start_groq_proxy.bat", install_dir.display())),
        ];

        for (filename, content) in shortcuts {
            let shortcut_path = desktop.join(filename);
            match fs::write(&shortcut_path, &content) {
                Ok(_) => println!("✓ Created shortcut: {:?}", shortcut_path),
                Err(e) => println!("⚠ Failed to create shortcut {}: {}", filename, e),
            }
        }
    }

    // Skip shortcuts on Unix for now to avoid hanging
    #[cfg(not(target_os = "windows"))]
    {
        println!("⚠ Skipping shortcuts creation on Unix to avoid hanging");
    }

    println!("=== SHORTCUTS CREATION COMPLETE ===");
    Ok(())
}

fn get_install_directory() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let home = dirs::home_dir().ok_or("Unable to find home directory")?;
    let install_dir = home.join("claude-proxy");
    fs::create_dir_all(&install_dir)?;
    Ok(install_dir)
}


#[cfg(not(target_os = "windows"))]
fn make_scripts_executable(dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
    use std::os::unix::fs::PermissionsExt;

    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.extension().and_then(|s| s.to_str()) == Some("py") {
            let mut perms = fs::metadata(&path)?.permissions();
            perms.set_mode(0o755); // rwxr-xr-x
            fs::set_permissions(&path, perms)?;
        }
    }

    Ok(())
}




fn is_in_path(path: &Path) -> Result<bool, Box<dyn std::error::Error>> {
    let path_str = path.to_str().ok_or("Invalid path")?;

    #[cfg(target_os = "windows")]
    {
        // Use PowerShell to accurately check both user and system PATH
        let powershell_script = format!(
            r#"
            $search_path = '{}'
            $user_path = [Environment]::GetEnvironmentVariable('PATH', 'User')
            $system_path = [Environment]::GetEnvironmentVariable('PATH', 'Machine')
            $combined_path = "$user_path;$system_path"

            $path_entries = $combined_path -split ';'
            $found = $false
            foreach ($entry in $path_entries) {{
                if ($entry.Trim().ToLower() -eq $search_path.ToLower()) {{
                    $found = $true
                    break
                }}
            }}

            if ($found) {{
                Write-Output 'FOUND'
            }} else {{
                Write-Output 'NOT_FOUND'
            }}
            "#,
            path_str
        );

        let output = Command::new("powershell")
            .args(["-ExecutionPolicy", "Bypass", "-Command", &powershell_script])
            .output()?;

        if !output.status.success() {
            return Err(format!(
                "Failed to check PATH: {}",
                String::from_utf8_lossy(&output.stderr)
            ).into());
        }

        let output_str = String::from_utf8_lossy(&output.stdout);
        let result = output_str.trim();
        Ok(result == "FOUND")
    }

    #[cfg(not(target_os = "windows"))]
    {
        let current_path = std::env::var("PATH").unwrap_or_default();
        let path_entries: Vec<&str> = current_path.split(':').collect();

        // Check if our path is already in PATH
        for entry in path_entries {
            if entry.trim() == path_str {
                return Ok(true);
            }
        }
        Ok(false)
    }
}

pub fn add_to_path(path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    #[cfg(target_os = "windows")]
    {
        let path_str = path.to_str().ok_or("Invalid path")?;

        // Use PowerShell to safely add to PATH without truncation
        // This method can handle PATH variables up to 32,767 characters
        let powershell_script = format!(
            r#"
            $new_entry = '{}'
            $old_path = [Environment]::GetEnvironmentVariable('PATH', 'User')
            if ($old_path -eq $null) {{ $old_path = '' }}
            if ($old_path -notlike "*$new_entry*") {{
                if ($old_path -ne '' -and -not $old_path.EndsWith(';')) {{
                    $old_path += ';'
                }}
                $new_path = $old_path + $new_entry
                [Environment]::SetEnvironmentVariable('PATH', $new_path, 'User')
                Write-Output 'SUCCESS: Added to PATH'
            }} else {{
                Write-Output 'ALREADY_EXISTS: Path already in PATH'
            }}
            "#,
            path_str
        );

        let output = Command::new("powershell")
            .args(["-ExecutionPolicy", "Bypass", "-Command", &powershell_script])
            .output()?;

        if !output.status.success() {
            return Err(format!(
                "Failed to add to PATH: {}",
                String::from_utf8_lossy(&output.stderr)
            ).into());
        }

        println!("PowerShell PATH update output: {}", String::from_utf8_lossy(&output.stdout));
    }

    #[cfg(not(target_os = "windows"))]
    {
        let home = dirs::home_dir().ok_or("Unable to find home directory")?;
        let profile_path = home.join(".bashrc");

        let export_line = format!("export PATH=\"$PATH:{}\"\n", path.display());

        use std::io::Write;
        std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(profile_path)?
            .write_all(export_line.as_bytes())?;
    }

    Ok(())
}