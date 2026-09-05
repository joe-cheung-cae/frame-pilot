//! Native application menu for the FramePilot desktop shell.

use std::path::PathBuf;

use tauri::menu::{AboutMetadata, Menu, MenuBuilder, MenuEvent, MenuItemBuilder, SubmenuBuilder};
use tauri::{AppHandle, Manager, Runtime, WebviewWindow};
use tauri_plugin_opener::OpenerExt;

pub const MENU_EVENT: &str = "framepilot-menu";

pub const NEW_ACCELERATOR: &str = "CmdOrCtrl+N";
pub const CLOSE_ACCELERATOR: &str = "CmdOrCtrl+W";
pub const QUIT_ACCELERATOR: &str = "CmdOrCtrl+Q";

pub const CUSTOM_ACCELERATORS: &[&str] = &[NEW_ACCELERATOR, CLOSE_ACCELERATOR, QUIT_ACCELERATOR];

pub struct DesktopPaths {
    pub data_dir: PathBuf,
}

fn about_metadata() -> AboutMetadata<'static> {
    AboutMetadata {
        name: Some("FramePilot".into()),
        version: Some(env!("CARGO_PKG_VERSION").into()),
        ..Default::default()
    }
}

fn emit_menu_command<R: Runtime>(app: &AppHandle<R>, command: &str) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };
    let payload = serde_json::to_string(command).unwrap_or_else(|_| "\"\"".into());
    let script = format!(
        "window.dispatchEvent(new CustomEvent('{MENU_EVENT}', {{ detail: {payload} }}));"
    );
    let _ = window.eval(&script);
}

fn toggle_fullscreen<R: Runtime>(window: &WebviewWindow<R>) {
    let current = window.is_fullscreen().unwrap_or(false);
    let _ = window.set_fullscreen(!current);
}

pub fn build_app_menu<R: Runtime, M: Manager<R>>(manager: &M) -> tauri::Result<Menu<R>> {
    let file = SubmenuBuilder::new(manager, "File")
        .item(
            &MenuItemBuilder::with_id("new", "New")
                .accelerator(NEW_ACCELERATOR)
                .build(manager)?,
        )
        .item(&MenuItemBuilder::with_id("open-data-folder", "Open data folder").build(manager)?)
        .item(&MenuItemBuilder::with_id("import", "Import").build(manager)?)
        .item(&MenuItemBuilder::with_id("export", "Export").build(manager)?)
        .separator()
        .item(
            &MenuItemBuilder::with_id("close", "Close")
                .accelerator(CLOSE_ACCELERATOR)
                .build(manager)?,
        )
        .item(
            &MenuItemBuilder::with_id("quit", "Quit")
                .accelerator(QUIT_ACCELERATOR)
                .build(manager)?,
        )
        .build()?;

    let edit = SubmenuBuilder::new(manager, "Edit")
        .undo()
        .redo()
        .separator()
        .cut()
        .copy()
        .paste()
        .select_all()
        .build()?;

    let view = SubmenuBuilder::new(manager, "View")
        .item(&MenuItemBuilder::with_id("fullscreen", "Fullscreen").build(manager)?)
        .item(&MenuItemBuilder::with_id("detached-preview", "Detached preview").build(manager)?)
        .build()?;

    let project = SubmenuBuilder::new(manager, "Project")
        .item(&MenuItemBuilder::with_id("process", "Process").build(manager)?)
        .item(&MenuItemBuilder::with_id("cull", "Culling").build(manager)?)
        .build()?;

    let help = SubmenuBuilder::new(manager, "Help")
        .item(&MenuItemBuilder::with_id("shortcuts", "Shortcuts").build(manager)?)
        .about_with_text("About", Some(about_metadata()))
        .build()?;

    #[cfg(target_os = "macos")]
    {
        let app_menu = SubmenuBuilder::new(manager, "FramePilot")
            .about(Some(about_metadata()))
            .separator()
            .hide()
            .hide_others()
            .show_all()
            .separator()
            .quit()
            .build()?;
        return MenuBuilder::new(manager)
            .item(&app_menu)
            .item(&file)
            .item(&edit)
            .item(&view)
            .item(&project)
            .item(&help)
            .build();
    }

    #[cfg(not(target_os = "macos"))]
    MenuBuilder::new(manager)
        .item(&file)
        .item(&edit)
        .item(&view)
        .item(&project)
        .item(&help)
        .build()
}

pub fn handle_menu_event<R: Runtime>(app: &AppHandle<R>, event: MenuEvent) {
    match event.id().0.as_str() {
        "new" | "import" | "export" | "process" | "cull" | "shortcuts" => {
            emit_menu_command(app, event.id().0.as_str());
        }
        "open-data-folder" => {
            if let Some(paths) = app.try_state::<DesktopPaths>() {
                let _ = app.opener().reveal_item_in_dir(&paths.data_dir);
            }
        }
        "close" => {
            let focused = crate::preview::focused_webview_label(app);
            if crate::preview::file_close_targets_app_quit(focused.as_deref()) {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.close();
                }
            } else if let Err(err) = crate::preview::close_preview_window(app) {
                eprintln!("FramePilot could not close detached preview: {err}");
            }
        }
        "quit" => {
            app.exit(0);
        }
        "fullscreen" => {
            if let Some(window) = app.get_webview_window("main") {
                toggle_fullscreen(&window);
            }
        }
        "detached-preview" => {
            if let Err(err) = crate::preview::toggle_preview_window(app) {
                eprintln!("FramePilot detached preview is unavailable: {err}");
            }
        }
        _ => {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const RESERVED_BARE_KEYS: &[&str] = &[
        "P", "M", "X", "U", "1", "2", "3", "4", "5", "0", "Space", "Z", "C", "G", "F", "E", "p",
        "m", "x", "u", "z", "c", "g", "f", "e", " ",
    ];

    #[test]
    fn custom_accelerators_are_not_reserved_bare_culling_keys() {
        for accel in CUSTOM_ACCELERATORS {
            assert!(
                accel.contains("Cmd") || accel.contains("Ctrl") || accel.contains("Alt"),
                "accelerator {accel} must be a modifier chord"
            );
            assert!(
                !RESERVED_BARE_KEYS.iter().any(|key| accel == key),
                "accelerator {accel} collides with a reserved culling key"
            );
        }
    }

    #[test]
    fn about_version_comes_from_package_metadata() {
        assert_eq!(env!("CARGO_PKG_VERSION"), "2.1.0-desktop");
    }

    #[test]
    fn detached_preview_menu_id_has_no_accelerator() {
        assert_eq!(crate::preview::DETACHED_PREVIEW_MENU_ID, "detached-preview");
        assert!(crate::preview::DETACHED_PREVIEW_ACCELERATOR.is_none());
        assert!(!CUSTOM_ACCELERATORS.iter().any(|accel| accel.contains("detached")));
    }
}
