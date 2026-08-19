//! Python sidecar lifecycle helpers. Unit tests do not start a live API.

use std::fs::{self, OpenOptions};
use std::io::{self, BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

pub const STARTUP_TIMEOUT: Duration = Duration::from_secs(15);
pub const SHUTDOWN_GRACE: Duration = Duration::from_secs(5);

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

pub fn terminate_sidecar(child: &mut Child) {
    if let Ok(Some(_)) = child.try_wait() {
        return;
    }
    send_term_signal(child);
    let deadline = Instant::now() + SHUTDOWN_GRACE;
    while Instant::now() < deadline {
        if let Ok(Some(_)) = child.try_wait() {
            return;
        }
        thread::sleep(Duration::from_millis(50));
    }
    let _ = child.kill();
    let _ = child.wait();
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
    use std::net::{IpAddr, Ipv4Addr, TcpListener};

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
}
