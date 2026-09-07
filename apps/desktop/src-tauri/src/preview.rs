//! Detached preview window (S9.07 / #166). Create failure is non-fatal.

use tauri::{AppHandle, Emitter, Manager, Runtime};

use crate::sidecar::initialization_script_for_window;

pub const PREVIEW_WINDOW_LABEL: &str = "preview";
pub const MAIN_WINDOW_LABEL: &str = "main";
pub const PREVIEW_WINDOW_TITLE: &str = "FramePilot Preview";
pub const DETACHED_PREVIEW_MENU_ID: &str = "detached-preview";
pub const DETACHED_PREVIEW_ACCELERATOR: Option<&str> = None;
pub const PREVIEW_OPENED_EVENT: &str = "framepilot-preview-opened";
pub const PREVIEW_CLOSED_EVENT: &str = "framepilot-preview-closed";

pub struct PreviewHost {
    pub port: u16,
}

pub fn window_close_targets_app_quit(label: &str) -> bool {
    label == MAIN_WINDOW_LABEL
}

pub fn window_destroyed_requests_sidecar_shutdown(label: &str) -> bool {
    window_close_targets_app_quit(label)
}

pub fn file_close_targets_app_quit(focused_webview_label: Option<&str>) -> bool {
    window_close_targets_app_quit(focused_webview_label.unwrap_or(MAIN_WINDOW_LABEL))
}

pub fn close_detached_preview_outcome(window_present: bool) -> Result<bool, String> {
    Ok(window_present)
}

pub fn focused_webview_label<R: Runtime>(app: &AppHandle<R>) -> Option<String> {
    let mut fallback: Option<String> = None;
    for (label, window) in app.webview_windows() {
        if !window.is_focused().unwrap_or(false) {
            continue;
        }
        if label == PREVIEW_WINDOW_LABEL {
            return Some(label);
        }
        fallback = Some(label);
    }
    fallback
}

pub fn emit_preview_opened<R: Runtime>(app: &AppHandle<R>) {
    let _ = app.emit(PREVIEW_OPENED_EVENT, ());
}

pub fn emit_preview_closed<R: Runtime>(app: &AppHandle<R>) {
    let _ = app.emit(PREVIEW_CLOSED_EVENT, ());
}

pub fn close_preview_window<R: Runtime>(app: &AppHandle<R>) -> Result<bool, String> {
    let Some(window) = app.get_webview_window(PREVIEW_WINDOW_LABEL) else {
        return close_detached_preview_outcome(false);
    };
    window.close().map_err(|err| err.to_string())?;
    close_detached_preview_outcome(true)
}

pub fn open_preview_window<R: Runtime>(app: &AppHandle<R>) -> Result<(), String> {
    if app.get_webview_window(PREVIEW_WINDOW_LABEL).is_some() {
        return Ok(());
    }
    let port = app
        .try_state::<PreviewHost>()
        .map(|host| host.port)
        .ok_or_else(|| "preview host is not configured".to_string())?;
    match tauri::WebviewWindowBuilder::new(
        app,
        PREVIEW_WINDOW_LABEL,
        tauri::WebviewUrl::App("index.html".into()),
    )
    .title(PREVIEW_WINDOW_TITLE)
    .inner_size(960.0, 720.0)
    .min_inner_size(480.0, 320.0)
    .resizable(true)
    .initialization_script(&initialization_script_for_window(port, PREVIEW_WINDOW_LABEL))
    .build()
    {
        Ok(_) => {
            emit_preview_opened(app);
            Ok(())
        }
        Err(err) => {
            eprintln!("FramePilot detached preview is unavailable: {err}");
            Err(err.to_string())
        }
    }
}

pub fn toggle_preview_window<R: Runtime>(app: &AppHandle<R>) -> Result<bool, String> {
    if app.get_webview_window(PREVIEW_WINDOW_LABEL).is_some() {
        close_preview_window(app)?;
        Ok(false)
    } else {
        open_preview_window(app)?;
        Ok(true)
    }
}

#[tauri::command]
pub fn toggle_detached_preview(app: AppHandle) -> Result<bool, String> {
    toggle_preview_window(&app)
}

#[tauri::command]
pub fn close_detached_preview(app: AppHandle) -> Result<bool, String> {
    close_preview_window(&app)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preview_window_label_is_preview() {
        assert_eq!(PREVIEW_WINDOW_LABEL, "preview");
        assert_eq!(PREVIEW_WINDOW_TITLE, "FramePilot Preview");
        assert_eq!(DETACHED_PREVIEW_MENU_ID, "detached-preview");
        assert!(DETACHED_PREVIEW_ACCELERATOR.is_none());
    }

    #[test]
    fn window_close_targets_app_quit_only_for_main() {
        assert!(window_close_targets_app_quit("main"));
        assert!(!window_close_targets_app_quit("preview"));
        assert!(!window_close_targets_app_quit("other"));
    }

    #[test]
    fn file_close_with_preview_focused_is_not_app_quit() {
        assert!(!file_close_targets_app_quit(Some("preview")));
        assert!(file_close_targets_app_quit(Some("main")));
        assert!(file_close_targets_app_quit(None));
    }

    #[test]
    fn destroyed_preview_does_not_request_sidecar_shutdown() {
        assert!(!window_destroyed_requests_sidecar_shutdown("preview"));
        assert!(window_destroyed_requests_sidecar_shutdown("main"));
    }

    #[test]
    fn missing_preview_window_close_is_ok_false() {
        assert_eq!(close_detached_preview_outcome(false), Ok(false));
        assert_eq!(close_detached_preview_outcome(true), Ok(true));
    }

    #[test]
    fn default_capabilities_include_preview_without_fs_or_shell() {
        let text = include_str!("../capabilities/default.json");
        assert!(
            text.contains("\"preview\""),
            "capabilities windows must include preview: {text}"
        );
        assert!(
            !text.contains("fs:"),
            "default capabilities must not add fs: permissions: {text}"
        );
        assert!(
            !text.contains("shell:"),
            "default capabilities must not add shell: permissions: {text}"
        );
        assert!(
            !text.contains("opener:default"),
            "must not grant opener:default"
        );
    }

    #[test]
    fn lib_gates_quit_and_registers_preview_commands() {
        let lib = include_str!("lib.rs");
        assert!(lib.contains("mod preview;"));
        assert!(lib.contains("invoke_handler"));
        assert!(lib.contains("toggle_detached_preview"));
        assert!(lib.contains("close_detached_preview"));
        assert!(lib.contains("with_denylist"));
        assert!(lib.contains("window_close_targets_app_quit"));
        assert!(lib.contains("window_destroyed_requests_sidecar_shutdown"));
    }

    #[test]
    fn menu_adds_detached_preview_without_accelerator() {
        let menu = include_str!("menu.rs");
        let idx = menu
            .find("detached-preview")
            .expect("View menu must include detached-preview");
        let slice = &menu[idx..idx.saturating_add(160).min(menu.len())];
        assert!(
            !slice.contains("accelerator"),
            "detached-preview must not steal a shortcut: {slice}"
        );
        assert!(menu.contains("file_close_targets_app_quit") || menu.contains("focused_webview_label"));
    }
}
