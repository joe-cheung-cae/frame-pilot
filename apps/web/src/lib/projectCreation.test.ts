import test from "node:test";
import assert from "node:assert/strict";

import {
  NONEMPTY_PROJECT_ROOT_API_DETAIL,
  NONEMPTY_PROJECT_ROOT_CONFIRM,
  createProjectWithNonemptyConfirm,
  normalizeProjectCreateDraft,
  projectCreateActionBlockMessage,
  projectCreationRecoveryHint,
  projectDataFolderHint,
  registerPickedProjectRoot,
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

test("uses the exact nonempty-folder confirmation copy", () => {
  assert.equal(
    NONEMPTY_PROJECT_ROOT_CONFIRM,
    "This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?",
  );
});

test("sends acknowledgeNonempty only after the user confirms a nonempty root", async () => {
  const calls: { name: string; rootPath?: string; options?: { acknowledgeNonempty?: boolean } }[] = [];
  const created = await createProjectWithNonemptyConfirm(
    { projectName: "Portrait session", projectRootPath: "/picked/folder" },
    {
      createProject: async (name, rootPath, options) => {
        calls.push({ name, rootPath, options });
        if (!options?.acknowledgeNonempty) {
          throw new Error(NONEMPTY_PROJECT_ROOT_API_DETAIL);
        }
        return { id: "project-1" };
      },
      confirmNonempty: (message) => {
        assert.equal(message, NONEMPTY_PROJECT_ROOT_CONFIRM);
        return true;
      },
    },
  );

  assert.deepEqual(created, { id: "project-1" });
  assert.deepEqual(calls, [
    { name: "Portrait session", rootPath: "/picked/folder", options: undefined },
    { name: "Portrait session", rootPath: "/picked/folder", options: { acknowledgeNonempty: true } },
  ]);
});

test("does not send acknowledgeNonempty when nonempty confirmation is declined", async () => {
  const calls: { options?: { acknowledgeNonempty?: boolean } }[] = [];
  await assert.rejects(
    () =>
      createProjectWithNonemptyConfirm(
        { projectName: "Portrait session", projectRootPath: "/picked/folder" },
        {
          createProject: async (_name, _rootPath, options) => {
            calls.push({ options });
            throw new Error(NONEMPTY_PROJECT_ROOT_API_DETAIL);
          },
          confirmNonempty: () => false,
        },
      ),
    { message: NONEMPTY_PROJECT_ROOT_API_DETAIL },
  );
  assert.equal(calls.length, 1);
  assert.equal(calls[0]?.options, undefined);
});

test("surfaces other create errors verbatim without asking to acknowledge nonempty", async () => {
  let confirmed = false;
  await assert.rejects(
    () =>
      createProjectWithNonemptyConfirm(
        { projectName: "Portrait session", projectRootPath: "/picked/folder" },
        {
          createProject: async () => {
            throw new Error("Project root path must stay under the FramePilot data directory");
          },
          confirmNonempty: () => {
            confirmed = true;
            return true;
          },
        },
      ),
    { message: "Project root path must stay under the FramePilot data directory" },
  );
  assert.equal(confirmed, false);
});

test("registers a picked directory before filling root_path", async () => {
  const registered = await registerPickedProjectRoot({
    pickDirectory: async () => "/picked/folder",
    registerRoot: async (path) => ({ path: `${path}-registered` }),
  });
  assert.equal(registered, "/picked/folder-registered");
});

test("does not register a project root when the directory picker is cancelled", async () => {
  let registered = false;
  const result = await registerPickedProjectRoot({
    pickDirectory: async () => null,
    registerRoot: async () => {
      registered = true;
      return { path: "/should-not-register" };
    },
  });
  assert.equal(result, null);
  assert.equal(registered, false);
});

test("surfaces register errors from the native picker flow verbatim", async () => {
  await assert.rejects(
    () =>
      registerPickedProjectRoot({
        pickDirectory: async () => "/picked/folder",
        registerRoot: async () => {
          throw new Error("Project root path cannot target a system directory");
        },
      }),
    { message: "Project root path cannot target a system directory" },
  );
});
