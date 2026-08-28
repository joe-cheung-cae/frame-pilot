export type ShellCopy = {
  chooseFolder: string;
  cullingEmptyImportDetail: string;
  exportCopyPathRecovery: string;
  exportHistoryEmptyDetail: string;
  importLoadRetryHint: string;
  projectListEmptyDetail: string;
};

const BROWSER_COPY: ShellCopy = {
  chooseFolder: "Choose a folder",
  cullingEmptyImportDetail: "Import JPEG, PNG, or WebP images before opening the culling workspace.",
  exportCopyPathRecovery:
    "The export path is still visible above. Select and copy it manually if browser clipboard access is blocked.",
  exportHistoryEmptyDetail: "No exports yet.",
  importLoadRetryHint:
    "Confirm the local FramePilot API is running, then choose the files again. Original source photos remain unchanged.",
  projectListEmptyDetail: "Create a local project before importing photos.",
};

const DESKTOP_COPY: ShellCopy = {
  chooseFolder: "Choose a folder",
  cullingEmptyImportDetail: "Choose a folder of JPEG, PNG, or WebP images before opening the culling workspace.",
  exportCopyPathRecovery:
    "The export path is still visible above. Select and copy it manually if clipboard access is blocked.",
  exportHistoryEmptyDetail: "No exports yet. After you export, FramePilot reveals the folder instead of downloading a file.",
  importLoadRetryHint:
    "Confirm the local FramePilot API is running, then choose a folder again. Original source photos remain unchanged.",
  projectListEmptyDetail: "Create a local project, then choose a folder to import photos.",
};

export function copyForShell(desktop: boolean): ShellCopy {
  return desktop ? DESKTOP_COPY : BROWSER_COPY;
}
