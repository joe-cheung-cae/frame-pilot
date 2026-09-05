//! OS app-support data directory. Policy lives in Rust only.

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use crate::sidecar::repo_root;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OsKind {
    MacOs,
    Windows,
    Linux,
}

#[derive(Debug, Clone, Copy)]
pub struct DataDirContext<'a> {
    pub packaged: bool,
    pub os: OsKind,
    pub home: &'a Path,
    pub appdata: Option<&'a Path>,
    pub repo_root: &'a Path,
    pub override_dir: Option<&'a Path>,
}

pub fn current_os() -> OsKind {
    if cfg!(target_os = "macos") {
        OsKind::MacOs
    } else if cfg!(target_os = "windows") {
        OsKind::Windows
    } else {
        OsKind::Linux
    }
}

/// Packaged defaults from locked decision 7.
pub fn packaged_app_support_dir(os: OsKind, home: &Path, appdata: Option<&Path>) -> PathBuf {
    match os {
        OsKind::MacOs => home.join("Library/Application Support/FramePilot"),
        OsKind::Windows => appdata
            .map(Path::to_path_buf)
            .unwrap_or_else(|| home.join("AppData").join("Roaming"))
            .join("FramePilot"),
        OsKind::Linux => home.join(".local/share/FramePilot"),
    }
}

pub const POINTER_FILENAME: &str = "data_dir.json";

pub fn default_data_dir(ctx: DataDirContext<'_>) -> PathBuf {
    if ctx.packaged {
        packaged_app_support_dir(ctx.os, ctx.home, ctx.appdata)
    } else {
        ctx.repo_root.join(".framepilot-desktop-dev")
    }
}

pub fn data_dir_pointer_path(anchor: &Path) -> PathBuf {
    anchor.join(POINTER_FILENAME)
}

pub fn read_data_dir_pointer(anchor: &Path) -> Option<PathBuf> {
    let raw = fs::read_to_string(data_dir_pointer_path(anchor)).ok()?;
    let value: serde_json::Value = serde_json::from_str(&raw).ok()?;
    let path = PathBuf::from(value.get("data_dir")?.as_str()?);
    path.is_absolute().then_some(path)
}

pub fn write_data_dir_pointer(anchor: &Path, data_dir: &Path) -> io::Result<()> {
    if !data_dir.is_absolute() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "data dir must be absolute",
        ));
    }
    fs::create_dir_all(anchor)?;
    let payload = serde_json::json!({ "data_dir": data_dir.to_string_lossy() });
    let tmp = anchor.join(format!("{POINTER_FILENAME}.tmp"));
    let pointer = data_dir_pointer_path(anchor);
    fs::write(&tmp, format!("{payload}\n"))?;
    let _ = fs::remove_file(&pointer);
    fs::rename(&tmp, pointer)?;
    Ok(())
}

pub fn resolve_data_dir(ctx: DataDirContext<'_>) -> PathBuf {
    if let Some(override_dir) = ctx.override_dir {
        if override_dir.is_absolute() {
            return override_dir.to_path_buf();
        }
    }
    let default = default_data_dir(ctx);
    if let Some(pointer) = read_data_dir_pointer(&default) {
        return pointer;
    }
    default
}

pub fn default_anchor_dir(packaged: bool) -> io::Result<PathBuf> {
    let home = home_dir().ok_or_else(|| {
        io::Error::new(io::ErrorKind::NotFound, "home directory is required")
    })?;
    let appdata = std::env::var_os("APPDATA").map(PathBuf::from);
    let root = repo_root();
    Ok(default_data_dir(DataDirContext {
        packaged,
        os: current_os(),
        home: &home,
        appdata: appdata.as_deref(),
        repo_root: &root,
        override_dir: None,
    }))
}

pub fn ensure_data_dir(path: &Path) -> io::Result<()> {
    fs::create_dir_all(path)?;
    fs::create_dir_all(path.join("logs"))?;
    Ok(())
}

fn home_dir() -> Option<PathBuf> {
    std::env::var_os("HOME")
        .or_else(|| std::env::var_os("USERPROFILE"))
        .map(PathBuf::from)
}

/// Runtime data dir. Packaged uses OS app-support; dev uses `.framepilot-desktop-dev`.
pub fn resolve_runtime_data_dir(packaged: bool) -> io::Result<PathBuf> {
    let home = home_dir().ok_or_else(|| {
        io::Error::new(io::ErrorKind::NotFound, "home directory is required")
    })?;
    let appdata = std::env::var_os("APPDATA").map(PathBuf::from);
    let override_dir = std::env::var_os("FRAMEPILOT_DATA_DIR").map(PathBuf::from);
    let root = repo_root();
    let path = resolve_data_dir(DataDirContext {
        packaged,
        os: current_os(),
        home: &home,
        appdata: appdata.as_deref(),
        repo_root: &root,
        override_dir: override_dir.as_deref(),
    });
    if !path.is_absolute() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "data dir must be absolute",
        ));
    }
    if packaged && path.file_name().and_then(|name| name.to_str()) == Some(".framepilot-data") {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "packaged data dir must not be CWD-relative .framepilot-data",
        ));
    }
    ensure_data_dir(&path)?;
    Ok(path)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn packaged_prefixes_match_locked_os_app_support_dirs() {
        let cases = [
            (
                OsKind::MacOs,
                Path::new("/Users/alex"),
                None,
                PathBuf::from("/Users/alex/Library/Application Support/FramePilot"),
            ),
            (
                OsKind::Windows,
                Path::new(r"C:\Users\alex"),
                Some(Path::new(r"C:\Users\alex\AppData\Roaming")),
                Path::new(r"C:\Users\alex\AppData\Roaming").join("FramePilot"),
            ),
            (
                OsKind::Linux,
                Path::new("/home/alex"),
                None,
                PathBuf::from("/home/alex/.local/share/FramePilot"),
            ),
        ];

        for (os, home, appdata, expected) in cases {
            let path = packaged_app_support_dir(os, home, appdata);
            assert_eq!(path, expected, "os={os:?}");
            assert_ne!(path.file_name().and_then(|n| n.to_str()), Some(".framepilot-data"));
        }
    }

    #[test]
    fn windows_prefix_falls_back_to_roaming_appdata() {
        let home = Path::new(r"C:\Users\alex");
        let path = packaged_app_support_dir(OsKind::Windows, home, None);
        assert_eq!(
            path,
            home.join("AppData").join("Roaming").join("FramePilot")
        );
    }

    #[test]
    fn packaged_path_is_never_cwd_framepilot_data() {
        let cwd = Path::new("/repo");
        let home = Path::new("/Users/alex");
        for os in [OsKind::MacOs, OsKind::Windows, OsKind::Linux] {
            let path = resolve_data_dir(DataDirContext {
                packaged: true,
                os,
                home,
                appdata: Some(Path::new(r"C:\Users\alex\AppData\Roaming")),
                repo_root: cwd,
                override_dir: None,
            });
            assert_ne!(path, cwd.join(".framepilot-data"), "os={os:?}");
            assert!(
                !path.ends_with(".framepilot-data"),
                "packaged path {path:?} must not be CWD .framepilot-data"
            );
            match os {
                OsKind::MacOs => {
                    assert!(path.ends_with("Library/Application Support/FramePilot"));
                }
                OsKind::Windows => {
                    assert_eq!(
                        path,
                        Path::new(r"C:\Users\alex\AppData\Roaming").join("FramePilot")
                    );
                }
                OsKind::Linux => {
                    assert!(path.ends_with(".local/share/FramePilot"));
                }
            }
        }
    }

    #[test]
    fn dev_path_uses_framepilot_desktop_dev() {
        let repo = Path::new("/repo");
        let path = resolve_data_dir(DataDirContext {
            packaged: false,
            os: OsKind::MacOs,
            home: Path::new("/Users/alex"),
            appdata: None,
            repo_root: repo,
            override_dir: None,
        });
        assert_eq!(path, repo.join(".framepilot-desktop-dev"));
        assert!(path.is_absolute());
        assert_ne!(path, repo.join(".framepilot-data"));
    }

    #[test]
    fn absolute_override_wins() {
        let override_dir = Path::new("/abs/override");
        let path = resolve_data_dir(DataDirContext {
            packaged: true,
            os: OsKind::Linux,
            home: Path::new("/home/alex"),
            appdata: None,
            repo_root: Path::new("/repo"),
            override_dir: Some(override_dir),
        });
        assert_eq!(path, override_dir);
    }

    fn unique_temp_dir(label: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "framepilot-data-dir-pointer-{}-{}-{}",
            label,
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("time")
                .as_nanos()
        ));
        fs::create_dir_all(&dir).expect("temp dir");
        dir
    }

    #[test]
    fn pointer_file_overrides_default_dev_dir() {
        let root = unique_temp_dir("pointer");
        let repo = root.join("repo");
        let default_dir = repo.join(".framepilot-desktop-dev");
        let moved = root.join("moved-data");
        fs::create_dir_all(&default_dir).expect("default dir");
        write_data_dir_pointer(&default_dir, &moved).expect("write pointer");
        let path = resolve_data_dir(DataDirContext {
            packaged: false,
            os: OsKind::Linux,
            home: Path::new("/home/alex"),
            appdata: None,
            repo_root: &repo,
            override_dir: None,
        });
        assert_eq!(path, moved);
        let _ = fs::remove_dir_all(&root);
    }

    #[test]
    fn env_override_still_wins_over_pointer_file() {
        let root = unique_temp_dir("env-wins");
        let repo = root.join("repo");
        let default_dir = repo.join(".framepilot-desktop-dev");
        let moved = root.join("moved-data");
        let env_dir = Path::new("/abs/env-override");
        fs::create_dir_all(&default_dir).expect("default dir");
        write_data_dir_pointer(&default_dir, &moved).expect("write pointer");
        let path = resolve_data_dir(DataDirContext {
            packaged: false,
            os: OsKind::Linux,
            home: Path::new("/home/alex"),
            appdata: None,
            repo_root: &repo,
            override_dir: Some(env_dir),
        });
        assert_eq!(path, env_dir);
        let _ = fs::remove_dir_all(&root);
    }

    #[test]
    fn lib_registers_apply_data_directory_without_fs_or_shell() {
        let lib = include_str!("lib.rs");
        assert!(lib.contains("apply_data_directory"));
        assert!(lib.contains("write_data_dir_pointer"));
        let capabilities = include_str!("../capabilities/default.json");
        assert!(
            !capabilities.contains("fs:"),
            "default capabilities must not add fs: permissions"
        );
        assert!(
            !capabilities.contains("shell:"),
            "default capabilities must not add shell: permissions"
        );
    }

    #[test]
    fn ensure_data_dir_creates_logs() {
        let dir = std::env::temp_dir().join(format!(
            "framepilot-data-dir-test-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("time")
                .as_nanos()
        ));
        ensure_data_dir(&dir).expect("create data dir");
        assert!(dir.is_dir());
        assert!(dir.join("logs").is_dir());
        let _ = fs::remove_dir_all(&dir);
    }
}
