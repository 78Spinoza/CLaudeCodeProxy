use std::fs;
use std::path::{Path, PathBuf};
use std::io::Write;
use reqwest;

const PYTHON_WINDOWS_URL: &str = "https://github.com/indygreg/python-build-standalone/releases/download/20231002/cpython-3.11.6+20231002-x86_64-pc-windows-msvc-shared-install_only.tar.gz";
const NODEJS_WINDOWS_URL: &str = "https://nodejs.org/dist/v18.18.2/node-v18.18.2-win-x64.zip";
const GIT_WINDOWS_URL: &str = "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/PortableGit-2.42.0.2-64-bit.7z.exe";

pub async fn download_python() -> Result<PathBuf, Box<dyn std::error::Error>> {
    println!("Downloading Python...");

    let install_dir = get_install_directory()?;
    let python_dir = install_dir.join("python");

    #[cfg(target_os = "windows")]
    {
        let url = PYTHON_WINDOWS_URL;
        let file_name = "python.tar.gz";
        let download_path = install_dir.join(file_name);

        download_file(url, &download_path).await?;
        extract_archive(&download_path, &python_dir)?;

        // Add to PATH
        add_to_system_path(&python_dir)?;
        add_to_system_path(&python_dir.join("Scripts"))?;

        println!("Python installed to: {:?}", python_dir);
        Ok(python_dir)
    }

    #[cfg(not(target_os = "windows"))]
    {
        // For Unix systems, use system package manager or pyenv
        install_python_unix().await
    }
}

pub async fn download_nodejs() -> Result<PathBuf, Box<dyn std::error::Error>> {
    println!("Downloading Node.js...");

    let install_dir = get_install_directory()?;
    let nodejs_dir = install_dir.join("nodejs");

    #[cfg(target_os = "windows")]
    {
        let url = NODEJS_WINDOWS_URL;
        let file_name = "nodejs.zip";
        let download_path = install_dir.join(file_name);

        download_file(url, &download_path).await?;
        extract_zip(&download_path, &nodejs_dir)?;

        // Add to PATH
        add_to_system_path(&nodejs_dir)?;

        println!("Node.js installed to: {:?}", nodejs_dir);
        Ok(nodejs_dir)
    }

    #[cfg(not(target_os = "windows"))]
    {
        install_nodejs_unix().await
    }
}

pub async fn download_git() -> Result<PathBuf, Box<dyn std::error::Error>> {
    println!("Downloading Git...");

    let install_dir = get_install_directory()?;
    let git_dir = install_dir.join("git");

    #[cfg(target_os = "windows")]
    {
        let url = GIT_WINDOWS_URL;
        let file_name = "git-portable.exe";
        let download_path = install_dir.join(file_name);

        download_file(url, &download_path).await?;

        // PortableGit is self-extracting
        std::process::Command::new(&download_path)
            .arg("-o")
            .arg(&git_dir)
            .arg("-y")
            .status()?;

        // Add to PATH
        add_to_system_path(&git_dir.join("bin"))?;

        println!("Git installed to: {:?}", git_dir);
        Ok(git_dir)
    }

    #[cfg(not(target_os = "windows"))]
    {
        install_git_unix().await
    }
}

async fn download_file(url: &str, dest_path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    println!("Downloading from: {}", url);
    println!("Saving to: {:?}", dest_path);

    // Create parent directory if it doesn't exist
    if let Some(parent) = dest_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let response = reqwest::get(url).await?;
    let mut file = fs::File::create(dest_path)?;
    let content = response.bytes().await?;
    file.write_all(&content)?;

    println!("Download completed: {:?}", dest_path);
    Ok(())
}

fn extract_zip(zip_path: &Path, extract_to: &Path) -> Result<(), Box<dyn std::error::Error>> {
    println!("Extracting ZIP: {:?} to {:?}", zip_path, extract_to);

    fs::create_dir_all(extract_to)?;

    let file = fs::File::open(zip_path)?;
    let mut archive = zip::ZipArchive::new(file)?;

    for i in 0..archive.len() {
        let mut file = archive.by_index(i)?;
        let outpath = match file.enclosed_name() {
            Some(path) => extract_to.join(path),
            None => continue,
        };

        if (file.name()).ends_with('/') {
            fs::create_dir_all(&outpath)?;
        } else {
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    fs::create_dir_all(p)?;
                }
            }
            let mut outfile = fs::File::create(&outpath)?;
            std::io::copy(&mut file, &mut outfile)?;
        }
    }

    println!("Extraction completed");
    Ok(())
}

fn extract_archive(archive_path: &Path, extract_to: &Path) -> Result<(), Box<dyn std::error::Error>> {
    println!("Extracting archive: {:?} to {:?}", archive_path, extract_to);

    fs::create_dir_all(extract_to)?;

    // For now, assume it's a tar.gz and use system tar if available
    #[cfg(target_os = "windows")]
    {
        // Windows 10+ has built-in tar
        let status = std::process::Command::new("tar")
            .args(["-xzf", archive_path.to_str().unwrap()])
            .args(["-C", extract_to.to_str().unwrap()])
            .status();

        match status {
            Ok(status) if status.success() => {
                println!("Archive extracted successfully");
                Ok(())
            }
            _ => {
                // Fallback: try to extract manually or use 7zip if available
                Err("Failed to extract archive".into())
            }
        }
    }

    #[cfg(not(target_os = "windows"))]
    {
        let status = std::process::Command::new("tar")
            .args(["-xzf", archive_path.to_str().unwrap()])
            .args(["-C", extract_to.to_str().unwrap()])
            .status()?;

        if status.success() {
            println!("Archive extracted successfully");
            Ok(())
        } else {
            Err("Failed to extract archive".into())
        }
    }
}

fn get_install_directory() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let home = dirs::home_dir().ok_or("Unable to find home directory")?;
    let install_dir = home.join("claude-proxy");
    fs::create_dir_all(&install_dir)?;
    Ok(install_dir)
}

fn add_to_system_path(path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    println!("Adding to PATH: {:?}", path);

    #[cfg(target_os = "windows")]
    {
        // CRITICAL: Use the safe add_to_path function from installer.rs to avoid truncation
        // Never use setx directly on PATH as it truncates at 1024 characters
        crate::installer::add_to_path(path)?;
    }

    #[cfg(not(target_os = "windows"))]
    {
        // Add to shell profile
        let home = dirs::home_dir().ok_or("Unable to find home directory")?;
        let profile_path = home.join(".bashrc");

        let export_line = format!("export PATH=\"$PATH:{}\"\n", path.display());

        std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(profile_path)?
            .write_all(export_line.as_bytes())?;
    }

    Ok(())
}

#[cfg(not(target_os = "windows"))]
async fn install_python_unix() -> Result<PathBuf, Box<dyn std::error::Error>> {
    // Try different package managers
    let commands = [
        ("apt", vec!["sudo", "apt", "update", "&&", "sudo", "apt", "install", "-y", "python3", "python3-pip"]),
        ("yum", vec!["sudo", "yum", "install", "-y", "python3", "python3-pip"]),
        ("brew", vec!["brew", "install", "python3"]),
    ];

    for (manager, cmd) in &commands {
        if which::which(manager).is_ok() {
            let status = std::process::Command::new("sh")
                .arg("-c")
                .arg(&cmd.join(" "))
                .status()?;

            if status.success() {
                println!("Python installed via {}", manager);
                return Ok(PathBuf::from("/usr/bin/python3"));
            }
        }
    }

    Err("Failed to install Python via package manager".into())
}

#[cfg(not(target_os = "windows"))]
async fn install_nodejs_unix() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let commands = [
        ("apt", "sudo apt update && sudo apt install -y nodejs npm"),
        ("yum", "sudo yum install -y nodejs npm"),
        ("brew", "brew install node"),
    ];

    for (manager, cmd) in &commands {
        if which::which(manager).is_ok() {
            let status = std::process::Command::new("sh")
                .arg("-c")
                .arg(cmd)
                .status()?;

            if status.success() {
                println!("Node.js installed via {}", manager);
                return Ok(PathBuf::from("/usr/bin/node"));
            }
        }
    }

    Err("Failed to install Node.js via package manager".into())
}

#[cfg(not(target_os = "windows"))]
async fn install_git_unix() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let commands = [
        ("apt", "sudo apt install -y git"),
        ("yum", "sudo yum install -y git"),
        ("brew", "brew install git"),
    ];

    for (manager, cmd) in &commands {
        if which::which(manager).is_ok() {
            let status = std::process::Command::new("sh")
                .arg("-c")
                .arg(cmd)
                .status()?;

            if status.success() {
                println!("Git installed via {}", manager);
                return Ok(PathBuf::from("/usr/bin/git"));
            }
        }
    }

    Err("Failed to install Git via package manager".into())
}