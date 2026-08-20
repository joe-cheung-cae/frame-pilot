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

pub fn resolve_data_dir(ctx: DataDirContext<'_>) -> PathBuf {
    if let Some(override_dir) = ctx.override_dir {
        if override_dir.is_absolute() {
            return override_dir.to_path_buf();
        }
    }
    if ctx.packaged {
        packaged_app_support_dir(ctx.os, ctx.home, ctx.appdata)
    } else {
        ctx.repo_root.join(".framepilot-desktop-dev")
    }
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
