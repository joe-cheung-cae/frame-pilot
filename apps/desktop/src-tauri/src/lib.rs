//! FramePilot desktop shell. Sidecar spawn is owned by Rust; `npm run verify` does not compile this crate.

mod data_dir;
mod menu;
mod sidecar;

use std::process::Child;
use std::sync::atomic::Ordering;
use std::sync::{mpsc, Arc};
use std::thread;
use std::time::Duration;

use data_dir::resolve_runtime_data_dir;
use menu::{build_app_menu, handle_menu_event, DesktopPaths};
use sidecar::{
    allocate_loopback_port, api_pythonpath, app_quit_action, blocking_error_script,
    close_choice_from_handshake, close_decision, close_decision_requests_shutdown, close_job_kind,
    default_python, find_active_job, initialization_script, parse_quit_choice, probe_health,
    quit_dialog_script, repo_root, request_cancel_then_wait, sidecar_spawn_spec, sidecar_stderr_log,
    spawn_sidecar, start_sidecar_unless_shutdown, supervisor_tick_after_probe, terminate_sidecar,
    wait_for_health, AppQuitAction, AppQuitEvent, CloseDecision, CloseJobKind, SidecarStart,
    SidecarState, SpawnedSidecar, SupervisorTick, CANCEL_WAIT, STARTUP_TIMEOUT,
};
use tauri::{Listener, Manager, RunEvent, WindowEvent};
