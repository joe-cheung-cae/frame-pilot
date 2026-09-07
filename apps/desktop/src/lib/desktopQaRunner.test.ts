import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mock, test } from "node:test";

const invokeCalls: Array<{ cmd: string; args?: unknown }> = [];
let invokeImpl: (cmd: string, args?: unknown) => Promise<unknown> = async () => undefined;

mock.module("@tauri-apps/api/core", {
  namedExports: {
    async invoke(cmd: string, args?: unknown) {
      invokeCalls.push({ cmd, args });
      return invokeImpl(cmd, args);
    },
  },
});

const {
  DESKTOP_QA_IMPORT_BATCH_SIZE,
  applyDesktopQaBootstrap,
  parseDesktopQaBootstrap,
  qaFailLine,
  readDesktopQaConfig,
  runDesktopQa,
  setDesktopQaNavigate,
  spaFlagsLine,
  startDesktopQaFromWindow,
  withTimeout,
} = await import("./desktopQaRunner.ts");

const runnerSource = readFileSync(new URL("./desktopQaRunner.ts", import.meta.url), "utf8");

type TestWindow = {
  __FRAMEPILOT_DESKTOP__?: unknown;
  __FRAMEPILOT_WINDOW__?: unknown;
  __FRAMEPILOT_DESKTOP_QA__?: unknown;
  __FRAMEPILOT_API_BASE__?: unknown;
  __FRAMEPILOT_DESKTOP_QA_STARTED__?: unknown;
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
  assert.match(runnerSource, /qaFailLine/);
  assert.match(runnerSource, /invoke\("qa_bootstrap"\)/);
  assert.match(runnerSource, /startDesktopQaFromWindow/);
  assert.match(runnerSource, /qa_started/);
  assert.match(runnerSource, /setDesktopQaNavigate/);
  assert.match(runnerSource, /cull_push/);
  assert.equal(DESKTOP_QA_IMPORT_BATCH_SIZE, 100);
});

test("qaFailLine is a single JSON object with milestone fail", () => {
  const line = qaFailLine("2026-09-07T13:55:50.000Z", new Error("culling preview img did not reach naturalWidth > 0"));
  assert.equal(line.includes("\n"), false);
  const parsed = JSON.parse(line) as { milestone: string; t: string; fail_reason: string };
  assert.equal(parsed.milestone, "fail");
  assert.equal(parsed.t, "2026-09-07T13:55:50.000Z");
  assert.match(parsed.fail_reason, /naturalWidth/);
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

test("parseDesktopQaBootstrap requires photos, project, and api_base", () => {
  assert.equal(parseDesktopQaBootstrap(null), null);
  assert.equal(parseDesktopQaBootstrap({ photos: "/p", project: "/j" }), null);
  assert.deepEqual(
    parseDesktopQaBootstrap({
      photos: " /home/a/.cache/framepilot-desktop-500-gui/photos ",
      project: "/home/a/.cache/framepilot-desktop-500-gui/project",
      evidence: "/home/a/.cache/framepilot-desktop-500-gui/evidence",
      api_base: "http://127.0.0.1:18000",
    }),
    {
      photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
      project: "/home/a/.cache/framepilot-desktop-500-gui/project",
      evidence: "/home/a/.cache/framepilot-desktop-500-gui/evidence",
      api_base: "http://127.0.0.1:18000",
    },
  );
});

test("applyDesktopQaBootstrap makes isolated page globals readable by readDesktopQaConfig", () => {
  const win: TestWindow = {};
  assert.equal(readDesktopQaConfig(win), null);
  assert.equal(
    applyDesktopQaBootstrap(win, {
      photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
      project: "/home/a/.cache/framepilot-desktop-500-gui/project",
      evidence: "/home/a/.cache/framepilot-desktop-500-gui/evidence",
      api_base: "http://127.0.0.1:18000",
    }),
    true,
  );
  assert.equal(win.__FRAMEPILOT_DESKTOP__, true);
  assert.equal(win.__FRAMEPILOT_WINDOW__, "main");
  assert.equal(win.__FRAMEPILOT_API_BASE__, "http://127.0.0.1:18000");
  assert.deepEqual(readDesktopQaConfig(win), {
    photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
    project: "/home/a/.cache/framepilot-desktop-500-gui/project",
  });
  assert.equal(
    applyDesktopQaBootstrap(
      { __FRAMEPILOT_WINDOW__: "preview" },
      {
        photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
        project: "/home/a/.cache/framepilot-desktop-500-gui/project",
        api_base: "http://127.0.0.1:18000",
      },
    ),
    false,
  );
});

test("spaFlagsLine records whether IPC bootstrap applied page globals", () => {
  const line = spaFlagsLine("2026-09-07T15:08:40.000Z", undefined, false);
  assert.equal(line.includes("\n"), false);
  const parsed = JSON.parse(line) as {
    milestone: string;
    desktop: boolean;
    qa: boolean;
    api_base: boolean;
    resolved_base: string;
    bootstrapped: boolean;
  };
  assert.equal(parsed.milestone, "spa_flags");
  assert.equal(parsed.desktop, false);
  assert.equal(parsed.qa, false);
  assert.equal(parsed.api_base, false);
  assert.equal(typeof parsed.resolved_base, "string");
  assert.equal(parsed.bootstrapped, false);
});

test("withTimeout rejects when the promise never settles", async () => {
  await assert.rejects(
    () => withTimeout(new Promise(() => undefined), 20, "GET /api/health timed out after 15s"),
    /timed out after 15s/,
  );
});

test("runDesktopQa calls registerDesktopProjectRoot and importPhotosFromPaths", async () => {
  setDesktopQaNavigate(null);
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

  assert.equal(calls.includes("registerDesktopProjectRoot:/home/a/.cache/framepilot-desktop-500-gui/project"), true);
  assert.equal(calls.includes("importPhotosFromPaths:proj-1:/home/a/.cache/framepilot-desktop-500-gui/photos"), true);
  assert.equal(calls.includes("push:/projects/proj-1/cull"), true);
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"idle"')),
    true,
  );
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"cull_push"')),
    true,
  );
  assert.equal(
    evidence.some((line) => line.includes('"via":"history"')),
    true,
  );
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"done"')),
    true,
  );
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"first_preview"')),
    true,
  );
});

test("runDesktopQa pushes cull through the registered React navigate", async () => {
  const calls: string[] = [];
  const evidence: string[] = [];
  setDesktopQaNavigate((href) => {
    calls.push(`react:${href}`);
  });
  const fakeApi = {
    getHealth: async () => ({ status: "ok", version: "2.1.0-desktop", service: "framepilot-api" }),
    getSettings: async () => ({ import_workers: 1 }),
    registerDesktopProjectRoot: async (path: string) => ({ path }),
    createProject: async () => ({ id: "proj-1" }),
    importPhotosFromPaths: async () => ({
      accepted_files: 1,
      skipped_files: 0,
      expanded_total: 1,
      job: { id: "import-1", status: "complete" as const },
    }),
    processProject: async () => ({ id: "process-1", status: "complete" as const, error_message: null }),
    getJob: async (_projectId: string, jobId: string) => ({
      id: jobId,
      status: "complete" as const,
      job_type: "import",
      error_message: null,
    }),
  };
  try {
    await runDesktopQa({
      api: fakeApi,
      writeEvidence: async (line) => {
        evidence.push(line);
      },
      push: (href) => {
        calls.push(`history:${href}`);
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
  } finally {
    setDesktopQaNavigate(null);
  }
  assert.equal(calls.includes("react:/projects/proj-1/cull"), true);
  assert.equal(calls.includes("history:/projects/proj-1/cull"), false);
  assert.equal(
    evidence.some((line) => line.includes('"via":"react"')),
    true,
  );
});

test("startDesktopQaFromWindow bootstraps QA flags via qa_bootstrap when init-script globals are missing", async () => {
  invokeCalls.length = 0;
  invokeImpl = async (cmd: string) => {
    if (cmd === "qa_bootstrap") {
      return {
        photos: "/home/a/.cache/framepilot-desktop-500-gui/photos",
        project: "/home/a/.cache/framepilot-desktop-500-gui/project",
        evidence: "/home/a/.cache/framepilot-desktop-500-gui/evidence",
        api_base: "http://127.0.0.1:18000",
      };
    }
    return undefined;
  };
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

  try {
    await withWindow({}, async () => {
      const win = (globalThis as { window: TestWindow }).window;
      const started = await startDesktopQaFromWindow({
        win,
        api: fakeApi,
        writeEvidence: async (line) => {
          evidence.push(line);
        },
        push: (href) => {
          calls.push(`push:${href}`);
        },
        queryPreviewImages: () => [
          {
            src: "http://127.0.0.1:18000/api/assets/proj-1/previews/a.webp",
            currentSrc: "http://127.0.0.1:18000/api/assets/proj-1/previews/a.webp",
            complete: true,
            naturalWidth: 3000,
          },
        ],
        now: () => "2026-09-07T00:00:00.000Z",
        sleep: async () => {},
      });
      assert.equal(started, true);
      assert.equal(win.__FRAMEPILOT_API_BASE__, "http://127.0.0.1:18000");
      assert.equal(win.__FRAMEPILOT_DESKTOP_QA_STARTED__, true);
      const again = await startDesktopQaFromWindow({
        win,
        api: fakeApi,
        writeEvidence: async () => undefined,
        push: () => undefined,
        queryPreviewImages: () => [],
        now: () => "2026-09-07T00:00:00.000Z",
        sleep: async () => {},
      });
      assert.equal(again, false);
    });
  } finally {
    invokeImpl = async () => undefined;
  }

  assert.equal(
    invokeCalls.some((call) => call.cmd === "qa_bootstrap"),
    true,
  );
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"qa_started"')),
    true,
  );
  assert.equal(calls.includes("getHealth"), true);
  assert.equal(calls.includes("registerDesktopProjectRoot:/home/a/.cache/framepilot-desktop-500-gui/project"), true);
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"idle"')),
    true,
  );
});

test("startDesktopQaFromWindow is a no-op on the preview window", async () => {
  const started = await startDesktopQaFromWindow({
    win: { __FRAMEPILOT_WINDOW__: "preview" },
    push: () => undefined,
  });
  assert.equal(started, false);
});
