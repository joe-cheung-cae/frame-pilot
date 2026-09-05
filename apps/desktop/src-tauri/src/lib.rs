//! FramePilot desktop shell. Sidecar spawn is owned by Rust; `npm run verify` does not compile this crate.

mod data_dir;
mod menu;
mod preview;
mod sidecar;
mod tray;

use std::path::PathBuf;
use std::process::Child;
use std::sync::atomic::Ordering;
use std::sync::{mpsc, Arc};
use std::thread;
use std::time::Duration;

use data_dir::{
    default_anchor_dir, ensure_data_dir, resolve_runtime_data_dir, write_data_dir_pointer,
};
use menu::{build_app_menu, handle_menu_event, DesktopPaths};
use sidecar::{
    allocate_loopback_port, api_pythonpath, app_quit_action, blocking_error_script,
    close_choice_from_handshake, close_decision, close_decision_requests_shutdown, close_job_kind,
    default_python, find_active_job, frozen_sidecar_binary, initialization_script_for_window,
    parse_quit_choice, probe_health, quit_dialog_script, repo_root, request_cancel_then_wait,
    sidecar_spawn_spec,
    sidecar_stderr_log, spawn_sidecar, staged_sidecar_resource_root, start_sidecar_unless_shutdown,
    supervisor_tick_after_probe, terminate_sidecar, wait_for_health, AppQuitAction, AppQuitEvent,
    CloseDecision, CloseJobKind, SidecarLaunchMode, SidecarStart, SidecarState, SpawnedSidecar,
    SupervisorTick, CANCEL_WAIT, STARTUP_TIMEOUT,
};
use tauri::{Listener, Manager, RunEvent, WindowEvent};

fn resolve_launch_mode(
    app: &tauri::AppHandle,
    repo_root: &std::path::Path,
) -> Result<SidecarLaunchMode, String> {
    if cfg!(debug_assertions) {
        return Ok(SidecarLaunchMode::DevVenv {
            python: default_python(repo_root),
            pythonpath: api_pythonpath(repo_root),
        });
    }

    let mut candidates = Vec::new();
    if let Ok(resource_dir) = app.path().resource_dir() {
        candidates.push(frozen_sidecar_binary(&resource_dir));
    }
    candidates.push(frozen_sidecar_binary(&staged_sidecar_resource_root()));

    for binary in &candidates {
        if binary.is_file() {
            return Ok(SidecarLaunchMode::Frozen {
                binary: binary.clone(),
            });
        }
    }

    Err(format!(
        "frozen sidecar not found (tried {}). Run packaging/pyinstaller/build.sh then packaging/scripts/stage-sidecar.sh before a release build.",
        candidates
            .iter()
            .map(|path| path.display().to_string())
            .collect::<Vec<_>>()
            .join(", ")
    ))
}

fn spawn_ready_sidecar(
    port: u16,
    data_dir: &std::path::Path,
    mode: &SidecarLaunchMode,
) -> Result<Child, String> {
    let spec = sidecar_spawn_spec(mode.clone(), port, data_dir).map_err(|err| err.to_string())?;
    let spawned = SpawnedSidecar::new(
        spawn_sidecar(&spec, &sidecar_stderr_log(data_dir)).map_err(|err| err.to_string())?,
    );
    let mut child = spawned.wait_ready(port, STARTUP_TIMEOUT)?;
    if !wait_for_health(port, STARTUP_TIMEOUT) {
        terminate_sidecar(&mut child);
        return Err("sidecar /health did not become ready".into());
    }
    Ok(child)
}

fn start_sidecar_process(
    port: u16,
    data_dir: &std::path::Path,
    mode: &SidecarLaunchMode,
    is_shutdown: impl Fn() -> bool,
) -> Result<SidecarStart, String> {
    start_sidecar_unless_shutdown(is_shutdown, || spawn_ready_sidecar(port, data_dir, mode))
}

fn start_sidecar_with_retry(
    port: u16,
    data_dir: &std::path::Path,
    mode: &SidecarLaunchMode,
    is_shutdown: impl Fn() -> bool,
) -> Result<(Child, bool), String> {
    match start_sidecar_process(port, data_dir, mode, &is_shutdown) {
        Ok(SidecarStart::Started(child)) => Ok((child, false)),
        Ok(SidecarStart::Abandoned) => Err("sidecar start abandoned during shutdown".into()),
        Err(first) => match start_sidecar_process(port, data_dir, mode, &is_shutdown) {
            Ok(SidecarStart::Started(child)) => Ok((child, true)),
            Ok(SidecarStart::Abandoned) => {
                Err(format!("{first}; retry abandoned during shutdown"))
            }
            Err(second) => Err(format!("{first}; retry failed: {second}")),
        },
    }
}

fn finish_quit(window: &tauri::Window, state: &SidecarState) {
    state.request_shutdown();
    let _ = window.destroy();
}

fn handle_close_requested(window: tauri::Window, state: Arc<SidecarState>, port: u16) {
    if state
        .close_in_progress
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return;
    }

    let job = find_active_job(port);
    let kind = close_job_kind(job.as_ref());
    if kind == CloseJobKind::None {
        finish_quit(&window, &state);
        return;
    }

    let Some(webview) = window.get_webview_window(window.label()) else {
        finish_quit(&window, &state);
        return;
    };
    let (tx, rx) = mpsc::channel();
    let event_id = webview.listen("framepilot-quit-choice", move |event| {
        let _ = tx.send(event.payload().to_string());
    });
    let payload = if webview.eval(&quit_dialog_script(kind)).is_err() {
        None
    } else {
        let first = rx.recv_timeout(Duration::from_secs(2)).ok();
        let dialog_shown = first
            .as_deref()
            .map(|payload| payload.trim().trim_matches('"') == "dialog_shown")
            .unwrap_or(false);
        if first.as_deref().and_then(parse_quit_choice).is_some() {
            first
        } else if dialog_shown {
            rx.recv_timeout(Duration::from_secs(3600)).ok()
        } else {
            None
        }
    };
    webview.unlisten(event_id);
    let choice = close_choice_from_handshake(payload.as_deref());
    let decision = close_decision(kind, choice);
    if !close_decision_requests_shutdown(decision) {
        state.close_in_progress.store(false, Ordering::SeqCst);
        return;
    }
    if decision == CloseDecision::CancelThenTerminate {
        if let Some(job) = job {
            let _ = request_cancel_then_wait(port, &job, CANCEL_WAIT);
        }
    }
    finish_quit(&window, &state);
}

#[tauri::command]
fn apply_data_directory(app: tauri::AppHandle, path: String) -> Result<String, String> {
    let new_dir = PathBuf::from(&path);
    if !new_dir.is_absolute() {
        return Err("data dir must be absolute".into());
    }
    let packaged = cfg!(not(debug_assertions));
    let anchor = default_anchor_dir(packaged).map_err(|err| err.to_string())?;
    write_data_dir_pointer(&anchor, &new_dir).map_err(|err| err.to_string())?;
    ensure_data_dir(&new_dir).map_err(|err| err.to_string())?;
    if let Some(paths) = app.try_state::<DesktopPaths>() {
        paths.set(new_dir.clone());
    }
    let Some(state) = app.try_state::<Arc<SidecarState>>() else {
        return Err("sidecar state is not configured".into());
    };
    let port = app
        .try_state::<preview::PreviewHost>()
        .map(|host| host.port)
        .ok_or_else(|| "preview host is not configured".to_string())?;
    let mode = resolve_launch_mode(&app, &repo_root())?;
    state.relocate_in_progress.store(true, Ordering::SeqCst);
    let result = (|| {
        state.terminate_stored_child();
        let child = spawn_ready_sidecar(port, &new_dir, &mode)?;
        state.store_child(child);
        Ok(new_dir.to_string_lossy().into_owned())
    })();
    state.relocate_in_progress.store(false, Ordering::SeqCst);
    result
}

fn show_blocking_error(app: &tauri::AppHandle, message: &str) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.eval(&blocking_error_script(message));
    }
}

fn supervise_sidecar(
    app: tauri::AppHandle,
    state: Arc<SidecarState>,
    port: u16,
    data_dir: PathBuf,
    mode: SidecarLaunchMode,
    mut restart_used: bool,
) {
    let mut health_failures: u8 = 0;
    loop {
        if state.is_shutdown() {
            return;
        }
        thread::sleep(Duration::from_millis(500));
        if state.is_shutdown() {
            return;
        }
        if state.relocate_in_progress.load(Ordering::SeqCst) {
            continue;
        }

        let exited = match state.child_has_exited() {
            Some(exited) => exited,
            None => return,
        };
        let healthy = probe_health(port, Duration::from_millis(400));
        match supervisor_tick_after_probe(
            state.is_shutdown(),
            exited,
            healthy,
            restart_used,
            health_failures,
        ) {
            SupervisorTick::Shutdown => return,
            SupervisorTick::Continue => {
                health_failures = 0;
                continue;
            }
            SupervisorTick::Restart => {
                restart_used = true;
                state.terminate_stored_child();
                if state.is_shutdown() {
                    return;
                }
                let current_dir = app
                    .try_state::<DesktopPaths>()
                    .map(|paths| paths.current())
                    .unwrap_or_else(|| data_dir.clone());
                match start_sidecar_process(port, &current_dir, &mode, || state.is_shutdown()) {
                    Ok(SidecarStart::Started(child)) => {
                        health_failures = 0;
                        state.store_child(child);
                    }
                    Ok(SidecarStart::Abandoned) => return,
                    Err(err) => {
                        show_blocking_error(
                            &app,
                            &format!("The local FramePilot API crashed and could not restart. {err}"),
                        );
                        return;
                    }
                }
            }
            SupervisorTick::BlockError => {
                show_blocking_error(
                    &app,
                    "The local FramePilot API stopped responding. Close the window and start FramePilot again.",
                );
                return;
            }
        }
    }
}

pub fn run() {
    let port = match allocate_loopback_port() {
        Ok(port) => port,
        Err(err) => {
            eprintln!("FramePilot could not allocate a loopback port: {err}");
            std::process::exit(1);
        }
    };
    let data_dir = match resolve_runtime_data_dir(cfg!(not(debug_assertions))) {
        Ok(path) => path,
        Err(err) => {
            eprintln!("FramePilot could not resolve the data directory: {err}");
            std::process::exit(1);
        }
    };
    let root = repo_root();
    let state = SidecarState::new();
    let setup_state = Arc::clone(&state);
    let setup_data_dir = data_dir.clone();

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(
            tauri_plugin_window_state::Builder::default()
                .with_denylist(&[preview::PREVIEW_WINDOW_LABEL])
                .build(),
        )
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            preview::toggle_detached_preview,
            preview::close_detached_preview,
            apply_data_directory,
        ])
        .manage(Arc::clone(&state))
        .manage(DesktopPaths::new(data_dir.clone()))
        .manage(preview::PreviewHost { port })
        .on_menu_event(|app, event| handle_menu_event(app, event))
        .setup(move |app| {
            let launch_mode = resolve_launch_mode(app.handle(), &root);

            let (startup_error, restart_used, watch_mode) = match launch_mode {
                Ok(mode) => {
                    let startup_state = Arc::clone(&setup_state);
                    match start_sidecar_with_retry(
                        port,
                        &setup_data_dir,
                        &mode,
                        move || startup_state.is_shutdown(),
                    ) {
                        Ok((child, restart_used)) => {
                            setup_state.store_child(child);
                            (None, restart_used, Some(mode))
                        }
                        Err(_) if setup_state.is_shutdown() => (None, true, Some(mode)),
                        Err(err) => (Some(err), true, Some(mode)),
                    }
                }
                Err(err) => (Some(err), true, None),
            };

            tauri::WebviewWindowBuilder::new(
                app,
                "main",
                tauri::WebviewUrl::App("index.html".into()),
            )
            .title("FramePilot")
            .inner_size(1200.0, 800.0)
            .min_inner_size(1100.0, 720.0)
            .initialization_script(&initialization_script_for_window(port, "main"))
            .build()?;

            let menu = build_app_menu(app)?;
            app.set_menu(menu)?;

            if let Err(err) = tray::install_tray(app.handle(), port, Arc::clone(&setup_state)) {
                eprintln!("FramePilot system tray is unavailable: {err}");
            }

            if let Some(err) = startup_error {
                show_blocking_error(
                    app.handle(),
                    &format!("The local FramePilot API failed to start. {err}"),
                );
            } else if let Some(mode) = watch_mode {
                let watch_app = app.handle().clone();
                let watch_state = Arc::clone(&setup_state);
                let watch_data_dir = setup_data_dir.clone();
                thread::spawn(move || {
                    supervise_sidecar(
                        watch_app,
                        watch_state,
                        port,
                        watch_data_dir,
                        mode,
                        restart_used,
                    );
                });
            }
            Ok(())
        })
        .on_window_event(move |window, event| {
            match event {
                WindowEvent::CloseRequested { api, .. } => {
                    if !preview::window_close_targets_app_quit(window.label()) {
                        return;
                    }
                    let shutting_down = window
                        .try_state::<Arc<SidecarState>>()
                        .is_some_and(|state| state.is_shutdown());
                    match app_quit_action(AppQuitEvent::WindowCloseRequested, shutting_down) {
                        AppQuitAction::PreventThenCloseDecision => {
                            api.prevent_close();
                            if let Some(state) = window.try_state::<Arc<SidecarState>>() {
                                let window = window.clone();
                                let state = Arc::clone(&state);
                                thread::spawn(move || handle_close_requested(window, state, port));
                            }
                        }
                        AppQuitAction::RequestShutdown => {
                            if let Some(state) = window.try_state::<Arc<SidecarState>>() {
                                state.request_shutdown();
                            }
                        }
                    }
                }
                WindowEvent::Destroyed => {
                    if preview::window_destroyed_requests_sidecar_shutdown(window.label()) {
                        if let Some(state) = window.try_state::<Arc<SidecarState>>() {
                            state.request_shutdown();
                        }
                    } else if window.label() == preview::PREVIEW_WINDOW_LABEL {
                        preview::emit_preview_closed(window.app_handle());
                    }
                }
                _ => {}
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building FramePilot desktop");

    app.run(move |app_handle, event| {
        match event {
            RunEvent::ExitRequested { api, .. } => {
                match app_quit_action(AppQuitEvent::ExitRequested, state.is_shutdown()) {
                    AppQuitAction::PreventThenCloseDecision => {
                        api.prevent_exit();
                        if let Some(webview) = app_handle.get_webview_window("main") {
                            let window = webview.as_ref().window();
                            let sidecar = Arc::clone(&state);
                            thread::spawn(move || handle_close_requested(window, sidecar, port));
                        }
                    }
                    AppQuitAction::RequestShutdown => state.request_shutdown(),
                }
            }
            RunEvent::Exit => {
                if app_quit_action(AppQuitEvent::Exit, state.is_shutdown())
                    == AppQuitAction::RequestShutdown
                {
                    state.request_shutdown();
                }
            }
            _ => {}
        }
    });
}
