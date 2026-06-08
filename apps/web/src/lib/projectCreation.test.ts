import test from "node:test";
import assert from "node:assert/strict";

import {
  normalizeProjectCreateDraft,
  projectCreateActionBlockMessage,
  projectCreationRecoveryHint,
  projectDataFolderHint,
} from "./projectCreation.ts";

test("explains why project creation is blocked", () => {
  assert.equal(
    projectCreateActionBlockMessage({ isCreating: true, name: "Portrait session" }),
    "Project creation is already running.",
  );
  assert.equal(
    projectCreateActionBlockMessage({ isCreating: false, name: "   " }),
    "Enter a project name before creating a project.",
  );
});

test("allows project creation when a trimmed name is present", () => {
  assert.equal(projectCreateActionBlockMessage({ isCreating: false, name: "  Portrait session  " }), "");
});

test("normalizes project creation drafts before submission", () => {
  assert.deepEqual(normalizeProjectCreateDraft({ name: "  Portrait session  ", rootPath: "   " }), {
    projectName: "Portrait session",
  });
  assert.deepEqual(
    normalizeProjectCreateDraft({
      name: "  Landscape selects  ",
      rootPath: "  /Users/name/Pictures/FramePilot landscape  ",
    }),
    {
      projectName: "Landscape selects",
      projectRootPath: "/Users/name/Pictures/FramePilot landscape",
    },
  );
});

test("describes local project data folder behavior", () => {
  assert.equal(
    projectDataFolderHint(""),
    "FramePilot will use its managed local data folder for copied originals, previews, caches, and exports.",
  );
  assert.equal(
    projectDataFolderHint("  /Users/name/Pictures/FramePilot session  "),
    "FramePilot will create copied originals, previews, caches, and exports in this local project folder.",
  );
});

test("explains how to recover from project creation failures", () => {
  assert.equal(
    projectCreationRecoveryHint(""),
    "Confirm the local FramePilot API is running, then try creating the project again.",
  );
  assert.equal(
    projectCreationRecoveryHint("  /Users/name/Pictures/FramePilot session  "),
    "Check that the local project data folder exists and is writable, or leave it blank to use FramePilot's managed local data folder.",
  );
});
