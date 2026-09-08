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
const QA_ALLOWED_MILESTONES: &[&str] = &[
    "host_window",
    "page_load",
    "spa_module",
    "spa_fetch",
    "spa_fetch_done",
    "spa_fetch_fail",
    "spa_flags",
    "qa_started",
    "qa_runner_mounted",
    "idle",
    "import_complete",
    "process_complete",
    "cull_push",
    "cull_workspace",
    "first_preview",
    "done",
    "fail",
];

#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
pub struct DesktopQaPayload {
    pub photos: String,
    pub project: String,
    pub evidence: String,
}

#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct DesktopQaBootstrap {
    pub photos: String,
    pub project: String,
    pub evidence: String,
    pub api_base: String,
}

#[derive(Debug, Clone)]
pub struct DesktopQaState {
    pub enabled: bool,
    pub evidence_path: Option<PathBuf>,
    pub payload: Option<DesktopQaPayload>,
    pub api_base: Option<String>,
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

fn is_allowed_qa_milestone(milestone: &str) -> bool {
    QA_ALLOWED_MILESTONES.contains(&milestone)
}

fn strip_windows_verbatim_prefix(raw: &str) -> String {
    const UNC_PREFIX: &str = r"\\?\UNC\";
    const VERBATIM_PREFIX: &str = r"\\?\";
    if let Some(rest) = raw.strip_prefix(UNC_PREFIX) {
        format!(r"\\{rest}")
    } else if let Some(rest) = raw.strip_prefix(VERBATIM_PREFIX) {
        rest.to_string()
    } else {
        raw.to_string()
    }
}

fn canonicalize_qa_path(raw: &str) -> Option<String> {
    let canonical = fs::canonicalize(raw).ok()?;
    let stripped = strip_windows_verbatim_prefix(canonical.to_str()?);
    if stripped.starts_with(r"\\.\") {
        return None;
    }
    Some(stripped)
}

fn confirm_canonical_qa_paths(
    photos: &str,
    project: &str,
    evidence: &str,
    data_dir: &str,
    prefix: &str,
) -> Option<DesktopQaPayload> {
    let prefix = canonicalize_qa_path(prefix)?;
    let photos = canonicalize_qa_path(photos)?;
    let project = canonicalize_qa_path(project)?;
    let evidence = canonicalize_qa_path(evidence)?;
    let data_dir = canonicalize_qa_path(data_dir)?;
    if !is_absolute_under_prefix(&photos, &prefix)
        || !is_absolute_under_prefix(&project, &prefix)
        || !is_absolute_under_prefix(&evidence, &prefix)
        || !is_absolute_under_prefix(&data_dir, &prefix)
    {
        return None;
    }
    if is_same_or_descendant(&data_dir, &project) {
        return None;
    }
    Some(DesktopQaPayload {
        photos,
        project,
        evidence,
    })
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
    let payload = resolve_desktop_qa(DesktopQaEnv {
        qa_flag: qa_flag.as_deref(),
        photos: photos.as_deref(),
        project: project.as_deref(),
        evidence: evidence.as_deref(),
        data_dir: data_dir.as_deref(),
        prefix: &prefix,
    })?;
    confirm_canonical_qa_paths(
        &payload.photos,
        &payload.project,
        &payload.evidence,
        data_dir.as_deref()?.trim(),
        &prefix,
    )
}

pub fn load_desktop_qa_state(api_base: Option<String>) -> DesktopQaState {
    match resolve_desktop_qa_from_env() {
        Some(payload) => DesktopQaState {
            enabled: true,
            evidence_path: Some(PathBuf::from(&payload.evidence).join(MILESTONES_FILE)),
            payload: Some(payload),
            api_base,
        },
        None => DesktopQaState {
            enabled: false,
            evidence_path: None,
            payload: None,
            api_base: None,
        },
    }
}

pub fn qa_bootstrap_payload(state: &DesktopQaState) -> Option<DesktopQaBootstrap> {
    if !state.enabled {
        return None;
    }
    let payload = state.payload.as_ref()?;
    let api_base = state.api_base.as_deref()?.trim();
    if api_base.is_empty() {
        return None;
    }
    Some(DesktopQaBootstrap {
        photos: payload.photos.clone(),
        project: payload.project.clone(),
        evidence: payload.evidence.clone(),
        api_base: api_base.to_string(),
    })
}

pub fn qa_init_script_assignment(payload: &DesktopQaPayload) -> Option<String> {
    let json = serde_json::to_string(payload).ok()?;
    Some(format!(
        "\nwindow.__FRAMEPILOT_DESKTOP_QA__ = {json};\ntry {{ void fetch(String(window.__FRAMEPILOT_API_BASE__) + \"/health?qa=init\"); }} catch (e) {{}}"
    ))
}

pub fn iso_utc_from_unix_secs(unix_secs: u64) -> String {
    let z = unix_secs as i64;
    let days = z.div_euclid(86400);
    let tod = z.rem_euclid(86400) as u32;
    let hh = tod / 3600;
    let mm = (tod % 3600) / 60;
    let ss = tod % 60;
    let z = days + 719468;
    let era = z.div_euclid(146097);
    let doe = (z - era * 146097) as u32;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe as i64 + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    format!("{y:04}-{m:02}-{d:02}T{hh:02}:{mm:02}:{ss:02}Z")
}

fn iso_utc_now() -> String {
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    iso_utc_from_unix_secs(secs)
}

pub fn write_host_milestone(state: &DesktopQaState, milestone: &str) -> Result<(), String> {
    if !state.enabled {
        return Ok(());
    }
    if milestone.is_empty() || milestone.contains('\n') || milestone.contains('\r') {
        return Err("qa host milestone is invalid".into());
    }
    let line = format!(
        "{{\"milestone\":{},\"t\":{}}}",
        serde_json::to_string(milestone).map_err(|err| err.to_string())?,
        serde_json::to_string(&iso_utc_now()).map_err(|err| err.to_string())?,
    );
    write_qa_evidence_line(true, state.evidence_path.as_deref(), &line)
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
    let milestone = match (obj.get("milestone"), obj.get("t")) {
        (Some(serde_json::Value::String(milestone)), Some(serde_json::Value::String(t)))
            if !milestone.is_empty() && !t.is_empty() =>
        {
            milestone.as_str()
        }
        _ => {
            return Err("qa evidence must include string milestone and t".into());
        }
    };
    if !is_allowed_qa_milestone(milestone) {
        return Err("qa evidence milestone is not allowlisted".into());
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

#[tauri::command]
pub fn qa_bootstrap(state: tauri::State<DesktopQaState>) -> Option<DesktopQaBootstrap> {
    qa_bootstrap_payload(&state)
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
    fn qa_write_evidence_rejects_unknown_milestone() {
        let dir = unique_temp_dir("unknown-ms");
        let dest = dir.join(MILESTONES_FILE);
        for milestone in ["unknown", "Idle", "DONE"] {
            let line = format!(r#"{{"milestone":"{milestone}","t":"2026-09-07T00:00:00Z"}}"#);
            let err = write_qa_evidence_line(true, Some(&dest), &line)
                .expect_err("unknown milestone");
            assert!(
                err.contains("allowlisted"),
                "reject message should mention allowlisted: {err}"
            );
        }
        assert!(!dest.exists(), "unknown milestone must not write dest");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn qa_write_evidence_accepts_all_allowlisted_milestones() {
        let dir = unique_temp_dir("allow-ms");
        let dest = dir.join(MILESTONES_FILE);
        for milestone in QA_ALLOWED_MILESTONES {
            let line = format!(r#"{{"milestone":"{milestone}","t":"2026-09-07T00:00:00Z"}}"#);
            write_qa_evidence_line(true, Some(&dest), &line).expect(milestone);
        }
        let text = fs::read_to_string(&dest).expect("read jsonl");
        for milestone in QA_ALLOWED_MILESTONES {
            assert!(
                text.contains(&format!(r#""milestone":"{milestone}""#)),
                "missing {milestone} in {text}"
            );
        }
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn strip_windows_verbatim_prefix_normalizes_extended_paths() {
        assert_eq!(
            strip_windows_verbatim_prefix(r"\\?\UNC\server\share\foo"),
            r"\\server\share\foo"
        );
        assert_eq!(
            strip_windows_verbatim_prefix(r"\\?\C:\Users\runner\AppData\Local\foo"),
            r"C:\Users\runner\AppData\Local\foo"
        );
        assert_eq!(
            strip_windows_verbatim_prefix("/home/alex/.cache/framepilot-desktop-500-gui"),
            "/home/alex/.cache/framepilot-desktop-500-gui"
        );
        assert_eq!(
            strip_windows_verbatim_prefix(r"C:\Users\runner\foo"),
            r"C:\Users\runner\foo"
        );
    }

    #[test]
    fn confirm_canonical_qa_paths_accepts_real_siblings_under_prefix() {
        let prefix = unique_temp_dir("canon-ok");
        let photos = prefix.join("photos");
        let project = prefix.join("project");
        let evidence = prefix.join("evidence");
        let data = prefix.join("data");
        for dir in [&photos, &project, &evidence, &data] {
            fs::create_dir_all(dir).expect("sibling");
        }
        let payload = confirm_canonical_qa_paths(
            photos.to_str().expect("photos utf8"),
            project.to_str().expect("project utf8"),
            evidence.to_str().expect("evidence utf8"),
            data.to_str().expect("data utf8"),
            prefix.to_str().expect("prefix utf8"),
        )
        .expect("real siblings under prefix");
        assert!(!payload.photos.contains(r"\\?\"));
        assert!(!payload.project.contains(r"\\?\"));
        assert!(!payload.evidence.contains(r"\\?\"));
        assert_eq!(
            payload.photos,
            canonicalize_qa_path(photos.to_str().expect("photos utf8")).expect("canon photos")
        );
        assert!(payload.photos.ends_with("photos"));
        let _ = fs::remove_dir_all(&prefix);
    }

    #[test]
    fn confirm_canonical_qa_paths_rejects_missing_path() {
        let prefix = unique_temp_dir("canon-miss");
        let photos = prefix.join("photos");
        let project = prefix.join("project");
        let evidence = prefix.join("evidence");
        let data = prefix.join("data");
        for dir in [&project, &evidence, &data] {
            fs::create_dir_all(dir).expect("sibling");
        }
        assert!(
            confirm_canonical_qa_paths(
                photos.to_str().expect("photos utf8"),
                project.to_str().expect("project utf8"),
                evidence.to_str().expect("evidence utf8"),
                data.to_str().expect("data utf8"),
                prefix.to_str().expect("prefix utf8"),
            )
            .is_none(),
            "missing photos must fail canonicalize"
        );
        let _ = fs::remove_dir_all(&prefix);
    }

    #[cfg(unix)]
    #[test]
    fn confirm_canonical_qa_paths_rejects_symlink_escape() {
        let prefix = unique_temp_dir("canon-link");
        let photos = prefix.join("photos");
        let project = prefix.join("project");
        let evidence = prefix.join("evidence");
        let data = prefix.join("data");
        for dir in [&project, &evidence, &data] {
            fs::create_dir_all(dir).expect("sibling");
        }
        let photos_s = photos.to_str().expect("photos utf8");
        let project_s = project.to_str().expect("project utf8");
        let evidence_s = evidence.to_str().expect("evidence utf8");
        let data_s = data.to_str().expect("data utf8");
        let prefix_s = prefix.to_str().expect("prefix utf8");

        std::os::unix::fs::symlink("/etc", &photos).expect("symlink /etc");
        assert!(
            confirm_canonical_qa_paths(photos_s, project_s, evidence_s, data_s, prefix_s).is_none(),
            "photos symlink to /etc must be rejected"
        );

        fs::remove_file(&photos).expect("remove /etc symlink");
        let home = std::env::var("HOME").expect("HOME");
        std::os::unix::fs::symlink(&home, &photos).expect("symlink HOME");
        assert!(
            confirm_canonical_qa_paths(photos_s, project_s, evidence_s, data_s, prefix_s).is_none(),
            "photos symlink to $HOME must be rejected"
        );
        let _ = fs::remove_dir_all(&prefix);
    }

    #[test]
    fn default_capabilities_allow_qa_write_evidence_without_fs_or_shell() {
        let text = include_str!("../capabilities/default.json");
        assert!(
            !text.contains("allow-qa-write-evidence"),
            "QA ACL must not be on default/preview: {text}"
        );
        assert!(!text.contains("fs:"));
        assert!(!text.contains("shell:"));
        let qa_text = include_str!("../capabilities/qa.json");
        assert!(
            qa_text.contains("allow-qa-write-evidence"),
            "explicit ACL required: {qa_text}"
        );
        assert!(qa_text.contains("\"main\""), "QA ACL is main-only: {qa_text}");
        assert!(
            !qa_text.contains("\"preview\""),
            "QA ACL must not include preview: {qa_text}"
        );
        assert!(!qa_text.contains("fs:"));
        assert!(!qa_text.contains("shell:"));
        let permission = include_str!("../permissions/qa.toml");
        assert!(permission.contains("identifier = \"allow-qa-write-evidence\""));
        assert!(permission.contains("qa_write_evidence"));
        assert!(
            permission.contains("qa_bootstrap"),
            "page JS must be allowed to read the fail-closed QA payload over IPC: {permission}"
        );
    }

    #[test]
    fn lib_registers_qa_write_evidence() {
        let lib = include_str!("lib.rs");
        assert!(lib.contains("mod qa;"));
        assert!(lib.contains("qa_write_evidence"));
        assert!(lib.contains("qa_bootstrap"));
        assert!(lib.contains("load_desktop_qa_state"));
        assert!(lib.contains("api_base_url(port)"));
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
        assert!(
            assignment.contains("/health?qa=init"),
            "init script must ping sidecar so a blank WebView is visible in access logs: {assignment}"
        );
    }

    #[test]
    fn iso_utc_from_unix_secs_is_rfc3339_z() {
        assert_eq!(iso_utc_from_unix_secs(0), "1970-01-01T00:00:00Z");
        assert_eq!(iso_utc_from_unix_secs(1_700_000_000), "2023-11-14T22:13:20Z");
    }

    #[test]
    fn write_host_milestone_noops_when_qa_off_and_appends_when_on() {
        let dir = unique_temp_dir("host");
        let dest = dir.join(MILESTONES_FILE);
        let off = DesktopQaState {
            enabled: false,
            evidence_path: Some(dest.clone()),
            payload: None,
            api_base: None,
        };
        write_host_milestone(&off, "host_window").expect("noop");
        assert!(!dest.exists());
        let on = DesktopQaState {
            enabled: true,
            evidence_path: Some(dest.clone()),
            payload: None,
            api_base: None,
        };
        write_host_milestone(&on, "host_window").expect("write");
        write_host_milestone(&on, "page_load").expect("write page_load");
        let text = fs::read_to_string(&dest).expect("read");
        assert!(text.contains("\"milestone\":\"host_window\""));
        assert!(text.contains("\"milestone\":\"page_load\""));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn lib_shows_main_window_and_records_qa_page_load() {
        let lib = include_str!("lib.rs");
        assert!(lib.contains("PageLoadEvent::Finished"));
        assert!(lib.contains("write_host_milestone"));
        assert!(lib.contains(".visible(true)"));
        assert!(lib.contains(".focused(true)"));
        assert!(lib.contains("always_on_top(true)"));
        assert!(lib.contains("window.show()"));
        assert!(lib.contains("window.set_focus()"));
    }

    #[test]
    fn desktop_main_reports_spa_module_when_the_bundle_runs() {
        let main = include_str!("../../src/main.tsx");
        assert!(
            main.contains("spa_module"),
            "packaged SPA must write spa_module so a blocked Vite bundle is visible in milestones.jsonl"
        );
        assert!(main.contains("qa_write_evidence"));
        assert!(
            main.contains("qa_bootstrap"),
            "packaged SPA must IPC-read QA payload; init-script window globals are not visible to page modules: {main}"
        );
        assert!(main.contains("spa_flags"));
        assert!(main.contains("applyDesktopQaBootstrap"));
        assert!(
            main.contains("startDesktopQaFromWindow"),
            "Path B must start from main.tsx so idle does not depend on React useEffect: {main}"
        );
        assert!(main.contains("spa_fetch"));
        let runner = include_str!("../../src/lib/desktopQaRunner.ts");
        assert!(
            runner.contains("setDesktopQaNavigate"),
            "cull navigation must use React Router, not history.pushState alone: {runner}"
        );
        assert!(runner.contains("__FRAMEPILOT_DESKTOP_QA_NAVIGATE__"));
        assert!(runner.contains("cull_push"));
        assert!(runner.contains("qa_runner_mounted"));
        assert!(runner.contains("cullLocationFields"));
        assert!(
            runner.contains("setDesktopQaCullHref"),
            "Path B must mount culling via an in-module store, not the WebView URL: {runner}"
        );
        assert!(
            runner.contains("setDesktopQaMountCull"),
            "Path B must call a window-registered React setState to mount CullingWorkspace: {runner}"
        );
        assert!(runner.contains("__FRAMEPILOT_DESKTOP_QA_MOUNT_CULL__"));
        assert!(
            runner.contains("mountQaCullingPreview"),
            "Path B must mount culling on a separate React root, not the live App tree: {runner}"
        );
        assert!(runner.contains("appendPreviewImage"));
        assert!(runner.contains("desktopQaCullMount"));
        assert!(runner.contains("cull_workspace"));
        let overlay = include_str!("../../src/lib/desktopQaCullMount.tsx");
        assert!(
            overlay.contains("createRoot"),
            "QA cull overlay must createRoot so App setState is not required: {overlay}"
        );
        assert!(overlay.contains("CullingWorkspace"));
        assert!(overlay.contains("MemoryRouter"));
        assert!(runner.contains("useSyncExternalStore"));
        assert!(runner.contains("parseCullProjectId"));
        assert!(
            runner.contains("__FRAMEPILOT_DESKTOP_QA_CULL_HREF__"),
            "Path B cull href must live on window so duplicated SPA modules share it: {runner}"
        );
        assert!(runner.contains("framepilot-qa-cull-href"));
        let app = include_str!("../../src/App.tsx");
        assert!(
            app.contains("setDesktopQaNavigate"),
            "NativeMenuListener must register React navigate on window: {app}"
        );
        assert!(
            app.contains("setDesktopQaMountCull"),
            "CullOverlay must register React setState on window during render: {app}"
        );
        assert!(app.contains("flushSync"));
        assert!(app.contains("CullingWorkspace"));
        assert!(app.contains("CullOverlay"));
        assert!(app.contains("MemoryRouter"));
        assert!(!app.contains("BrowserRouter"));
        assert!(!app.contains("HashRouter"));
    }

    #[test]
    fn qa_bootstrap_payload_is_none_when_gate_is_off() {
        let payload = DesktopQaPayload {
            photos: "/home/alex/.cache/framepilot-desktop-500-gui/photos".into(),
            project: "/home/alex/.cache/framepilot-desktop-500-gui/project".into(),
            evidence: "/home/alex/.cache/framepilot-desktop-500-gui/evidence".into(),
        };
        let off = DesktopQaState {
            enabled: false,
            evidence_path: None,
            payload: Some(payload.clone()),
            api_base: Some("http://127.0.0.1:4242".into()),
        };
        assert!(qa_bootstrap_payload(&off).is_none());
        let missing_base = DesktopQaState {
            enabled: true,
            evidence_path: None,
            payload: Some(payload.clone()),
            api_base: None,
        };
        assert!(qa_bootstrap_payload(&missing_base).is_none());
        let on = DesktopQaState {
            enabled: true,
            evidence_path: None,
            payload: Some(payload),
            api_base: Some("http://127.0.0.1:4242".into()),
        };
        let boot = qa_bootstrap_payload(&on).expect("enabled QA state returns bootstrap");
        assert_eq!(
            boot.photos,
            "/home/alex/.cache/framepilot-desktop-500-gui/photos"
        );
        assert_eq!(
            boot.project,
            "/home/alex/.cache/framepilot-desktop-500-gui/project"
        );
        assert_eq!(boot.api_base, "http://127.0.0.1:4242");
    }

    #[test]
    fn tauri_csp_allows_custom_protocol_scripts() {
        let conf = include_str!("../tauri.conf.json");
        assert!(conf.contains("customprotocol:"));
        assert!(conf.contains("http://tauri.localhost"));
        assert!(conf.contains("tauri:"));
    }
}
