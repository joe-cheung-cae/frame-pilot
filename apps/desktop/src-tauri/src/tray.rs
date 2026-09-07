//! Optional system tray (D3.06 / S9.06). Create failure is non-fatal.

use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

use tauri::menu::{MenuBuilder, MenuEvent, MenuItemBuilder};
use tauri::tray::{MouseButton, MouseButtonState, TrayIcon, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Manager, Runtime};

use crate::sidecar::{find_active_job, ActiveJobRef, SidecarState};

pub const TRAY_SHOW_ID: &str = "tray-show";
pub const TRAY_QUIT_ID: &str = "tray-quit";
pub const TRAY_SHOW_LABEL: &str = "Show";
pub const TRAY_QUIT_LABEL: &str = "Quit";
pub const IDLE_TOOLTIP: &str = "No active job";

pub const TRAY_POLL_ACTIVE_MS: u64 = 1000;
pub const TRAY_POLL_IDLE_MS: u64 = 5000;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TrayAction {
    Show,
    Quit,
}

pub fn tray_menu_items() -> &'static [(&'static str, &'static str)] {
    &[
        (TRAY_SHOW_ID, TRAY_SHOW_LABEL),
        (TRAY_QUIT_ID, TRAY_QUIT_LABEL),
    ]
}

pub fn tray_action_from_menu_id(id: &str) -> Option<TrayAction> {
    match id {
        TRAY_SHOW_ID => Some(TrayAction::Show),
        TRAY_QUIT_ID => Some(TrayAction::Quit),
        _ => None,
    }
}

pub fn clamp_progress_percent(value: f64) -> i32 {
    value.round().clamp(0.0, 100.0) as i32
}

pub fn job_step_label(current_step: &str, status: &str) -> String {
    let trimmed = current_step.trim();
    if !trimmed.is_empty() {
        return trimmed.to_string();
    }
    if status == "queued" {
        "Queued".to_string()
    } else {
        "Running".to_string()
    }
}

pub fn job_type_label(job_type: &str) -> String {
    match job_type {
        "import" => "Import".to_string(),
        "processing" => "Grouping and ranking".to_string(),
        "export" => "Export".to_string(),
        "" => "Job".to_string(),
        other => {
            let mut chars = other.chars();
            match chars.next() {
                Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                None => "Job".to_string(),
            }
        }
    }
}

pub fn job_tooltip(job: Option<&ActiveJobRef>) -> String {
    let Some(job) = job else {
        return IDLE_TOOLTIP.to_string();
    };
    format!(
        "{} · {} · {}%",
        job_type_label(&job.job_type),
        job.current_step,
        job.progress_percent
    )
}

pub fn tray_poll_interval_ms(job_active: bool) -> u64 {
    if job_active {
        TRAY_POLL_ACTIVE_MS
    } else {
        TRAY_POLL_IDLE_MS
    }
}

pub fn is_primary_tray_click(button_is_left: bool, released: bool) -> bool {
    button_is_left && released
}

pub fn show_main_window<R: Runtime>(app: &AppHandle<R>) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

pub fn handle_tray_menu_event<R: Runtime>(app: &AppHandle<R>, event: &MenuEvent) {
    match tray_action_from_menu_id(event.id().0.as_str()) {
        Some(TrayAction::Show) => show_main_window(app),
        Some(TrayAction::Quit) => {
            // Same path as File → Quit: ExitRequested intercepts this and
            // runs handle_close_requested (do not skip the running-job dialog).
            app.exit(0);
        }
        None => {}
    }
}

fn is_primary_tray_icon_event(event: &TrayIconEvent) -> bool {
    matches!(
        event,
        TrayIconEvent::Click {
            button: MouseButton::Left,
            button_state: MouseButtonState::Up,
            ..
        }
    ) && is_primary_tray_click(true, true)
}

pub fn install_tray<R: Runtime>(
    app: &AppHandle<R>,
    port: u16,
    state: Arc<SidecarState>,
) -> tauri::Result<()> {
    let show = MenuItemBuilder::with_id(TRAY_SHOW_ID, TRAY_SHOW_LABEL).build(app)?;
    let quit = MenuItemBuilder::with_id(TRAY_QUIT_ID, TRAY_QUIT_LABEL).build(app)?;
    let menu = MenuBuilder::new(app).item(&show).item(&quit).build()?;

    let mut builder = TrayIconBuilder::with_id("framepilot-tray")
        .menu(&menu)
        .tooltip(IDLE_TOOLTIP)
        .title(IDLE_TOOLTIP)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| handle_tray_menu_event(app, &event))
        .on_tray_icon_event(|tray, event| {
            if is_primary_tray_icon_event(&event) {
                show_main_window(tray.app_handle());
            }
        });
    if let Some(icon) = app.default_window_icon() {
        builder = builder.icon(icon.clone());
    }

    let tray = builder.build(app)?;
    let poll_tray = tray.clone();
    thread::spawn(move || poll_tray_progress(poll_tray, port, state));
    app.manage(tray);
    Ok(())
}

fn poll_tray_progress<R: Runtime>(tray: TrayIcon<R>, port: u16, state: Arc<SidecarState>) {
    let mut last = String::new();
    while !state.is_shutdown() {
        let job = find_active_job(port);
        let tooltip = job_tooltip(job.as_ref());
        if tooltip != last {
            let _ = tray.set_tooltip(Some(tooltip.as_str()));
            let _ = tray.set_title(Some(tooltip.as_str()));
            last = tooltip;
        }
        let deadline = Instant::now() + Duration::from_millis(tray_poll_interval_ms(job.is_some()));
        while Instant::now() < deadline {
            if state.is_shutdown() {
                return;
            }
            thread::sleep(Duration::from_millis(100));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sidecar::ActiveJobRef;

    fn job(
        job_type: &str,
        status: &str,
        current_step: &str,
        progress_percent: f64,
    ) -> ActiveJobRef {
        ActiveJobRef {
            project_id: "p".into(),
            job_id: "j".into(),
            job_type: job_type.into(),
            status: status.into(),
            progress_percent: clamp_progress_percent(progress_percent),
            current_step: job_step_label(current_step, status),
        }
    }

    #[test]
    fn tray_menu_is_show_and_quit_only() {
        assert_eq!(
            tray_menu_items(),
            &[
                (TRAY_SHOW_ID, TRAY_SHOW_LABEL),
                (TRAY_QUIT_ID, TRAY_QUIT_LABEL)
            ]
        );
        assert_eq!(TRAY_SHOW_ID, "tray-show");
        assert_eq!(TRAY_QUIT_ID, "tray-quit");
        assert_eq!(tray_action_from_menu_id("tray-show"), Some(TrayAction::Show));
        assert_eq!(tray_action_from_menu_id("tray-quit"), Some(TrayAction::Quit));
        assert_eq!(tray_action_from_menu_id("quit"), None);
        assert_eq!(tray_action_from_menu_id("import"), None);
    }

    #[test]
    fn tray_tooltip_idle_is_no_active_job() {
        assert_eq!(job_tooltip(None), "No active job");
        assert_eq!(IDLE_TOOLTIP, "No active job");
    }

    #[test]
    fn tray_tooltip_formats_processing_progress() {
        assert_eq!(clamp_progress_percent(42.4), 42);
        assert_eq!(
            job_tooltip(Some(&job(
                "processing",
                "running",
                "Building groups",
                42.4
            ))),
            "Grouping and ranking · Building groups · 42%"
        );
    }

    #[test]
    fn tray_tooltip_formats_import_empty_step_and_clamps_percent() {
        assert_eq!(clamp_progress_percent(130.0), 100);
        assert_eq!(job_step_label("", "running"), "Running");
        assert_eq!(job_step_label("   ", "queued"), "Queued");
        assert_eq!(
            job_tooltip(Some(&job("import", "running", "", 130.0))),
            "Import · Running · 100%"
        );
    }

    #[test]
    fn tray_tooltip_formats_export_progress() {
        assert_eq!(
            job_tooltip(Some(&job("export", "queued", "Writing zip", 10.0))),
            "Export · Writing zip · 10%"
        );
    }

    #[test]
    fn tray_poll_interval_mirrors_jobs_refetch() {
        assert_eq!(tray_poll_interval_ms(true), 1000);
        assert_eq!(tray_poll_interval_ms(false), 5000);
    }

    #[test]
    fn primary_left_click_release_shows_window() {
        assert!(is_primary_tray_click(true, true));
        assert!(!is_primary_tray_click(true, false));
        assert!(!is_primary_tray_click(false, true));
    }

    #[test]
    fn default_capabilities_have_no_fs_or_shell() {
        let text = include_str!("../capabilities/default.json");
        assert!(
            !text.contains("fs:"),
            "default capabilities must not add fs: permissions: {text}"
        );
        assert!(
            !text.contains("shell:"),
            "default capabilities must not add shell: permissions: {text}"
        );
        assert!(
            text.contains("opener:allow-reveal-item-in-dir"),
            "keep reveal-scoped opener"
        );
        assert!(
            !text.contains("opener:default"),
            "must not grant opener:default"
        );
    }
}
