//! FramePilot desktop shell. Sidecar spawn is owned by Rust; `npm run verify` does not compile this crate.

mod data_dir;
mod sidecar;

use std::process::Child;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::Duration;

use data_dir::resolve_runtime_data_dir;
use sidecar::{
    allocate_loopback_port, api_pythonpath, blocking_error_script, close_decision, close_job_kind,
    default_python, find_active_job, initialization_script, parse_quit_choice, probe_health,
    quit_dialog_script, recovery_action, repo_root, request_cancel_then_wait, sidecar_spawn_spec,
    sidecar_stderr_log, spawn_sidecar, store_sidecar_child, terminate_sidecar, wait_for_health,
    CloseChoice, CloseDecision, CloseJobKind, RecoveryAction, SpawnedSidecar, CANCEL_WAIT,
    STARTUP_TIMEOUT,
};
use tauri::{Listener, Manager, RunEvent, WindowEvent};

struct SidecarState {
    child: Mutex<Option<Child>>,
    shutdown: AtomicBool,
    close_in_progress: AtomicBool,
}

impl SidecarState {
    fn new() -> Arc<Self> {
        Arc::new(Self {
            child: Mutex::new(None),
            shutdown: AtomicBool::new(false),
            close_in_progress: AtomicBool::new(false),
        })
    }

    fn store_child(&self, child: Child) {
        store_sidecar_child(
            &self.child,
            self.shutdown.load(Ordering::SeqCst),
            child,
        );
    }

    fn request_shutdown(&self) {
        self.shutdown.store(true, Ordering::SeqCst);
        if let Ok(mut guard) = self.child.lock() {
            if let Some(mut child) = guard.take() {
                terminate_sidecar(&mut child);
            }
        }
    }
}

fn start_sidecar_process(
    port: u16,
    data_dir: &std::path::Path,
    python: &std::path::Path,
    pythonpath: &std::path::Path,
) -> Result<Child, String> {
    let spec = sidecar_spawn_spec(
        python.to_path_buf(),
        port,
        data_dir,
        pythonpath.to_path_buf(),
    )
    .map_err(|err| err.to_string())?;
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

fn start_sidecar_with_retry(
    port: u16,
    data_dir: &std::path::Path,
    python: &std::path::Path,
    pythonpath: &std::path::Path,
) -> Result<(Child, bool), String> {
    match start_sidecar_process(port, data_dir, python, pythonpath) {
        Ok(child) => Ok((child, false)),
        Err(first) => {
            match start_sidecar_process(port, data_dir, python, pythonpath) {
                Ok(child) => Ok((child, true)),
                Err(second) => Err(format!("{first}; retry failed: {second}")),
            }
        }
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
    if webview.eval(&quit_dialog_script(kind)).is_err() {
        finish_quit(&window, &state);
        return;
    }
    let first = rx.recv_timeout(Duration::from_secs(2)).ok();
    let dialog_shown = first
        .as_deref()
        .map(|payload| payload.trim().trim_matches('"') == "dialog_shown")
        .unwrap_or(false);
    let payload = if first.as_deref().and_then(parse_quit_choice).is_some() {
        first
    } else if dialog_shown {
        rx.recv_timeout(Duration::from_secs(3600)).ok()
    } else {
        None
    };
    webview.unlisten(event_id);
    let choice = payload
        .as_deref()
        .and_then(parse_quit_choice)
        .unwrap_or(CloseChoice::CancelAndQuit);
    match close_decision(kind, choice) {
        CloseDecision::Stay => {
            state.close_in_progress.store(false, Ordering::SeqCst);
        }
        CloseDecision::CancelThenTerminate => {
            if let Some(job) = job {
                let _ = request_cancel_then_wait(port, &job, CANCEL_WAIT);
            }
            finish_quit(&window, &state);
        }
        CloseDecision::Terminate => finish_quit(&window, &state),
    }
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
    data_dir: std::path::PathBuf,
    python: std::path::PathBuf,
    pythonpath: std::path::PathBuf,
    mut restart_used: bool,
) {
    let mut health_failures: u8 = 0;
    loop {
        if state.shutdown.load(Ordering::SeqCst) {
            return;
        }
        thread::sleep(Duration::from_millis(500));
        if state.shutdown.load(Ordering::SeqCst) {
            return;
        }

        let exited = match state.child.lock() {
            Ok(mut guard) => match guard.as_mut() {
                Some(child) => matches!(child.try_wait(), Ok(Some(_))),
                None => false,
            },
            Err(_) => return,
        };
        let healthy = probe_health(port, Duration::from_millis(400));
        if !exited && healthy {
            health_failures = 0;
            continue;
        }
        if !healthy {
            health_failures = health_failures.saturating_add(1);
        }

        match recovery_action(restart_used, health_failures) {
            RecoveryAction::Restart => {
                restart_used = true;
                if let Ok(mut guard) = state.child.lock() {
                    if let Some(mut child) = guard.take() {
                        terminate_sidecar(&mut child);
                    }
                }
                match start_sidecar_process(port, &data_dir, &python, &pythonpath) {
                    Ok(child) => {
                        health_failures = 0;
                        state.store_child(child);
                    }
                    Err(err) => {
                        show_blocking_error(
                            &app,
                            &format!("The local FramePilot API crashed and could not restart. {err}"),
                        );
                        return;
                    }
                }
            }
            RecoveryAction::BlockError => {
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
    let python = default_python(&root);
    let pythonpath = api_pythonpath(&root);
    let state = SidecarState::new();
    let setup_state = Arc::clone(&state);
    let setup_data_dir = data_dir.clone();
    let setup_python = python.clone();
    let setup_pythonpath = pythonpath.clone();

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .manage(Arc::clone(&state))
        .setup(move |app| {
            let (startup_error, restart_used) =
                match start_sidecar_with_retry(port, &setup_data_dir, &setup_python, &setup_pythonpath)
                {
                    Ok((child, restart_used)) => {
                        setup_state.store_child(child);
                        (None, restart_used)
                    }
                    Err(err) => (Some(err), true),
                };

            tauri::WebviewWindowBuilder::new(
                app,
                "main",
                tauri::WebviewUrl::App("index.html".into()),
            )
            .title("FramePilot")
            .inner_size(1200.0, 800.0)
            .min_inner_size(1100.0, 720.0)
            .initialization_script(&initialization_script(port))
            .build()?;

            if let Some(err) = startup_error {
                show_blocking_error(
                    app.handle(),
                    &format!("The local FramePilot API failed to start. {err}"),
                );
            } else {
                let watch_app = app.handle().clone();
                let watch_state = Arc::clone(&setup_state);
                let watch_data_dir = setup_data_dir.clone();
                let watch_python = setup_python.clone();
                let watch_pythonpath = setup_pythonpath.clone();
                thread::spawn(move || {
                    supervise_sidecar(
                        watch_app,
                        watch_state,
                        port,
                        watch_data_dir,
                        watch_python,
                        watch_pythonpath,
                        restart_used,
                    );
                });
            }
            Ok(())
        })
        .on_window_event(move |window, event| {
            match event {
                WindowEvent::CloseRequested { api, .. } => {
                    api.prevent_close();
                    if let Some(state) = window.try_state::<Arc<SidecarState>>() {
                        let window = window.clone();
                        let state = Arc::clone(&state);
                        thread::spawn(move || handle_close_requested(window, state, port));
                    }
                }
                WindowEvent::Destroyed => {
                    if let Some(state) = window.try_state::<Arc<SidecarState>>() {
                        state.request_shutdown();
                    }
                }
                _ => {}
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building FramePilot desktop");

    app.run(move |_app_handle, event| {
        if matches!(event, RunEvent::Exit | RunEvent::ExitRequested { .. }) {
            state.request_shutdown();
        }
    });
}
