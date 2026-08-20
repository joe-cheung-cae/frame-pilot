//! Python sidecar lifecycle helpers. Unit tests do not start a live API.

use std::fs::{self, OpenOptions};
use std::io::{self, BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

pub const STARTUP_TIMEOUT: Duration = Duration::from_secs(15);
pub const SHUTDOWN_GRACE: Duration = Duration::from_secs(5);
pub const CANCEL_WAIT: Duration = Duration::from_secs(10);

const READY_PREFIX: &str = "FRAMEPILOT_API ready ";
const LOOPBACK_HOST: &str = "127.0.0.1";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReadyLine {
    pub host: String,
    pub port: u16,
    pub data_dir: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReadyLineError {
    InvalidFormat,
    PortZero,
    PortMismatch { expected: u16, actual: u16 },
    HostNotLoopback,
}

impl std::fmt::Display for ReadyLineError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidFormat => write!(f, "ready line has invalid format"),
            Self::PortZero => write!(f, "ready line port must not be 0"),
            Self::PortMismatch { expected, actual } => {
                write!(f, "ready line port {actual} differs from allocated {expected}")
            }
            Self::HostNotLoopback => write!(f, "ready line host must be {LOOPBACK_HOST}"),
        }
    }
}

impl std::error::Error for ReadyLineError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SidecarSpawnSpec {
    pub program: PathBuf,
    pub args: Vec<String>,
    pub pythonpath: PathBuf,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecoveryAction {
    Restart,
    BlockError,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SupervisorTick {
    Continue,
    Shutdown,
    Restart,
    BlockError,
}

pub enum SidecarStart {
    Started(Child),
    Abandoned,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ShutdownAction {
    SendTerm,
    Wait,
    Kill,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CloseJobKind {
    None,
    Import,
    Processing,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CloseChoice {
    Stay,
    CancelAndQuit,
    QuitAnyway,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CloseDecision {
    Stay,
    CancelThenTerminate,
    Terminate,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ActiveJobRef {
    pub project_id: String,
    pub job_id: String,
    pub job_type: String,
    pub status: String,
}

pub fn shutdown_action(term_sent: bool, elapsed: Duration, grace: Duration) -> ShutdownAction {
    if !term_sent {
        ShutdownAction::SendTerm
    } else if elapsed >= grace {
        ShutdownAction::Kill
    } else {
        ShutdownAction::Wait
    }
}

pub fn close_job_kind(job: Option<&ActiveJobRef>) -> CloseJobKind {
    match job.map(|job| job.job_type.as_str()) {
        Some("import") => CloseJobKind::Import,
        Some("processing") => CloseJobKind::Processing,
        Some(_) => CloseJobKind::Processing,
        None => CloseJobKind::None,
    }
}

pub fn close_decision(kind: CloseJobKind, choice: CloseChoice) -> CloseDecision {
    match choice {
        CloseChoice::Stay => CloseDecision::Stay,
        CloseChoice::QuitAnyway => CloseDecision::Terminate,
        CloseChoice::CancelAndQuit => match kind {
            CloseJobKind::Import => CloseDecision::CancelThenTerminate,
            CloseJobKind::None | CloseJobKind::Processing => CloseDecision::Terminate,
        },
    }
}

pub fn parse_quit_choice(payload: &str) -> Option<CloseChoice> {
    let trimmed = payload.trim().trim_matches('"');
    match trimmed {
        "stay" => Some(CloseChoice::Stay),
        "cancel_and_quit" => Some(CloseChoice::CancelAndQuit),
        "quit_anyway" => Some(CloseChoice::QuitAnyway),
        _ => None,
    }
}

/// Unresolved handshake (`None`, including eval failure) stays. CancelAndQuit only from an explicit payload.
pub fn close_choice_from_handshake(payload: Option<&str>) -> CloseChoice {
    payload.and_then(parse_quit_choice).unwrap_or(CloseChoice::Stay)
}

pub fn job_status_is_terminal(status: &str) -> bool {
    matches!(
        status,
        "complete" | "complete_with_errors" | "failed" | "cancelled"
    )
}

pub fn quit_dialog_script(kind: CloseJobKind) -> String {
    let (title, body, extra_button) = match kind {
        CloseJobKind::Import => (
            "Import is still running",
            "You can keep working, quit and cancel the import, or quit anyway. Cancelled imports stay retryable and original photos are not modified.",
            r#"<button type=\"button\" data-choice=cancel_and_quit>Quit and cancel import</button>"#,
        ),
        CloseJobKind::Processing => (
            "Grouping and ranking is still running",
            "This job cannot be cancelled. You can keep working or quit anyway. The next launch marks the job failed and keeps original photos unchanged.",
            "",
        ),
        CloseJobKind::None => return String::new(),
    };
    format!(
        r#"(function() {{
  var existing = document.getElementById("framepilot-quit-dialog");
  if (existing) existing.remove();
  var overlay = document.createElement("div");
  overlay.id = "framepilot-quit-dialog";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.style.cssText = "position:fixed;inset:0;z-index:99999;display:grid;place-items:center;background:rgba(15,17,21,0.55);";
  overlay.innerHTML = "<div style=\"max-width:28rem;margin:1.5rem;padding:1.25rem;border-radius:0.5rem;background:#fff;color:#1f2933;font-family:system-ui,sans-serif;line-height:1.45\"><h2 style=\"margin:0 0 0.5rem;font-size:1.1rem\">{title}</h2><p style=\"margin:0 0 1rem\">{body}</p><div style=\"display:flex;flex-wrap:wrap;gap:0.5rem\">{extra_button}<button type=\"button\" data-choice=\"quit_anyway\">Quit anyway</button><button type=\"button\" data-choice=\"stay\">Keep working</button></div></div>";
  function emitChoice(choice) {{
    var emit = window.__TAURI__ && window.__TAURI__.event && window.__TAURI__.event.emit;
    if (emit) {{
      emit("framepilot-quit-choice", choice);
      return;
    }}
    var internals = window.__TAURI_INTERNALS__;
    if (internals && internals.invoke) {{
      internals.invoke("plugin:event|emit", {{ event: "framepilot-quit-choice", payload: choice }});
    }}
  }}
  function choose(choice) {{
    overlay.remove();
    emitChoice(choice);
  }}
  overlay.querySelectorAll("[data-choice]").forEach(function(button) {{
    button.addEventListener("click", function() {{ choose(button.getAttribute("data-choice")); }});
  }});
  document.body.appendChild(overlay);
  emitChoice("dialog_shown");
}})();"#
    )
}

pub fn allocate_loopback_port() -> io::Result<u16> {
    let listener = TcpListener::bind((LOOPBACK_HOST, 0))?;
    let port = listener.local_addr()?.port();
    drop(listener);
    if port == 0 {
        return Err(io::Error::other("loopback bind returned port 0"));
    }
    Ok(port)
}

pub fn parse_ready_line(line: &str, allocated_port: u16) -> Result<ReadyLine, ReadyLineError> {
    let line = line.trim();
    let Some(rest) = line.strip_prefix(READY_PREFIX) else {
        return Err(ReadyLineError::InvalidFormat);
    };

    let Some(host_rest) = rest.strip_prefix("host=") else {
        return Err(ReadyLineError::InvalidFormat);
    };
    let Some((host, after_host)) = host_rest.split_once(' ') else {
        return Err(ReadyLineError::InvalidFormat);
    };
    if host != LOOPBACK_HOST {
        return Err(ReadyLineError::HostNotLoopback);
    }

    let Some(port_rest) = after_host.strip_prefix("port=") else {
        return Err(ReadyLineError::InvalidFormat);
    };
    let Some((port_str, after_port)) = port_rest.split_once(' ') else {
        return Err(ReadyLineError::InvalidFormat);
    };
    let port: u16 = port_str.parse().map_err(|_| ReadyLineError::InvalidFormat)?;
    if port == 0 {
        return Err(ReadyLineError::PortZero);
    }
    if port != allocated_port {
        return Err(ReadyLineError::PortMismatch {
            expected: allocated_port,
            actual: port,
        });
    }

    let Some(data_dir) = after_port.strip_prefix("data_dir=") else {
        return Err(ReadyLineError::InvalidFormat);
    };
    if data_dir.is_empty() {
        return Err(ReadyLineError::InvalidFormat);
    }

    Ok(ReadyLine {
        host: host.to_string(),
        port,
        data_dir: data_dir.to_string(),
    })
}

pub fn api_base_url(port: u16) -> String {
    format!("http://{LOOPBACK_HOST}:{port}")
}

pub fn initialization_script(port: u16) -> String {
    format!(
        "window.__FRAMEPILOT_API_BASE__ = \"{}\";\nwindow.__FRAMEPILOT_DESKTOP__ = true;",
        api_base_url(port)
    )
}

pub fn blocking_error_script(message: &str) -> String {
    let html = format!(
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>FramePilot</title>\
<style>body{{font-family:system-ui,sans-serif;margin:48px;line-height:1.5}}</style></head>\
<body><h1>FramePilot could not start the local API</h1><p>{}</p></body></html>",
        html_escape(message)
    );
    let encoded = serde_json::to_string(&html).unwrap_or_else(|_| "\"FramePilot API failed\"".into());
    format!("document.open();document.write({encoded});document.close();")
}

pub fn sidecar_stderr_log(data_dir: &Path) -> PathBuf {
    data_dir.join("logs").join("sidecar.log")
}

pub fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(3)
        .expect("repo root from src-tauri")
        .to_path_buf()
}

pub fn default_python(repo_root: &Path) -> PathBuf {
    if cfg!(windows) {
        repo_root.join(".venv").join("Scripts").join("python.exe")
    } else {
        repo_root.join(".venv").join("bin").join("python")
    }
}

pub fn api_pythonpath(repo_root: &Path) -> PathBuf {
    repo_root.join("apps").join("api")
}

pub fn sidecar_spawn_spec(
    python: PathBuf,
    port: u16,
    data_dir: &Path,
    pythonpath: PathBuf,
) -> io::Result<SidecarSpawnSpec> {
    if port == 0 {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "shipped sidecar path must pass --port <n>, never --port 0",
        ));
    }
    if !data_dir.is_absolute() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "--data-dir must be an absolute path",
        ));
    }
    Ok(SidecarSpawnSpec {
        program: python,
        args: vec![
            "-m".into(),
            "app.sidecar_main".into(),
            "--host".into(),
            LOOPBACK_HOST.into(),
            "--port".into(),
            port.to_string(),
            "--data-dir".into(),
            data_dir.to_string_lossy().into_owned(),
        ],
        pythonpath,
    })
}

pub fn spawn_sidecar(spec: &SidecarSpawnSpec, stderr_log: &Path) -> io::Result<Child> {
    if let Some(parent) = stderr_log.parent() {
        fs::create_dir_all(parent)?;
    }
    let log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(stderr_log)?;
    let mut command = Command::new(&spec.program);
    command
        .args(&spec.args)
        .env("FRAMEPILOT_DESKTOP", "1")
        .env("PYTHONPATH", &spec.pythonpath)
        .stdout(Stdio::piped())
        .stderr(Stdio::from(log));
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NEW_PROCESS_GROUP: u32 = 0x00000200;
        command.creation_flags(CREATE_NEW_PROCESS_GROUP);
    }
    command.spawn()
}

/// Just-spawned sidecar. Drop terminates and waits while armed.
pub struct SpawnedSidecar {
    child: Option<Child>,
    armed: bool,
}

impl SpawnedSidecar {
    pub fn new(child: Child) -> Self {
        Self {
            child: Some(child),
            armed: true,
        }
    }

    pub fn child_mut(&mut self) -> &mut Child {
        self.child
            .as_mut()
            .expect("spawned sidecar child already taken")
    }

    pub fn into_child(mut self) -> Child {
        self.armed = false;
        self.child
            .take()
            .expect("spawned sidecar child already taken")
    }

    pub fn wait_ready(mut self, allocated_port: u16, timeout: Duration) -> Result<Child, String> {
        let stdout = self
            .child_mut()
            .stdout
            .take()
            .ok_or_else(|| "sidecar stdout missing".to_string())?;
        wait_for_ready_line(stdout, allocated_port, timeout).map_err(|err| err.to_string())?;
        Ok(self.into_child())
    }
}

impl Drop for SpawnedSidecar {
    fn drop(&mut self) {
        if !self.armed {
            return;
        }
        if let Some(ref mut child) = self.child {
            terminate_sidecar(child);
        }
    }
}

pub fn wait_for_ready_line(
    stdout: impl Read + Send + 'static,
    allocated_port: u16,
    timeout: Duration,
) -> io::Result<ReadyLine> {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let mut lines = BufReader::new(stdout).lines();
        let result = lines
            .next()
            .transpose()
            .map(|line| line.unwrap_or_default());
        let _ = tx.send(result);
    });
    match rx.recv_timeout(timeout) {
        Ok(Ok(line)) => parse_ready_line(&line, allocated_port)
            .map_err(|err| io::Error::new(io::ErrorKind::InvalidData, err.to_string())),
        Ok(Err(err)) => Err(err),
        Err(_) => Err(io::Error::new(
            io::ErrorKind::TimedOut,
            "timed out waiting for sidecar ready line",
        )),
    }
}

pub fn probe_health(port: u16, timeout: Duration) -> bool {
    let Ok(addr) = format!("{LOOPBACK_HOST}:{port}").parse() else {
        return false;
    };
    let Ok(mut stream) = TcpStream::connect_timeout(&addr, timeout) else {
        return false;
    };
    let _ = stream.set_read_timeout(Some(timeout));
    let _ = stream.set_write_timeout(Some(timeout));
    let request =
        format!("GET /health HTTP/1.1\r\nHost: {LOOPBACK_HOST}:{port}\r\nConnection: close\r\n\r\n");
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }
    let mut body = Vec::new();
    let _ = stream.read_to_end(&mut body);
    let text = String::from_utf8_lossy(&body);
    let status_ok = text.starts_with("HTTP/1.1 200") || text.starts_with("HTTP/1.0 200");
    status_ok && text.contains("\"status\"") && text.contains("ok")
}

pub fn wait_for_health(port: u16, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if probe_health(port, Duration::from_millis(400)) {
            return true;
        }
        thread::sleep(Duration::from_millis(100));
    }
    false
}

pub fn recovery_action(restart_already_used: bool, health_failures: u8) -> RecoveryAction {
    if health_failures >= 2 || restart_already_used {
        RecoveryAction::BlockError
    } else {
        RecoveryAction::Restart
    }
}

/// Re-check shutdown after `probe_health` so a close during the probe cannot Restart.
pub fn supervisor_tick_after_probe(
    shutdown: bool,
    exited: bool,
    healthy: bool,
    restart_used: bool,
    health_failures: u8,
) -> SupervisorTick {
    if shutdown {
        return SupervisorTick::Shutdown;
    }
    if !exited && healthy {
        return SupervisorTick::Continue;
    }
    let failures = if !healthy {
        health_failures.saturating_add(1)
    } else {
        health_failures
    };
    match recovery_action(restart_used, failures) {
        RecoveryAction::Restart => SupervisorTick::Restart,
        RecoveryAction::BlockError => SupervisorTick::BlockError,
    }
}

/// Spawn only if shutdown is clear. Re-check after spawn and terminate instead of
/// returning a live child when shutdown was set during startup.
pub fn start_sidecar_unless_shutdown<F>(
    is_shutdown: impl Fn() -> bool,
    spawn: F,
) -> Result<SidecarStart, String>
where
    F: FnOnce() -> Result<Child, String>,
{
    if is_shutdown() {
        return Ok(SidecarStart::Abandoned);
    }
    match spawn() {
        Ok(mut child) => {
            if is_shutdown() {
                terminate_sidecar(&mut child);
                return Ok(SidecarStart::Abandoned);
            }
            Ok(SidecarStart::Started(child))
        }
        Err(err) => {
            if is_shutdown() {
                Ok(SidecarStart::Abandoned)
            } else {
                Err(err)
            }
        }
    }
}

pub fn terminate_sidecar(child: &mut Child) {
    if let Ok(Some(_)) = child.try_wait() {
        return;
    }
    let started = Instant::now();
    let mut term_sent = false;
    loop {
        if let Ok(Some(_)) = child.try_wait() {
            return;
        }
        match shutdown_action(term_sent, started.elapsed(), SHUTDOWN_GRACE) {
            ShutdownAction::SendTerm => {
                send_term_signal(child);
                term_sent = true;
            }
            ShutdownAction::Wait => thread::sleep(Duration::from_millis(50)),
            ShutdownAction::Kill => {
                let _ = child.kill();
                let _ = child.wait();
                return;
            }
        }
    }
}

/// Store `child` unless shutdown is already set. Shutdown terminates instead of
/// dropping the process without a wait.
pub fn store_sidecar_child(slot: &Mutex<Option<Child>>, shutdown: bool, child: Child) {
    if shutdown {
        let mut child = child;
        terminate_sidecar(&mut child);
        return;
    }
    match slot.lock() {
        Ok(mut guard) => {
            *guard = Some(child);
        }
        Err(_) => {
            let mut child = child;
            terminate_sidecar(&mut child);
        }
    }
}

pub struct SidecarState {
    child: Mutex<Option<Child>>,
    shutdown: AtomicBool,
    pub close_in_progress: AtomicBool,
}

impl SidecarState {
    pub fn new() -> Arc<Self> {
        Arc::new(Self {
            child: Mutex::new(None),
            shutdown: AtomicBool::new(false),
            close_in_progress: AtomicBool::new(false),
        })
    }

    pub fn is_shutdown(&self) -> bool {
        self.shutdown.load(Ordering::SeqCst)
    }

    pub fn store_child(&self, child: Child) {
        store_sidecar_child(
            &self.child,
            self.shutdown.load(Ordering::SeqCst),
            child,
        );
    }

    pub fn child_has_exited(&self) -> Option<bool> {
        let mut guard = self.child.lock().ok()?;
        Some(match guard.as_mut() {
            Some(child) => matches!(child.try_wait(), Ok(Some(_))),
            None => false,
        })
    }

    pub fn terminate_stored_child(&self) {
        let taken = match self.child.lock() {
            Ok(mut guard) => guard.take(),
            Err(poisoned) => poisoned.into_inner().take(),
        };
        if let Some(mut child) = taken {
            terminate_sidecar(&mut child);
        }
    }

    pub fn request_shutdown(&self) {
        self.shutdown.store(true, Ordering::SeqCst);
        self.terminate_stored_child();
    }
}

impl Drop for SidecarState {
    fn drop(&mut self) {
        self.shutdown.store(true, Ordering::SeqCst);
        self.terminate_stored_child();
    }
}

fn http_exchange(
    port: u16,
    method: &str,
    path: &str,
    timeout: Duration,
) -> io::Result<(u16, String)> {
    let addr = format!("{LOOPBACK_HOST}:{port}")
        .parse()
        .map_err(|err| io::Error::new(io::ErrorKind::InvalidInput, err))?;
    let mut stream = TcpStream::connect_timeout(&addr, timeout)?;
    let _ = stream.set_read_timeout(Some(timeout));
    let _ = stream.set_write_timeout(Some(timeout));
    let request = format!(
        "{method} {path} HTTP/1.1\r\nHost: {LOOPBACK_HOST}:{port}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
    );
    stream.write_all(request.as_bytes())?;
    let mut raw = Vec::new();
    let _ = stream.read_to_end(&mut raw);
    parse_http_response(&String::from_utf8_lossy(&raw))
}

pub fn parse_http_response(text: &str) -> io::Result<(u16, String)> {
    let normalized = text.replace("\r\n", "\n");
    let (header, body) = normalized
        .split_once("\n\n")
        .unwrap_or((normalized.as_str(), ""));
    let status_line = header.lines().next().unwrap_or("");
    let status = status_line
        .split_whitespace()
        .nth(1)
        .and_then(|code| code.parse().ok())
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "missing HTTP status"))?;
    Ok((status, body.to_string()))
}

fn job_is_active(status: &str) -> bool {
    status == "queued" || status == "running"
}

pub fn first_active_job_from_projects_json(body: &str) -> Option<ActiveJobRef> {
    let value: serde_json::Value = serde_json::from_str(body).ok()?;
    for project in value.as_array()? {
        let project_id = project.get("id")?.as_str()?.to_string();
        let job = project.get("active_import_job")?;
        if job.is_null() {
            continue;
        }
        let status = job.get("status")?.as_str().unwrap_or("");
        if !job_is_active(status) {
            continue;
        }
        return Some(ActiveJobRef {
            project_id,
            job_id: job.get("id")?.as_str()?.to_string(),
            job_type: job
                .get("job_type")
                .and_then(|value| value.as_str())
                .unwrap_or("import")
                .to_string(),
            status: status.to_string(),
        });
    }
    None
}

pub fn first_active_job_from_jobs_json(project_id: &str, body: &str) -> Option<ActiveJobRef> {
    let value: serde_json::Value = serde_json::from_str(body).ok()?;
    for job in value.as_array()? {
        let status = job.get("status")?.as_str().unwrap_or("");
        if !job_is_active(status) {
            continue;
        }
        return Some(ActiveJobRef {
            project_id: job
                .get("project_id")
                .and_then(|value| value.as_str())
                .unwrap_or(project_id)
                .to_string(),
            job_id: job.get("id")?.as_str()?.to_string(),
            job_type: job.get("job_type")?.as_str()?.to_string(),
            status: status.to_string(),
        });
    }
    None
}

pub fn find_active_job(port: u16) -> Option<ActiveJobRef> {
    let timeout = Duration::from_millis(800);
    let (_, projects_body) = http_exchange(port, "GET", "/api/projects", timeout).ok()?;
    if let Some(job) = first_active_job_from_projects_json(&projects_body) {
        return Some(job);
    }
    let projects: serde_json::Value = serde_json::from_str(&projects_body).ok()?;
    for project in projects.as_array()? {
        let project_id = project.get("id")?.as_str()?;
        let path = format!("/api/projects/{project_id}/jobs?limit=50");
        if let Ok((200, body)) = http_exchange(port, "GET", &path, timeout) {
            if let Some(job) = first_active_job_from_jobs_json(project_id, &body) {
                return Some(job);
            }
        }
    }
    None
}

pub fn request_cancel_then_wait(port: u16, job: &ActiveJobRef, timeout: Duration) -> bool {
    let cancel_path = format!("/api/projects/{}/jobs/{}/cancel", job.project_id, job.job_id);
    let _ = http_exchange(port, "POST", &cancel_path, Duration::from_secs(2));
    let get_path = format!("/api/projects/{}/jobs/{}", job.project_id, job.job_id);
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if let Ok((200, body)) = http_exchange(port, "GET", &get_path, Duration::from_millis(400)) {
            if let Ok(value) = serde_json::from_str::<serde_json::Value>(&body) {
                if job_status_is_terminal(value.get("status").and_then(|status| status.as_str()).unwrap_or(""))
                {
                    return true;
                }
            }
        }
        thread::sleep(Duration::from_millis(200));
    }
    false
}

fn send_term_signal(child: &Child) {
    #[cfg(unix)]
    {
        extern "C" {
            fn kill(pid: i32, sig: i32) -> i32;
        }
        unsafe {
            kill(child.id() as i32, 15);
        }
    }
    #[cfg(windows)]
    {
        extern "system" {
            fn GenerateConsoleCtrlEvent(dwCtrlEvent: u32, dwProcessGroupId: u32) -> i32;
        }
        const CTRL_BREAK_EVENT: u32 = 1;
        unsafe {
            let _ = GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, child.id());
        }
    }
    #[cfg(not(any(unix, windows)))]
    {
        let _ = child;
    }
}

fn html_escape(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;
    use std::net::{IpAddr, Ipv4Addr, TcpListener, TcpStream};
    use std::process::{Command, Stdio};
    use std::sync::atomic::{AtomicBool, Ordering};
    use std::sync::{Arc, Mutex};
    use std::time::Instant;

    fn port_flag_value(args: &[String]) -> Option<&str> {
        args.windows(2)
            .find(|pair| pair[0] == "--port")
            .map(|pair| pair[1].as_str())
    }

    #[test]
    fn allocate_loopback_port_returns_nonzero_and_drops_listener() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        assert_ne!(port, 0);
        let rebound = TcpListener::bind((LOOPBACK_HOST, port))
            .expect("listener must have been dropped so the port can be rebound");
        let addr = rebound.local_addr().expect("local addr");
        assert_eq!(addr.ip(), IpAddr::V4(Ipv4Addr::LOCALHOST));
        assert_eq!(addr.port(), port);
    }

    #[test]
    fn parse_ready_line_accepts_data_dir_with_spaces() {
        let allocated = 55_555;
        let line = "FRAMEPILOT_API ready host=127.0.0.1 port=55555 data_dir=/Users/chao/Library/Application Support/FramePilot";
        let parsed = parse_ready_line(line, allocated).expect("parse ready line");
        assert_eq!(parsed.host, "127.0.0.1");
        assert_eq!(parsed.port, allocated);
        assert_eq!(
            parsed.data_dir,
            "/Users/chao/Library/Application Support/FramePilot"
        );
    }

    #[test]
    fn parse_ready_line_accepts_exact_string_with_spaced_data_dir() {
        let line = "FRAMEPILOT_API ready host=127.0.0.1 port=54321 data_dir=/Users/chao/Library/Application Support/FramePilot";
        let parsed = parse_ready_line(line, 54321).expect("valid ready line");
        assert_eq!(parsed.host, "127.0.0.1");
        assert_eq!(parsed.port, 54321);
        assert_eq!(
            parsed.data_dir,
            "/Users/chao/Library/Application Support/FramePilot"
        );
    }

    #[test]
    fn parse_ready_line_rejects_port_zero() {
        let line =
            "FRAMEPILOT_API ready host=127.0.0.1 port=0 data_dir=/tmp/Application Support/FramePilot";
        assert_eq!(parse_ready_line(line, 0), Err(ReadyLineError::PortZero));
        assert_eq!(
            parse_ready_line(
                "FRAMEPILOT_API ready host=127.0.0.1 port=0 data_dir=/tmp/framepilot-data",
                8000
            ),
            Err(ReadyLineError::PortZero)
        );
    }

    #[test]
    fn parse_ready_line_rejects_mismatched_allocated_port() {
        let line = "FRAMEPILOT_API ready host=127.0.0.1 port=55555 data_dir=/tmp/Application Support/FramePilot";
        assert_eq!(
            parse_ready_line(line, 12_345),
            Err(ReadyLineError::PortMismatch {
                expected: 12_345,
                actual: 55_555
            })
        );
        assert_eq!(
            parse_ready_line(
                "FRAMEPILOT_API ready host=127.0.0.1 port=8000 data_dir=/tmp/framepilot-data",
                9000
            ),
            Err(ReadyLineError::PortMismatch {
                expected: 9000,
                actual: 8000
            })
        );
    }

    #[test]
    fn wait_for_ready_line_parses_stdout_cursor() {
        let line = "FRAMEPILOT_API ready host=127.0.0.1 port=4242 data_dir=/tmp/Application Support/FramePilot\n";
        let parsed = wait_for_ready_line(Cursor::new(line), 4242, Duration::from_secs(1))
            .expect("ready line from cursor");
        assert_eq!(parsed.port, 4242);
        assert_eq!(parsed.data_dir, "/tmp/Application Support/FramePilot");
    }

    #[test]
    fn spawn_spec_never_passes_port_zero_and_keeps_absolute_data_dir() {
        let data_dir = PathBuf::from("/tmp/Application Support/FramePilot");
        let err = sidecar_spawn_spec(
            PathBuf::from("python"),
            0,
            &data_dir,
            PathBuf::from("/repo/apps/api"),
        )
        .expect_err("port 0 must be rejected");
        assert_eq!(err.kind(), io::ErrorKind::InvalidInput);

        let spec = sidecar_spawn_spec(
            PathBuf::from("python"),
            4242,
            &data_dir,
            PathBuf::from("/repo/apps/api"),
        )
        .expect("spawn spec");
        assert_eq!(port_flag_value(&spec.args), Some("4242"));
        assert_ne!(port_flag_value(&spec.args), Some("0"));
        let data_dir_index = spec
            .args
            .iter()
            .position(|arg| arg == "--data-dir")
            .expect("--data-dir");
        assert_eq!(spec.args[data_dir_index + 1], data_dir.to_string_lossy());
        assert!(Path::new(&spec.args[data_dir_index + 1]).is_absolute());
    }

    #[test]
    fn initialization_script_injects_literal_boolean_and_unslash_base() {
        let script = initialization_script(4242);
        assert!(script.contains("window.__FRAMEPILOT_API_BASE__ = \"http://127.0.0.1:4242\";"));
        assert!(!script.contains("http://127.0.0.1:4242/"));
        assert!(script.contains("window.__FRAMEPILOT_DESKTOP__ = true;"));
        assert!(!script.contains("__FRAMEPILOT_DESKTOP__ = \"true\""));
        assert!(!script.contains("__FRAMEPILOT_DESKTOP__ = 1"));
    }

    #[test]
    fn recovery_action_restarts_once_then_blocks() {
        assert_eq!(recovery_action(false, 0), RecoveryAction::Restart);
        assert_eq!(recovery_action(false, 1), RecoveryAction::Restart);
        assert_eq!(recovery_action(true, 1), RecoveryAction::BlockError);
        assert_eq!(recovery_action(false, 2), RecoveryAction::BlockError);
        assert_eq!(recovery_action(true, 2), RecoveryAction::BlockError);
    }

    #[test]
    fn shutdown_action_returns_kill_after_grace_window() {
        assert_eq!(
            shutdown_action(false, Duration::ZERO, SHUTDOWN_GRACE),
            ShutdownAction::SendTerm
        );
        assert_eq!(
            shutdown_action(true, Duration::from_millis(4_999), SHUTDOWN_GRACE),
            ShutdownAction::Wait
        );
        assert_eq!(
            shutdown_action(true, SHUTDOWN_GRACE, SHUTDOWN_GRACE),
            ShutdownAction::Kill
        );
        assert_eq!(
            shutdown_action(true, Duration::from_secs(6), SHUTDOWN_GRACE),
            ShutdownAction::Kill
        );
    }

    #[test]
    fn close_decision_cancels_import_only_and_maps_processing_to_terminate() {
        assert_eq!(
            close_decision(CloseJobKind::Import, CloseChoice::CancelAndQuit),
            CloseDecision::CancelThenTerminate
        );
        assert_eq!(
            close_decision(CloseJobKind::Processing, CloseChoice::CancelAndQuit),
            CloseDecision::Terminate
        );
        assert_eq!(
            close_decision(CloseJobKind::Processing, CloseChoice::QuitAnyway),
            CloseDecision::Terminate
        );
        assert_eq!(
            close_decision(CloseJobKind::Import, CloseChoice::Stay),
            CloseDecision::Stay
        );
        assert_eq!(
            close_job_kind(Some(&ActiveJobRef {
                project_id: "p".into(),
                job_id: "j".into(),
                job_type: "import".into(),
                status: "running".into(),
            })),
            CloseJobKind::Import
        );
        assert_eq!(
            close_job_kind(Some(&ActiveJobRef {
                project_id: "p".into(),
                job_id: "j".into(),
                job_type: "processing".into(),
                status: "queued".into(),
            })),
            CloseJobKind::Processing
        );
        assert_eq!(parse_quit_choice("\"cancel_and_quit\""), Some(CloseChoice::CancelAndQuit));
        assert_eq!(parse_quit_choice("stay"), Some(CloseChoice::Stay));
        assert!(job_status_is_terminal("cancelled"));
        assert!(job_status_is_terminal("failed"));
        assert!(!job_status_is_terminal("running"));
    }

    #[test]
    fn quit_dialog_script_hides_cancel_for_processing_jobs() {
        let import_script = quit_dialog_script(CloseJobKind::Import);
        assert!(import_script.contains("Quit and cancel import"));
        assert!(import_script.contains("Keep working"));
        assert!(import_script.contains("Quit anyway"));
        let processing_script = quit_dialog_script(CloseJobKind::Processing);
        assert!(!processing_script.contains("Quit and cancel"));
        assert!(processing_script.contains("cannot be cancelled"));
        assert!(processing_script.contains("Quit anyway"));
    }

    fn assert_javascript_parses(script: &str) {
        let path = std::env::temp_dir().join(format!(
            "framepilot-quit-dialog-{}-{}.js",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("time")
                .as_nanos()
        ));
        std::fs::write(&path, script).expect("write quit dialog script");
        let output = Command::new("node")
            .arg("--check")
            .arg(&path)
            .output()
            .expect("node --check");
        let _ = std::fs::remove_file(&path);
        assert!(
            output.status.success(),
            "quit dialog script failed node --check: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    #[test]
    fn quit_dialog_script_import_is_valid_javascript_with_cancel_button() {
        let import_script = quit_dialog_script(CloseJobKind::Import);
        assert!(
            import_script.contains("data-choice=cancel_and_quit"),
            "import overlay must keep data-choice=cancel_and_quit: {import_script}"
        );
        assert!(import_script.contains("Quit and cancel import"));
        assert_javascript_parses(&import_script);
    }

    #[test]
    fn quit_dialog_script_processing_is_valid_javascript_without_cancel() {
        let processing_script = quit_dialog_script(CloseJobKind::Processing);
        assert!(!processing_script.contains("Quit and cancel"));
        assert!(!processing_script.contains("cancel_and_quit"));
        assert!(processing_script.contains("Quit anyway"));
        assert_javascript_parses(&processing_script);
    }

    #[test]
    fn close_choice_from_handshake_unresolved_stays() {
        assert_eq!(close_choice_from_handshake(None), CloseChoice::Stay);
        assert_eq!(
            close_choice_from_handshake(Some("dialog_shown")),
            CloseChoice::Stay
        );
        assert_eq!(
            close_choice_from_handshake(Some("\"dialog_shown\"")),
            CloseChoice::Stay
        );
        assert_eq!(
            close_choice_from_handshake(Some("not-a-choice")),
            CloseChoice::Stay
        );
        assert_eq!(close_choice_from_handshake(Some("")), CloseChoice::Stay);
        assert_eq!(close_choice_from_handshake(Some("stay")), CloseChoice::Stay);
        assert_eq!(
            close_choice_from_handshake(Some("\"cancel_and_quit\"")),
            CloseChoice::CancelAndQuit
        );
        assert_eq!(
            close_choice_from_handshake(Some("cancel_and_quit")),
            CloseChoice::CancelAndQuit
        );
        assert_eq!(
            close_choice_from_handshake(Some("quit_anyway")),
            CloseChoice::QuitAnyway
        );
        assert_eq!(
            close_decision(CloseJobKind::Import, close_choice_from_handshake(None)),
            CloseDecision::Stay
        );
        assert_eq!(
            close_decision(
                CloseJobKind::Import,
                close_choice_from_handshake(Some("dialog_shown"))
            ),
            CloseDecision::Stay
        );
        assert_eq!(
            close_decision(
                CloseJobKind::Import,
                close_choice_from_handshake(Some("cancel_and_quit"))
            ),
            CloseDecision::CancelThenTerminate
        );
        assert_eq!(
            close_decision(
                CloseJobKind::Import,
                close_choice_from_handshake(Some("quit_anyway"))
            ),
            CloseDecision::Terminate
        );
        assert_eq!(
            close_decision(
                CloseJobKind::Processing,
                close_choice_from_handshake(Some("cancel_and_quit"))
            ),
            CloseDecision::Terminate
        );
    }

    #[test]
    fn first_active_job_parsers_read_import_and_processing_jobs() {
        let projects = r#"[{"id":"proj-1","active_import_job":{"id":"job-1","job_type":"import","status":"running"}}]"#;
        let import_job = first_active_job_from_projects_json(projects).expect("import job");
        assert_eq!(import_job.job_id, "job-1");
        assert_eq!(import_job.job_type, "import");
        let idle = r#"[{"id":"proj-1","active_import_job":null}]"#;
        assert_eq!(first_active_job_from_projects_json(idle), None);
        let jobs = r#"[{"id":"job-2","project_id":"proj-1","job_type":"processing","status":"queued"}]"#;
        let processing = first_active_job_from_jobs_json("proj-1", jobs).expect("processing job");
        assert_eq!(processing.job_id, "job-2");
        assert_eq!(processing.job_type, "processing");
    }

    fn wait_until_listening(port: u16, timeout: Duration) {
        let deadline = Instant::now() + timeout;
        let addr = format!("{LOOPBACK_HOST}:{port}")
            .parse()
            .expect("loopback addr");
        while Instant::now() < deadline {
            if TcpStream::connect_timeout(&addr, Duration::from_millis(50)).is_ok() {
                return;
            }
            thread::sleep(Duration::from_millis(20));
        }
        panic!("loopback holder did not listen on {port}");
    }

    fn spawn_loopback_holder(port: u16, stdout: Stdio, ready_line: Option<&str>) -> Child {
        let script = r#"
import socket, sys, time
port = int(sys.argv[1])
line = sys.argv[2]
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("127.0.0.1", port))
sock.listen(1)
if line:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
while True:
    time.sleep(60)
"#;
        let child = Command::new("python3")
            .args(["-c", script, &port.to_string(), ready_line.unwrap_or("")])
            .stdout(stdout)
            .stderr(Stdio::null())
            .spawn()
            .expect("spawn python3 loopback holder");
        let spawned = SpawnedSidecar::new(child);
        wait_until_listening(port, Duration::from_secs(2));
        spawned.into_child()
    }

    fn process_is_alive(pid: u32) -> bool {
        #[cfg(unix)]
        {
            extern "C" {
                fn kill(pid: i32, sig: i32) -> i32;
            }
            unsafe { kill(pid as i32, 0) == 0 }
        }
        #[cfg(not(unix))]
        {
            let _ = pid;
            false
        }
    }

    fn assert_port_free(port: u16) {
        let rebound = TcpListener::bind((LOOPBACK_HOST, port))
            .expect("allocated loopback port must be free after terminate-and-wait");
        let addr = rebound.local_addr().expect("local addr");
        assert_eq!(addr.ip(), IpAddr::V4(Ipv4Addr::LOCALHOST));
        assert_eq!(addr.port(), port);
    }

    #[test]
    fn ready_line_timeout_terminates_listener_and_retry_can_bind_same_port() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::piped(), None);
        let err = SpawnedSidecar::new(child)
            .wait_ready(port, Duration::from_millis(300))
            .expect_err("ready line must time out");
        assert!(err.contains("timed out"), "{err}");
        assert_port_free(port);

        let retry = spawn_loopback_holder(port, Stdio::piped(), None);
        let retry_err = SpawnedSidecar::new(retry)
            .wait_ready(port, Duration::from_millis(300))
            .expect_err("retry ready line must time out");
        assert!(retry_err.contains("timed out"), "{retry_err}");
        assert_port_free(port);
    }

    #[test]
    fn ready_line_parse_failure_terminates_listener_and_frees_port() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::piped(), Some("not a ready line"));
        let err = SpawnedSidecar::new(child)
            .wait_ready(port, Duration::from_secs(2))
            .expect_err("ready line must fail to parse");
        assert!(
            err.contains("invalid") || err.contains("ready line"),
            "{err}"
        );
        assert_port_free(port);
    }

    #[test]
    fn missing_stdout_terminates_child_before_return() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::null(), None);
        let pid = child.id();
        let err = SpawnedSidecar::new(child)
            .wait_ready(port, Duration::from_secs(1))
            .expect_err("missing stdout must fail");
        assert_eq!(err, "sidecar stdout missing");
        assert!(!process_is_alive(pid), "child {pid} must be terminated");
        assert_port_free(port);
    }

    #[test]
    fn store_child_terminates_when_shutdown_is_set() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::null(), None);
        let pid = child.id();
        let slot = Mutex::new(None);
        store_sidecar_child(&slot, true, child);
        assert!(slot.lock().expect("slot").is_none());
        assert!(!process_is_alive(pid), "child {pid} must be terminated");
        assert_port_free(port);
    }

    #[test]
    fn store_child_keeps_child_when_shutdown_is_clear() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::null(), None);
        let slot: Mutex<Option<Child>> = Mutex::new(None);
        store_sidecar_child(&slot, false, child);
        assert!(slot.lock().expect("slot").is_some());
        TcpListener::bind((LOOPBACK_HOST, port))
            .expect_err("stored child must still own the allocated port");
        let stored = slot.lock().expect("slot").take().expect("stored child");
        drop(SpawnedSidecar::new(stored));
        assert_port_free(port);
    }

    #[test]
    fn supervisor_rechecks_shutdown_after_health_probe() {
        assert_eq!(recovery_action(false, 1), RecoveryAction::Restart);
        assert_eq!(
            supervisor_tick_after_probe(true, false, false, false, 0),
            SupervisorTick::Shutdown
        );
        assert_eq!(
            supervisor_tick_after_probe(true, true, false, false, 1),
            SupervisorTick::Shutdown
        );
        assert_eq!(
            supervisor_tick_after_probe(true, false, true, false, 0),
            SupervisorTick::Shutdown
        );
        assert_eq!(
            supervisor_tick_after_probe(false, false, true, false, 0),
            SupervisorTick::Continue
        );
        assert_eq!(
            supervisor_tick_after_probe(false, false, false, false, 0),
            SupervisorTick::Restart
        );
        assert_eq!(
            supervisor_tick_after_probe(false, false, false, true, 1),
            SupervisorTick::BlockError
        );
    }

    #[test]
    fn start_sidecar_process_does_not_spawn_when_shutdown_is_set() {
        let spawn_called = AtomicBool::new(false);
        let result = start_sidecar_unless_shutdown(
            || true,
            || {
                spawn_called.store(true, Ordering::SeqCst);
                Err("spawn must not run after shutdown".into())
            },
        )
        .expect("shutdown start is not an error");
        assert!(!spawn_called.load(Ordering::SeqCst));
        assert!(matches!(result, SidecarStart::Abandoned));
    }

    #[test]
    fn start_sidecar_process_terminates_child_spawned_after_shutdown() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let shutdown = AtomicBool::new(false);
        let result = start_sidecar_unless_shutdown(
            || shutdown.swap(true, Ordering::SeqCst),
            || Ok(spawn_loopback_holder(port, Stdio::null(), None)),
        )
        .expect("post-spawn shutdown is not an error");
        assert!(matches!(result, SidecarStart::Abandoned));
        assert_port_free(port);
    }

    #[test]
    fn start_sidecar_process_and_store_child_do_not_keep_live_child_when_shutdown_is_set() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::null(), None);
        let pid = child.id();
        let state = SidecarState::new();
        state.request_shutdown();
        state.store_child(child);
        assert!(!process_is_alive(pid), "store_child must terminate");
        assert_port_free(port);

        let port = allocate_loopback_port().expect("allocate loopback port");
        let started = start_sidecar_unless_shutdown(
            || state.is_shutdown(),
            || Ok(spawn_loopback_holder(port, Stdio::null(), None)),
        )
        .expect("start after shutdown");
        assert!(matches!(started, SidecarStart::Abandoned));
        assert_port_free(port);
    }

    #[test]
    fn start_sidecar_process_abandons_spawn_error_when_shutdown_is_set() {
        let shutdown = AtomicBool::new(false);
        let result = start_sidecar_unless_shutdown(
            || shutdown.swap(true, Ordering::SeqCst),
            || Err("sidecar /health did not become ready".into()),
        )
        .expect("shutdown during failed start is not an error");
        assert!(matches!(result, SidecarStart::Abandoned));
    }

    #[test]
    fn close_during_health_probe_leaves_no_sidecar() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::null(), None);
        let pid = child.id();
        let state = SidecarState::new();
        state.store_child(child);
        let shutdown_state = Arc::clone(&state);
        let shutdown_thread = thread::spawn(move || {
            thread::sleep(Duration::from_millis(50));
            shutdown_state.request_shutdown();
        });
        let _healthy = probe_health(port, Duration::from_millis(400));
        assert_eq!(
            supervisor_tick_after_probe(state.is_shutdown(), false, false, false, 0),
            SupervisorTick::Shutdown
        );
        shutdown_thread.join().expect("shutdown thread");
        assert!(!process_is_alive(pid), "child {pid} must be terminated");
        assert_port_free(port);
    }

    #[test]
    fn sidecar_state_drop_terminates_stored_child() {
        let port = allocate_loopback_port().expect("allocate loopback port");
        let child = spawn_loopback_holder(port, Stdio::null(), None);
        let pid = child.id();
        let state = SidecarState::new();
        state.store_child(child);
        drop(state);
        assert!(!process_is_alive(pid), "Drop must terminate child {pid}");
        assert_port_free(port);
    }
}
