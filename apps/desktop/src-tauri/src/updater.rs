//! Optional check for updates (S9.10 / #167). Menu click only; no launch-time network.

use std::error::Error;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

use serde::Deserialize;
use tauri::{AppHandle, Runtime};
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

pub const CHECK_FOR_UPDATES_MENU_ID: &str = "check-for-updates";
pub const CHECK_FOR_UPDATES_LABEL: &str = "Check for updates";
pub const CHECK_FOR_UPDATES_ACCELERATOR: Option<&str> = None;
pub const RELEASES_LATEST_URL: &str =
    "https://api.github.com/repos/joe-cheung-cae/frame-pilot/releases/latest";
pub const REQUEST_TIMEOUT: Duration = Duration::from_secs(10);
pub const LOCAL_VERSION: &str = env!("CARGO_PKG_VERSION");

static CHECK_IN_FLIGHT: AtomicBool = AtomicBool::new(false);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FetchResponse {
    pub status: u16,
    pub body: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FetchError {
    Timeout,
    Transport(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CheckOutcome {
    MissingManifest,
    UpToDate {
        current: String,
    },
    UpdateAvailable {
        current: String,
        latest: String,
        html_url: Option<String>,
    },
    NetworkError {
        message: String,
    },
}

#[derive(Debug, Deserialize)]
struct GithubRelease {
    tag_name: Option<String>,
    html_url: Option<String>,
}

pub fn user_agent() -> String {
    format!("FramePilot/{LOCAL_VERSION}")
}

pub fn try_begin_check_flag(flag: &AtomicBool) -> bool {
    flag.compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_ok()
}

pub fn finish_check_flag(flag: &AtomicBool) {
    flag.store(false, Ordering::SeqCst);
}

pub fn try_begin_check() -> bool {
    try_begin_check_flag(&CHECK_IN_FLIGHT)
}

pub fn finish_check() {
    finish_check_flag(&CHECK_IN_FLIGHT);
}

pub fn normalize_core_version(raw: &str) -> Option<(u64, u64, u64)> {
    let trimmed = raw.trim();
    let without_v = trimmed
        .strip_prefix('v')
        .or_else(|| trimmed.strip_prefix('V'))
        .unwrap_or(trimmed);
    let core = without_v.split(['-', '+']).next().unwrap_or("");
    let mut parts = core.split('.');
    let major = parts.next()?.parse().ok()?;
    let minor = parts.next()?.parse().ok()?;
    let patch = parts.next()?.parse().ok()?;
    if parts.next().is_some() {
        return None;
    }
    Some((major, minor, patch))
}

pub fn interpret_fetch_result(
    result: Result<FetchResponse, FetchError>,
    local_version: &str,
) -> CheckOutcome {
    match result {
        Err(FetchError::Timeout) => CheckOutcome::NetworkError {
            message: "The update check timed out.".into(),
        },
        Err(FetchError::Transport(message)) => CheckOutcome::NetworkError { message },
        Ok(response) => interpret_http_response(response, local_version),
    }
}

fn interpret_http_response(response: FetchResponse, local_version: &str) -> CheckOutcome {
    match response.status {
        403 => CheckOutcome::NetworkError {
            message: "GitHub returned HTTP 403.".into(),
        },
        429 => CheckOutcome::NetworkError {
            message: "GitHub returned HTTP 429.".into(),
        },
        500..=599 => CheckOutcome::NetworkError {
            message: format!("GitHub returned HTTP {}.", response.status),
        },
        200 => parse_manifest(&response.body, local_version),
        _ => CheckOutcome::MissingManifest,
    }
}

fn parse_manifest(body: &str, local_version: &str) -> CheckOutcome {
    if body.trim().is_empty() {
        return CheckOutcome::MissingManifest;
    }
    let Ok(release) = serde_json::from_str::<GithubRelease>(body) else {
        return CheckOutcome::MissingManifest;
    };
    let Some(tag_name) = release
        .tag_name
        .map(|tag| tag.trim().to_string())
        .filter(|tag| !tag.is_empty())
    else {
        return CheckOutcome::MissingManifest;
    };
    let Some(remote) = normalize_core_version(&tag_name) else {
        return CheckOutcome::MissingManifest;
    };
    let Some(local) = normalize_core_version(local_version) else {
        return CheckOutcome::MissingManifest;
    };
    if remote > local {
        CheckOutcome::UpdateAvailable {
            current: local_version.to_string(),
            latest: tag_name,
            html_url: release
                .html_url
                .map(|url| url.trim().to_string())
                .filter(|url| !url.is_empty()),
        }
    } else {
        CheckOutcome::UpToDate {
            current: local_version.to_string(),
        }
    }
}

pub fn dialog_message(outcome: &CheckOutcome) -> Option<String> {
    match outcome {
        CheckOutcome::MissingManifest => None,
        CheckOutcome::UpToDate { current } => {
            Some(format!("FramePilot {current} is up to date."))
        }
        CheckOutcome::UpdateAvailable {
            current,
            latest,
            html_url,
        } => {
            let mut message = format!(
                "A newer FramePilot release is available.\nCurrent: {current}\nLatest: {latest}"
            );
            if let Some(url) = html_url {
                message.push('\n');
                message.push_str(url);
            }
            Some(message)
        }
        CheckOutcome::NetworkError { message } => {
            Some(format!("Could not check for updates.\n{message}"))
        }
    }
}

pub fn check_latest_with_fetcher<F>(local_version: &str, fetch: F) -> CheckOutcome
where
    F: FnOnce() -> Result<FetchResponse, FetchError>,
{
    interpret_fetch_result(fetch(), local_version)
}

fn map_transport_error(err: ureq::Transport) -> FetchError {
    let message = err.to_string();
    let timed_out = err
        .source()
        .and_then(|source| source.downcast_ref::<std::io::Error>())
        .is_some_and(|io| io.kind() == std::io::ErrorKind::TimedOut)
        || message.to_ascii_lowercase().contains("timed out")
        || message.to_ascii_lowercase().contains("timeout");
    if timed_out {
        FetchError::Timeout
    } else {
        FetchError::Transport(message)
    }
}

fn read_response(status: u16, response: ureq::Response) -> Result<FetchResponse, FetchError> {
    let body = response.into_string().unwrap_or_default();
    Ok(FetchResponse { status, body })
}

fn fetch_latest_release() -> Result<FetchResponse, FetchError> {
    let agent = ureq::AgentBuilder::new()
        .timeout(REQUEST_TIMEOUT)
        .build();
    let request = agent
        .get(RELEASES_LATEST_URL)
        .set("User-Agent", &user_agent())
        .set("Accept", "application/vnd.github+json");
    match request.call() {
        Ok(response) => read_response(response.status(), response),
        Err(ureq::Error::Status(code, response)) => read_response(code, response),
        Err(ureq::Error::Transport(err)) => Err(map_transport_error(err)),
    }
}

pub fn check_latest_release(local_version: &str) -> CheckOutcome {
    check_latest_with_fetcher(local_version, fetch_latest_release)
}

fn show_check_outcome<R: Runtime>(app: &AppHandle<R>, outcome: &CheckOutcome) {
    let Some(message) = dialog_message(outcome) else {
        if matches!(outcome, CheckOutcome::MissingManifest) {
            eprintln!("FramePilot update check: release manifest missing");
        }
        return;
    };
    let kind = match outcome {
        CheckOutcome::NetworkError { .. } => MessageDialogKind::Warning,
        _ => MessageDialogKind::Info,
    };
    let _ = app
        .dialog()
        .message(message)
        .title(CHECK_FOR_UPDATES_LABEL)
        .kind(kind)
        .blocking_show();
}

pub fn request_check_for_updates<R: Runtime>(app: &AppHandle<R>) {
    if !try_begin_check() {
        return;
    }
    let app = app.clone();
    thread::spawn(move || {
        let outcome = check_latest_release(LOCAL_VERSION);
        show_check_outcome(&app, &outcome);
        finish_check();
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    const DESKTOP: &str = "2.1.0-desktop";

    fn ok_json(tag: &str, url: Option<&str>) -> FetchResponse {
        let html = match url {
            Some(url) => format!(r#", "html_url": "{url}""#),
            None => String::new(),
        };
        FetchResponse {
            status: 200,
            body: format!(r#"{{"tag_name": "{tag}"{html}}}"#),
        }
    }

    #[test]
    fn menu_id_has_no_accelerator_and_is_not_a_reserved_culling_key() {
        assert_eq!(CHECK_FOR_UPDATES_MENU_ID, "check-for-updates");
        assert_eq!(CHECK_FOR_UPDATES_LABEL, "Check for updates");
        assert!(CHECK_FOR_UPDATES_ACCELERATOR.is_none());
        let catalog = include_str!("menu.rs")
            .split("#[cfg(test)]")
            .next()
            .expect("menu catalog");
        let idx = catalog
            .find(r#"with_id("check-for-updates", "Check for updates")"#)
            .expect("Help menu must include check-for-updates");
        let slice = &catalog[idx..(idx + 180).min(catalog.len())];
        assert!(
            !slice.contains("accelerator"),
            "check-for-updates must have no accelerator: {slice}"
        );
        for key in [
            "P", "M", "X", "U", "1", "2", "3", "4", "5", "0", "Space", "Z", "C", "G", "F", "E",
        ] {
            assert_ne!(CHECK_FOR_UPDATES_MENU_ID, key);
        }
    }

    #[test]
    fn lib_setup_does_not_call_the_check() {
        let source = include_str!("lib.rs");
        let setup_idx = source
            .find(".setup(move |app|")
            .expect("lib.rs must have a setup closure");
        let after_setup = &source[setup_idx..];
        let setup_end = after_setup
            .find(".on_window_event")
            .unwrap_or(after_setup.len());
        let setup = &after_setup[..setup_end];
        assert!(
            !setup.contains("check_latest_release")
                && !setup.contains("request_check_for_updates")
                && !setup.contains("updater::"),
            "setup must not check for updates: {setup}"
        );
        assert!(
            !source.contains("tauri_plugin_updater"),
            "do not add tauri-plugin-updater"
        );
    }

    #[test]
    fn cargo_uses_ureq_not_updater_plugin() {
        let cargo = include_str!("../Cargo.toml");
        assert!(
            cargo.contains("ureq"),
            "Cargo.toml must depend on ureq for the Releases GET"
        );
        assert!(
            !cargo.contains("tauri-plugin-updater"),
            "do not add tauri-plugin-updater"
        );
        let conf = include_str!("../tauri.conf.json");
        assert!(
            !conf.contains("updater") && !conf.contains("createUpdaterArtifacts"),
            "tauri.conf.json must not enable the updater plugin"
        );
        assert!(
            conf.contains("connect-src 'self' http://127.0.0.1:* http://localhost:*"),
            "CSP connect-src must stay loopback-only"
        );
        assert!(!conf.contains("api.github.com"));
        let caps = include_str!("../capabilities/default.json");
        assert!(!caps.contains("fs:"));
        assert!(!caps.contains("shell:"));
        assert!(!caps.contains("opener:default"));
        assert!(!caps.contains("updater"));
        assert!(caps.contains("opener:allow-reveal-item-in-dir"));
        assert!(caps.contains("dialog:default"));
    }

    #[test]
    fn user_agent_uses_package_version() {
        assert_eq!(LOCAL_VERSION, DESKTOP);
        assert_eq!(user_agent(), format!("FramePilot/{DESKTOP}"));
        assert_eq!(
            RELEASES_LATEST_URL,
            "https://api.github.com/repos/joe-cheung-cae/frame-pilot/releases/latest"
        );
        assert_eq!(REQUEST_TIMEOUT, Duration::from_secs(10));
    }

    #[test]
    fn missing_manifest_is_non_fatal_noop() {
        let four_oh_four = interpret_fetch_result(
            Ok(FetchResponse {
                status: 404,
                body: r#"{"message":"Not Found"}"#.into(),
            }),
            DESKTOP,
        );
        assert_eq!(four_oh_four, CheckOutcome::MissingManifest);
        assert_eq!(dialog_message(&four_oh_four), None);

        let empty = interpret_fetch_result(
            Ok(FetchResponse {
                status: 200,
                body: String::new(),
            }),
            DESKTOP,
        );
        assert_eq!(empty, CheckOutcome::MissingManifest);
        assert_eq!(dialog_message(&empty), None);

        let no_tag = interpret_fetch_result(
            Ok(FetchResponse {
                status: 200,
                body: r#"{"html_url":"https://example.invalid"}"#.into(),
            }),
            DESKTOP,
        );
        assert_eq!(no_tag, CheckOutcome::MissingManifest);

        let bad_tag = interpret_fetch_result(Ok(ok_json("not-a-version", None)), DESKTOP);
        assert_eq!(bad_tag, CheckOutcome::MissingManifest);
    }

    #[test]
    fn newer_remote_core_is_available() {
        let outcome = interpret_fetch_result(
            Ok(ok_json(
                "v2.2.0",
                Some("https://github.com/joe-cheung-cae/frame-pilot/releases/tag/v2.2.0"),
            )),
            DESKTOP,
        );
        assert_eq!(
            outcome,
            CheckOutcome::UpdateAvailable {
                current: DESKTOP.into(),
                latest: "v2.2.0".into(),
                html_url: Some(
                    "https://github.com/joe-cheung-cae/frame-pilot/releases/tag/v2.2.0".into()
                ),
            }
        );
        let message = dialog_message(&outcome).expect("update dialog");
        assert!(message.contains(DESKTOP), "{message}");
        assert!(message.contains("v2.2.0"), "{message}");
        assert!(
            message.contains("https://github.com/joe-cheung-cae/frame-pilot/releases/tag/v2.2.0"),
            "{message}"
        );
    }

    #[test]
    fn older_or_equal_remote_core_is_current() {
        let older = interpret_fetch_result(Ok(ok_json("v2.0.0", None)), DESKTOP);
        assert_eq!(
            older,
            CheckOutcome::UpToDate {
                current: DESKTOP.into()
            }
        );
        let equal = interpret_fetch_result(Ok(ok_json("v2.1.0", None)), DESKTOP);
        assert_eq!(
            equal,
            CheckOutcome::UpToDate {
                current: DESKTOP.into()
            }
        );
        let message = dialog_message(&equal).expect("up to date dialog");
        assert!(message.contains(DESKTOP), "{message}");
    }

    #[test]
    fn timeout_and_forbidden_do_not_panic() {
        let timeout = interpret_fetch_result(Err(FetchError::Timeout), DESKTOP);
        match &timeout {
            CheckOutcome::NetworkError { message } => {
                assert!(!message.is_empty(), "timeout message");
            }
            other => panic!("timeout must be NetworkError, got {other:?}"),
        }
        assert!(dialog_message(&timeout).is_some());

        let forbidden = interpret_fetch_result(
            Ok(FetchResponse {
                status: 403,
                body: "rate limit".into(),
            }),
            DESKTOP,
        );
        match &forbidden {
            CheckOutcome::NetworkError { message } => {
                assert!(message.contains("403") || message.to_lowercase().contains("forbidden"));
            }
            other => panic!("403 must be NetworkError, got {other:?}"),
        }
        assert!(dialog_message(&forbidden).is_some());

        let server = interpret_fetch_result(
            Ok(FetchResponse {
                status: 502,
                body: "bad gateway".into(),
            }),
            DESKTOP,
        );
        assert!(matches!(server, CheckOutcome::NetworkError { .. }));
    }

    #[test]
    fn injected_fetcher_never_touches_live_github() {
        let outcome = check_latest_with_fetcher(DESKTOP, || {
            Ok(FetchResponse {
                status: 404,
                body: String::new(),
            })
        });
        assert_eq!(outcome, CheckOutcome::MissingManifest);
        assert!(!RELEASES_LATEST_URL.is_empty());
    }

    #[test]
    fn second_click_is_ignored_while_in_flight() {
        let flag = AtomicBool::new(false);
        assert!(try_begin_check_flag(&flag));
        assert!(!try_begin_check_flag(&flag));
        finish_check_flag(&flag);
        assert!(try_begin_check_flag(&flag));
    }

    #[test]
    fn normalize_strips_v_and_semver_suffix() {
        assert_eq!(normalize_core_version("v2.2.0"), Some((2, 2, 0)));
        assert_eq!(normalize_core_version("2.1.0-desktop"), Some((2, 1, 0)));
        assert_eq!(normalize_core_version("v2.1.0"), Some((2, 1, 0)));
        assert_eq!(normalize_core_version("v2.0.0"), Some((2, 0, 0)));
        assert_eq!(normalize_core_version("2.1.0+build"), Some((2, 1, 0)));
        assert_eq!(normalize_core_version(""), None);
        assert_eq!(normalize_core_version("latest"), None);
    }
}
