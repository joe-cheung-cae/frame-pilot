import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mock, test } from "node:test";

const invokeCalls: Array<{ cmd: string; args?: unknown }> = [];

mock.module("@tauri-apps/api/core", {
  namedExports: {
    async invoke(cmd: string, args?: unknown) {
      invokeCalls.push({ cmd, args });
    },
  },
});

const { DESKTOP_QA_IMPORT_BATCH_SIZE, readDesktopQaConfig, runDesktopQa } = await import("./desktopQaRunner.ts");

const runnerSource = readFileSync(new URL("./desktopQaRunner.ts", import.meta.url), "utf8");

type TestWindow = {
  __FRAMEPILOT_DESKTOP__?: unknown;
  __FRAMEPILOT_WINDOW__?: unknown;
  __FRAMEPILOT_DESKTOP_QA__?: unknown;
};

async function withWindow<T>(windowValue: TestWindow | undefined, run: () => T | Promise<T>): Promise<T> {
  const globalObject = globalThis as { window?: TestWindow };
  const hadWindow = Object.prototype.hasOwnProperty.call(globalThis, "window");
  const previous = globalObject.window;
  if (windowValue === undefined) {
    delete globalObject.window;
  } else {
    globalObject.window = windowValue;
  }
  try {
    return await run();
  } finally {
    if (hadWindow) {
      globalObject.window = previous;
    } else {
      delete globalObject.window;
    }
  }
}

test("runner module calls production registerDesktopProjectRoot and importPhotosFromPaths", () => {
  assert.match(runnerSource, /api\.registerDesktopProjectRoot/);
  assert.match(runnerSource, /api\.importPhotosFromPaths/);
  assert.match(runnerSource, /IMPORT_UPLOAD_BATCH_SIZE/);
  assert.equal(DESKTOP_QA_IMPORT_BATCH_SIZE, 100);
});

test("readDesktopQaConfig is a no-op without desktop main QA object", async () => {
  await withWindow(undefined, () => {
    assert.equal(readDesktopQaConfig(undefined), null);
  });
  await withWindow({ __FRAMEPILOT_DESKTOP__: true, __FRAMEPILOT_WINDOW__: "preview" }, () => {
    assert.equal(
      readDesktopQaConfig({
        __FRAMEPILOT_DESKTOP__: true,
        __FRAMEPILOT_WINDOW__: "preview",
        __FRAMEPILOT_DESKTOP_QA__: {
          photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
          project: "/home/a/.cache/framepilot-desktop-500-gui/project",
        },
      }),
      null,
    );
  });
  assert.equal(
    readDesktopQaConfig({
      __FRAMEPILOT_DESKTOP__: true,
      __FRAMEPILOT_WINDOW__: "main",
    }),
    null,
  );
  assert.deepEqual(
    readDesktopQaConfig({
      __FRAMEPILOT_DESKTOP__: true,
      __FRAMEPILOT_WINDOW__: "main",
      __FRAMEPILOT_DESKTOP_QA__: {
        photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
        project: "/home/a/.cache/framepilot-desktop-500-gui/project",
      },
    }),
    {
      photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
      project: "/home/a/.cache/framepilot-desktop-500-gui/project",
    },
  );
});

test("runDesktopQa calls registerDesktopProjectRoot and importPhotosFromPaths", async () => {
  const calls: string[] = [];
  const evidence: string[] = [];
  const fakeApi = {
    getHealth: async () => {
      calls.push("getHealth");
      return { status: "ok", version: "2.1.0-desktop", service: "framepilot-api" };
    },
    getSettings: async () => {
      calls.push("getSettings");
      return { import_workers: 1 };
    },
    registerDesktopProjectRoot: async (path: string) => {
      calls.push(`registerDesktopProjectRoot:${path}`);
      return { path };
    },
    createProject: async (name: string, rootPath?: string) => {
      calls.push(`createProject:${name}:${rootPath ?? ""}`);
      return { id: "proj-1" };
    },
    importPhotosFromPaths: async (projectId: string, paths: readonly string[]) => {
      calls.push(`importPhotosFromPaths:${projectId}:${paths.join(",")}`);
      return {
        accepted_files: 1,
        skipped_files: 0,
        expanded_total: 1,
        job: { id: "import-1", status: "complete" as const },
      };
    },
    processProject: async (projectId: string) => {
      calls.push(`processProject:${projectId}`);
      return { id: "process-1", status: "complete" as const, error_message: null };
    },
    getJob: async (projectId: string, jobId: string) => {
      calls.push(`getJob:${projectId}:${jobId}`);
      return { id: jobId, status: "complete" as const, job_type: "import", error_message: null };
    },
  };

  await runDesktopQa({
    api: fakeApi,
    writeEvidence: async (line) => {
      evidence.push(line);
    },
    push: (href) => {
      calls.push(`push:${href}`);
    },
    queryPreviewImages: () => [
      {
        src: "http://127.0.0.1:9/api/assets/proj-1/previews/a.webp",
        currentSrc: "http://127.0.0.1:9/api/assets/proj-1/previews/a.webp",
        complete: true,
        naturalWidth: 3000,
      },
    ],
    config: {
      photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
      project: "/home/a/.cache/framepilot-desktop-500-gui/project",
    },
    now: () => "2026-09-07T00:00:00.000Z",
    sleep: async () => {},
  });

  assert.equal(
    calls.includes("registerDesktopProjectRoot:/home/a/.cache/framepilot-desktop-500-gui/project"),
    true,
  );
  assert.equal(
    calls.includes(
      "importPhotosFromPaths:proj-1:/home/a/.cache/framepilot-desktop-500-gui/photos",
    ),
    true,
  );
  assert.equal(calls.includes("push:/projects/proj-1/cull"), true);
  assert.equal(evidence.some((line) => line.includes('"milestone":"idle"')), true);
  assert.equal(evidence.some((line) => line.includes('"milestone":"done"')), true);
  assert.equal(evidence.some((line) => line.includes('"milestone":"first_preview"')), true);
});
