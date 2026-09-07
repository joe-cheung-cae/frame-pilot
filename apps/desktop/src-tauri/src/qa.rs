//! Fail-closed Path B QA gate. Injected only for the packaged leftover harness.

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

const QA_FLAG: &str = "FRAMEPILOT_DESKTOP_QA";
const QA_PHOTOS: &str = "FRAMEPILOT_DESKTOP_QA_PHOTOS";
const QA_PROJECT: &str = "FRAMEPILOT_DESKTOP_QA_PROJECT";
const QA_EVIDENCE: &str = "FRAMEPILOT_DESKTOP_QA_EVIDENCE";
const DATA_DIR_ENV: &str = "FRAMEPILOT_DATA_DIR";
const SCRATCH_DIR_NAME: &str = "framepilot-desktop-500-gui";
const MILESTONES_FILE: &str = "milestones.jsonl";

#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
pub struct DesktopQaPayload {
    pub photos: String,
    pub project: String,
    pub evidence: String,
}

#[derive(Debug, Clone)]
pub struct DesktopQaState {
    pub enabled: bool,
    pub evidence_path: Option<PathBuf>,
}

pub struct DesktopQaEnv<'a> {
    pub qa_flag: Option<&'a str>,
    pub photos: Option<&'a str>,
    pub project: Option<&'a str>,
    pub evidence: Option<&'a str>,
    pub data_dir: Option<&'a str>,
    pub prefix: &'a str,
}

fn split_qa_path(raw: &str) -> Option<(bool, Vec<String>)> {
    let s = raw.trim();
    if s.is_empty() || s.contains('\0') {
        return None;
    }
    if s.starts_with('/') {
        return normalize_parts(s.split('/'), false, Vec::new());
    }
    let bytes = s.as_bytes();
    if bytes.len() >= 2 && bytes[0].is_ascii_alphabetic() && bytes[1] == b':' {
        let rest = if bytes.len() >= 3 && (bytes[2] == b'\\' || bytes[2] == b'/') {
            &s[3..]
        } else {
            return None;
        };
        let drive = format!("{}:", s[..1].to_ascii_uppercase());
        return normalize_parts(rest.split(['\\', '/']), true, vec![drive]);
    }
    if s.starts_with(r"\\") {
        let rest = s.trim_start_matches('\\');
        return normalize_parts(rest.split(['\\', '/']), true, vec![String::from("UNC")]);
    }
    None
}

fn normalize_parts<'a>(
    parts: impl Iterator<Item = &'a str>,
    windows: bool,
    mut out: Vec<String>,
) -> Option<(bool, Vec<String>)> {
    for part in parts {
        if part.is_empty() || part == "." {
            continue;
        }
        if part == ".." {
            if windows && out.len() <= 1 {
                return None;
            }
            if !windows && out.is_empty() {
                return None;
            }
            let _ = out.pop();
            continue;
        }
        out.push(part.to_string());
    }
    Some((windows, out))
}

fn same_component(left: &str, right: &str, windows: bool) -> bool {
    if windows {
        left.eq_ignore_ascii_case(right)
    } else {
        left == right
    }
}

fn components_start_with(path: &[String], prefix: &[String], windows: bool) -> bool {
    path.len() >= prefix.len()
        && path
            .iter()
            .zip(prefix)
            .all(|(left, right)| same_component(left, right, windows))
}

fn is_absolute_under_prefix(path: &str, prefix: &str) -> bool {
    match (split_qa_path(path), split_qa_path(prefix)) {
        (Some((windows_path, path_parts)), Some((windows_prefix, prefix_parts)))
            if windows_path == windows_prefix =>
        {
            path_parts.len() > prefix_parts.len()
                && components_start_with(&path_parts, &prefix_parts, windows_path)
        }
        _ => false,
    }
}

fn is_same_or_descendant(path: &str, ancestor: &str) -> bool {
    match (split_qa_path(path), split_qa_path(ancestor)) {
        (Some((windows_path, path_parts)), Some((windows_ancestor, ancestor_parts)))
            if windows_path == windows_ancestor =>
        {
            components_start_with(&path_parts, &ancestor_parts, windows_path)
        }
        _ => false,
    }
}

pub fn qa_scratch_prefix_from_env() -> Option<String> {
    if cfg!(windows) {
        let local = std::env::var("LOCALAPPDATA").ok()?;
        let trimmed = local.trim_end_matches(['\\', '/']);
        if trimmed.is_empty() {
            return None;
        }
        Some(format!(r"{trimmed}\{SCRATCH_DIR_NAME}"))
    } else {
        let home = std::env::var("HOME").ok()?;
        let trimmed = home.trim_end_matches('/');
        if trimmed.is_empty() {
            return None;
        }
        Some(format!("{trimmed}/.cache/{SCRATCH_DIR_NAME}"))
    }
}

pub fn resolve_desktop_qa(input: DesktopQaEnv<'_>) -> Option<DesktopQaPayload> {
    if input.qa_flag != Some("1") {
        return None;
    }
    let photos = input.photos?.trim();
    let project = input.project?.trim();
    let evidence = input.evidence?.trim();
    let data_dir = input.data_dir?.trim();
    if photos.is_empty() || project.is_empty() || evidence.is_empty() || data_dir.is_empty() {
        return None;
    }
    if !is_absolute_under_prefix(photos, input.prefix)
        || !is_absolute_under_prefix(project, input.prefix)
        || !is_absolute_under_prefix(evidence, input.prefix)
        || !is_absolute_under_prefix(data_dir, input.prefix)
    {
        return None;
    }
    if is_same_or_descendant(data_dir, project) {
        return None;
    }
    Some(DesktopQaPayload {
        photos: photos.to_string(),
        project: project.to_string(),
        evidence: evidence.to_string(),
    })
}

pub fn resolve_desktop_qa_from_env() -> Option<DesktopQaPayload> {
    let prefix = qa_scratch_prefix_from_env()?;
    let qa_flag = std::env::var(QA_FLAG).ok();
    let photos = std::env::var(QA_PHOTOS).ok();
    let project = std::env::var(QA_PROJECT).ok();
    let evidence = std::env::var(QA_EVIDENCE).ok();
    let data_dir = std::env::var(DATA_DIR_ENV).ok();
    resolve_desktop_qa(DesktopQaEnv {
        qa_flag: qa_flag.as_deref(),
        photos: photos.as_deref(),
        project: project.as_deref(),
        evidence: evidence.as_deref(),
        data_dir: data_dir.as_deref(),
        prefix: &prefix,
    })
}

pub fn load_desktop_qa_state() -> DesktopQaState {
    match resolve_desktop_qa_from_env() {
        Some(payload) => DesktopQaState {
            enabled: true,
            evidence_path: Some(PathBuf::from(payload.evidence).join(MILESTONES_FILE)),
        },
        None => DesktopQaState {
            enabled: false,
            evidence_path: None,
        },
    }
}

pub fn qa_init_script_assignment(payload: &DesktopQaPayload) -> Option<String> {
    let json = serde_json::to_string(payload).ok()?;
    Some(format!("\nwindow.__FRAMEPILOT_DESKTOP_QA__ = {json};"))
}

pub fn write_qa_evidence_line(
    enabled: bool,
    dest: Option<&Path>,
    line: &str,
) -> Result<(), String> {
    if !enabled {
        return Err("qa evidence is disabled".into());
    }
    let Some(dest) = dest else {
        return Err("qa evidence is disabled".into());
    };
    if line.contains('\n') || line.contains('\r') {
        return Err("qa evidence line must not contain newlines".into());
    }
    let trimmed = line.trim();
    if trimmed.is_empty() {
        return Err("qa evidence line is empty".into());
    }
    let parsed: serde_json::Value =
        serde_json::from_str(trimmed).map_err(|err| format!("qa evidence is not JSON: {err}"))?;
    let obj = parsed
        .as_object()
        .ok_or_else(|| "qa evidence must be a JSON object".to_string())?;
    match (obj.get("milestone"), obj.get("t")) {
        (Some(serde_json::Value::String(milestone)), Some(serde_json::Value::String(t)))
            if !milestone.is_empty() && !t.is_empty() => {}
        _ => {
            return Err("qa evidence must include string milestone and t".into());
        }
    }
    if let Some(parent) = dest.parent() {
        fs::create_dir_all(parent).map_err(|err| err.to_string())?;
    }
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(dest)
        .map_err(|err| err.to_string())?;
    file.write_all(trimmed.as_bytes())
        .map_err(|err| err.to_string())?;
    file.write_all(b"\n").map_err(|err| err.to_string())?;
    file.flush().map_err(|err| err.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn qa_write_evidence(
    state: tauri::State<DesktopQaState>,
    line: String,
) -> Result<(), String> {
    write_qa_evidence_line(state.enabled, state.evidence_path.as_deref(), &line)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn posix_env<'a>(
        flag: &'a str,
        photos: &'a str,
        project: &'a str,
        evidence: &'a str,
        data_dir: &'a str,
        prefix: &'a str,
    ) -> DesktopQaEnv<'a> {
        DesktopQaEnv {
            qa_flag: Some(flag),
            photos: Some(photos),
            project: Some(project),
            evidence: Some(evidence),
            data_dir: Some(data_dir),
            prefix,
        }
    }

    fn unique_temp_dir(label: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "framepilot-qa-{}-{}-{}",
            label,
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("time")
                .as_nanos()
        ));
        fs::create_dir_all(&dir).expect("temp dir");
        dir
    }

    #[test]
    fn qa_gate_rejects_home_drive_root_relative_and_prefix_as_project() {
        let home = "/home/alex";
        let prefix = "/home/alex/.cache/framepilot-desktop-500-gui";
        let photos = format!("{prefix}/photos");
        let project = format!("{prefix}/project");
        let evidence = format!("{prefix}/evidence");
        let data = format!("{prefix}/data");

        assert!(
            resolve_desktop_qa(posix_env("1", home, &project, &evidence, &data, prefix)).is_none(),
            "HOME must not pass the prefix gate"
        );
        assert!(
            resolve_desktop_qa(posix_env(
                "1",
                r"C:\",
                r"C:\Users\runner\AppData\Local\framepilot-desktop-500-gui\project",
                r"C:\Users\runner\AppData\Local\framepilot-desktop-500-gui\evidence",
                r"C:\Users\runner\AppData\Local\framepilot-desktop-500-gui\data",
                r"C:\Users\runner\AppData\Local\framepilot-desktop-500-gui",
            ))
            .is_none(),
            r"C:\ must not pass the prefix gate"
        );
        assert!(
            resolve_desktop_qa(posix_env("1", "photos", &project, &evidence, &data, prefix))
                .is_none(),
            "relative photos must not pass"
        );
        assert!(
            resolve_desktop_qa(posix_env("1", &photos, prefix, &evidence, &data, prefix)).is_none(),
            "prefix as project root must not pass"
        );
    }

    #[test]
    fn qa_gate_accepts_absolute_siblings_under_prefix() {
        let prefix = "/home/alex/.cache/framepilot-desktop-500-gui";
        let payload = resolve_desktop_qa(posix_env(
            "1",
            &format!("{prefix}/photos"),
            &format!("{prefix}/project"),
            &format!("{prefix}/evidence"),
            &format!("{prefix}/data"),
            prefix,
        ))
        .expect("siblings under prefix");
        assert_eq!(payload.photos, format!("{prefix}/photos"));
        assert_eq!(payload.project, format!("{prefix}/project"));
        assert_eq!(payload.evidence, format!("{prefix}/evidence"));
    }

    #[test]
    fn qa_gate_accepts_windows_siblings_under_localappdata_prefix() {
        let prefix = r"C:\Users\runner\AppData\Local\framepilot-desktop-500-gui";
        let payload = resolve_desktop_qa(posix_env(
            "1",
            &format!(r"{prefix}\photos"),
            &format!(r"{prefix}\project"),
            &format!(r"{prefix}\evidence"),
            &format!(r"{prefix}\data"),
            prefix,
        ))
        .expect("windows siblings");
        assert!(payload.photos.ends_with(r"\photos"));
    }

    #[test]
    fn qa_gate_requires_flag_one_and_absolute_data_dir() {
        let prefix = "/home/alex/.cache/framepilot-desktop-500-gui";
        let photos = format!("{prefix}/photos");
        let project = format!("{prefix}/project");
        let evidence = format!("{prefix}/evidence");
        let data = format!("{prefix}/data");
        assert!(
            resolve_desktop_qa(posix_env("true", &photos, &project, &evidence, &data, prefix))
                .is_none()
        );
        assert!(
            resolve_desktop_qa(posix_env("1", &photos, &project, &evidence, "/var/tmp", prefix))
                .is_none()
        );
        assert!(resolve_desktop_qa(posix_env(
            "1",
            &format!("{prefix}/photos/../.."),
            &project,
            &evidence,
            &data,
            prefix,
        ))
        .is_none());
    }

    #[test]
    fn qa_write_evidence_denied_when_qa_off() {
        let dir = unique_temp_dir("deny");
        let dest = dir.join(MILESTONES_FILE);
        let line = r#"{"milestone":"idle","t":"2026-09-07T00:00:00Z"}"#;
        let err = write_qa_evidence_line(false, Some(&dest), line).expect_err("denied");
        assert!(
            err.contains("disabled"),
            "deny message should mention disabled: {err}"
        );
        assert!(!dest.exists());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn qa_write_evidence_rejects_newline_and_appends_jsonl() {
        let dir = unique_temp_dir("write");
        let dest = dir.join(MILESTONES_FILE);
        let ok = r#"{"milestone":"idle","t":"2026-09-07T00:00:00Z"}"#;
        write_qa_evidence_line(true, Some(&dest), ok).expect("write");
        write_qa_evidence_line(true, Some(&dest), r#"{"milestone":"done","t":"2026-09-07T00:00:01Z"}"#)
            .expect("second write");
        let text = fs::read_to_string(&dest).expect("read jsonl");
        assert!(text.contains("\"milestone\":\"idle\""));
        assert!(text.contains("\"milestone\":\"done\""));
        assert!(text.ends_with('\n'));
        assert!(write_qa_evidence_line(
            true,
            Some(&dest),
            "{\"milestone\":\"idle\",\"t\":\"a\nb\"}"
        )
        .is_err());
        assert!(write_qa_evidence_line(true, Some(&dest), "[{\"milestone\":\"idle\",\"t\":\"1\"}]")
            .is_err());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn default_capabilities_allow_qa_write_evidence_without_fs_or_shell() {
        let text = include_str!("../capabilities/default.json");
        assert!(
            text.contains("allow-qa-write-evidence"),
            "explicit ACL required: {text}"
        );
        assert!(!text.contains("fs:"));
        assert!(!text.contains("shell:"));
        let permission = include_str!("../permissions/qa.toml");
        assert!(permission.contains("identifier = \"allow-qa-write-evidence\""));
        assert!(permission.contains("qa_write_evidence"));
    }

    #[test]
    fn lib_registers_qa_write_evidence() {
        let lib = include_str!("lib.rs");
        assert!(lib.contains("mod qa;"));
        assert!(lib.contains("qa_write_evidence"));
        assert!(lib.contains("load_desktop_qa_state"));
    }

    #[test]
    fn qa_init_script_assignment_is_json() {
        let payload = DesktopQaPayload {
            photos: r"C:\Users\a\AppData\Local\framepilot-desktop-500-gui\photos".into(),
            project: r"C:\Users\a\AppData\Local\framepilot-desktop-500-gui\project".into(),
            evidence: r"C:\Users\a\AppData\Local\framepilot-desktop-500-gui\evidence".into(),
        };
        let assignment = qa_init_script_assignment(&payload).expect("json");
        assert!(assignment.contains("window.__FRAMEPILOT_DESKTOP_QA__ = "));
        assert!(assignment.contains(r"\\"));
    }
}
