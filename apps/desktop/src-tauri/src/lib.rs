//! Phase 0 sidecar spawn skeleton. This crate is not compiled by `npm run verify`.

use std::io::{BufRead, BufReader};
use std::net::TcpListener;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

struct SidecarProcess {
    child: Child,
}

impl SidecarProcess {
    fn spawn(port: u16, data_dir: PathBuf) -> std::io::Result<Self> {
        let python = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .nth(3)
            .expect("repo root")
            .join(".venv/bin/python");
        let mut command = Command::new(python);
        command
            .args([
                "-m",
                "app.sidecar_main",
                "--host",
                "127.0.0.1",
                "--port",
                &port.to_string(),
                "--data-dir",
                &data_dir.to_string_lossy(),
            ])
            .env("FRAMEPILOT_DESKTOP", "1")
            .env(
                "PYTHONPATH",
                PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                    .ancestors()
                    .nth(3)
                    .expect("repo root")
                    .join("apps/api"),
            )
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        Ok(Self {
            child: command.spawn()?,
        })
    }

    fn terminate(&mut self) {
        let _ = self.child.kill();
        let deadline = Instant::now() + Duration::from_secs(5);
        while Instant::now() < deadline {
            if let Ok(Some(_)) = self.child.try_wait() {
                return;
            }
            std::thread::sleep(Duration::from_millis(50));
        }
        let _ = self.child.kill();
    }
}

fn allocate_loopback_port() -> std::io::Result<u16> {
    let listener = TcpListener::bind(("127.0.0.1", 0))?;
    Ok(listener.local_addr()?.port())
}

fn wait_for_ready_line(child: &mut Child) -> std::io::Result<String> {
    let stdout = child.stdout.take().ok_or_else(|| {
        std::io::Error::new(std::io::ErrorKind::BrokenPipe, "sidecar stdout missing")
    })?;
    let mut lines = BufReader::new(stdout).lines();
    let line = lines.next().transpose()?.unwrap_or_default();
    if !line.starts_with("FRAMEPILOT_API ready host=127.0.0.1 port=") {
        return Err(std::io::Error::other(format!("unexpected ready line: {line}")));
    }
    Ok(line)
}

pub fn run() {
    // Intended runtime: bind a free loopback port, spawn the sidecar, poll /health
    // for 15s, and SIGTERM on window exit. This host cannot compile Tauri without rustc.
    let _ = (allocate_loopback_port, wait_for_ready_line, SidecarProcess::spawn);
    eprintln!("FramePilot desktop shell requires rustc/cargo; sidecar spawn is not started.");
}
