import fs from "node:fs";
import test from "node:test";
import assert from "node:assert/strict";

import { copyForShell } from "./shellCopy.ts";

test("copyForShell(false) keeps current browser empty and recovery copy", () => {
  const copy = copyForShell(false);
  assert.equal(copy.chooseFolder, "Choose a folder");
  assert.equal(copy.projectListEmptyDetail, "Create a local project before importing photos.");
  assert.equal(
    copy.cullingEmptyImportDetail,
    "Import JPEG, PNG, WebP, HEIC/HEIF, or AVIF images before opening the culling workspace.",
  );
  assert.equal(
    copy.importLoadRetryHint,
    "Confirm the local FramePilot API is running, then choose the files again. Original source photos remain unchanged.",
  );
  assert.equal(
    copy.exportCopyPathRecovery,
    "The export path is still visible above. Select and copy it manually if browser clipboard access is blocked.",
  );
  assert.equal(copy.exportHistoryEmptyDetail, "No exports yet.");
});

test("copyForShell(true) uses native folder language and never says choose files in your browser", () => {
  const copy = copyForShell(true);
  assert.equal(copy.chooseFolder, "Choose a folder");
  assert.doesNotMatch(copy.chooseFolder, /Choose files in your browser/);
  assert.equal(copy.projectListEmptyDetail, "Create a local project, then choose a folder to import photos.");
  assert.equal(
    copy.cullingEmptyImportDetail,
    "Choose a folder of JPEG, PNG, WebP, HEIC/HEIF, or AVIF images before opening the culling workspace.",
  );
  assert.equal(
    copy.importLoadRetryHint,
    "Confirm the local FramePilot API is running, then choose a folder again. Original source photos remain unchanged.",
  );
  assert.equal(
    copy.exportCopyPathRecovery,
    "The export path is still visible above. Select and copy it manually if clipboard access is blocked.",
  );
  assert.equal(
    copy.exportHistoryEmptyDetail,
    "No exports yet. After you export, FramePilot reveals the folder instead of downloading a file.",
  );
  const blob = Object.values(copy).join("\n");
  assert.doesNotMatch(blob, /Choose files in your browser/);
});

test("import and export workflow helpers stay shell-agnostic", () => {
  const importSource = fs.readFileSync(new URL("./importWorkflow.ts", import.meta.url), "utf8");
  const exportSource = fs.readFileSync(new URL("./exportSelection.ts", import.meta.url), "utf8");
  assert.doesNotMatch(importSource, /shellCopy/);
  assert.doesNotMatch(exportSource, /shellCopy/);
  assert.doesNotMatch(importSource, /function importLoadRecoveryMessage\([^)]*desktop/);
  assert.doesNotMatch(exportSource, /function exportActionRecoveryMessage\([^)]*desktop/);
});

test("ImportPanel folder label and import-load hint come from the shell copy record", () => {
  const source = fs.readFileSync(new URL("../components/ImportPanel.tsx", import.meta.url), "utf8");
  assert.match(source, /copyForShell\((?:isDesktopShell\(\)|desktopShell)\)/);
  assert.match(source, /copy\.chooseFolder/);
  assert.match(source, /copy\.importLoadRetryHint/);
  assert.doesNotMatch(source, /<span className="font-medium">Choose a folder<\/span>/);
});

test("ProjectList, CullingWorkspace, and ExportPanel select copyForShell once", () => {
  const list = fs.readFileSync(new URL("../components/ProjectList.tsx", import.meta.url), "utf8");
  const cull = fs.readFileSync(new URL("../components/CullingWorkspace.tsx", import.meta.url), "utf8");
  const exp = fs.readFileSync(new URL("../components/ExportPanel.tsx", import.meta.url), "utf8");
  assert.match(list, /copyForShell\(isDesktopShell\(\)\)/);
  assert.match(list, /copy\.projectListEmptyDetail/);
  assert.match(cull, /copyForShell\(isDesktopShell\(\)\)/);
  assert.match(cull, /copy\.cullingEmptyImportDetail/);
  assert.match(exp, /copyForShell\((?:isDesktopShell\(\)|desktopShell)\)/);
  assert.match(exp, /copy\.exportCopyPathRecovery/);
  assert.match(exp, /copy\.exportHistoryEmptyDetail/);
});
