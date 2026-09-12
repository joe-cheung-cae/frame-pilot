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
  parseDesktopQaMode,
  qaFailLine,
  readDesktopQaConfig,
  readQuitDialog,
  clickQuitDialogChoice,
  jobStatusIsActive,
  runDesktopQa,
  runDesktopQaQuitMatrix,
  cullLocationFields,
  getDesktopQaCullHref,
  hashPush,
  historyPush,
  locationShowsCull,
  parseCullProjectId,
  readDesktopQaRoute,
  routeShowsCull,
  appendPreviewImage,
  setDesktopQaCullHref,
  setDesktopQaMountCull,
  setDesktopQaNavigate,
  setDesktopQaRoute,
  subscribeDesktopQaCull,
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
  __FRAMEPILOT_DESKTOP_QA_ROUTE__?: string;
  __FRAMEPILOT_DESKTOP_QA_CULL_HREF__?: string;
  __FRAMEPILOT_DESKTOP_QA_SET_CULL_PROJECT_ID__?: ((projectId: string | null) => void) | null;
  location?: { pathname: string; hash: string };
  dispatchEvent?: (event: Event) => boolean;
  addEventListener?: (type: string, listener: (event: Event) => void) => void;
  removeEventListener?: (type: string, listener: (event: Event) => void) => void;
};

function fakeQaWindow(extra: Partial<TestWindow> = {}): TestWindow {
  const listeners = new Map<string, Set<(event: Event) => void>>();
  return {
    location: { pathname: "/", hash: "" },
    addEventListener(type, listener) {
      const set = listeners.get(type) ?? new Set();
      set.add(listener);
      listeners.set(type, set);
    },
    removeEventListener(type, listener) {
      listeners.get(type)?.delete(listener);
    },
    dispatchEvent(event) {
      const type = (event as { type?: string }).type ?? "";
      for (const listener of listeners.get(type) ?? []) {
        listener(event);
      }
      return true;
    },
    ...extra,
  };
}

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
  assert.match(runnerSource, /__FRAMEPILOT_DESKTOP_QA_NAVIGATE__/);
  assert.match(runnerSource, /qa_runner_mounted/);
  assert.match(runnerSource, /cull_push/);
  assert.match(runnerSource, /framepilot-qa-navigate/);
  assert.match(runnerSource, /setDesktopQaCullHref/);
  assert.match(runnerSource, /setDesktopQaMountCull/);
  assert.match(runnerSource, /__FRAMEPILOT_DESKTOP_QA_MOUNT_CULL__/);
  assert.match(runnerSource, /__FRAMEPILOT_DESKTOP_QA_SET_CULL_PROJECT_ID__/);
  assert.match(runnerSource, /mountQaCullingPreview/);
  assert.match(runnerSource, /appendPreviewImage/);
  assert.match(runnerSource, /desktopQaCullMount/);
  assert.match(runnerSource, /cull_workspace/);
  assert.match(runnerSource, /useSyncExternalStore/);
  assert.match(runnerSource, /parseCullProjectId/);
  assert.match(runnerSource, /__FRAMEPILOT_DESKTOP_QA_CULL_HREF__/);
  assert.match(runnerSource, /framepilot-qa-cull-href/);
  assert.match(runnerSource, /cullLocationFields/);
  assert.match(runnerSource, /invoke\("qa_request_close"\)/);
  assert.match(runnerSource, /close_requested/);
  assert.equal(runnerSource.includes("1500"), false);
  assert.equal(DESKTOP_QA_IMPORT_BATCH_SIZE, 100);
  const appSource = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");
  assert.match(appSource, /MemoryRouter/);
  assert.match(appSource, /CullingWorkspace/);
  assert.match(appSource, /setDesktopQaMountCull/);
  assert.match(appSource, /flushSync/);
  assert.match(appSource, /CullOverlay/);
  assert.match(appSource, /TAKE_MENU_COMMAND/);
  const menuSource = readFileSync(new URL("./nativeMenu.ts", import.meta.url), "utf8");
  assert.match(menuSource, /allow-take-menu-command/);
  assert.equal(appSource.includes("BrowserRouter"), false);
  assert.equal(appSource.includes("HashRouter"), false);
  assert.equal(appSource.includes("useSyncExternalStore"), false);
});

test("setDesktopQaCullHref notifies subscribers with the cull project id", () => {
  const seen: string[] = [];
  const unsubscribe = subscribeDesktopQaCull(() => {
    seen.push(getDesktopQaCullHref());
  });
  try {
    setDesktopQaCullHref("");
    assert.equal(parseCullProjectId("/projects/proj-1/cull"), "proj-1");
    assert.equal(parseCullProjectId("/projects/proj-1/process"), null);
    setDesktopQaCullHref("/projects/proj-1/cull");
    assert.equal(getDesktopQaCullHref(), "/projects/proj-1/cull");
    assert.equal(seen.includes("/projects/proj-1/cull"), true);
  } finally {
    unsubscribe();
    setDesktopQaCullHref("");
  }
});

test("setDesktopQaCullHref calls window-registered React setState with the cull project id", async () => {
  const seen: Array<string | null> = [];
  const win = fakeQaWindow({
    __FRAMEPILOT_DESKTOP_QA_SET_CULL_PROJECT_ID__: (id) => {
      seen.push(id);
    },
  });
  await withWindow(win, () => {
    setDesktopQaCullHref("/projects/proj-1/cull");
    assert.deepEqual(seen, ["proj-1"]);
    assert.equal(win.__FRAMEPILOT_DESKTOP_QA_CULL_HREF__, "/projects/proj-1/cull");
    setDesktopQaCullHref("");
  });
});

test("setDesktopQaCullHref shares the cull href through window for duplicated modules", async () => {
  const win = fakeQaWindow();
  await withWindow(win, () => {
    const seen: string[] = [];
    const unsubscribe = subscribeDesktopQaCull(() => {
      seen.push(getDesktopQaCullHref());
    });
    try {
      setDesktopQaCullHref("/projects/proj-1/cull");
      assert.equal(win.__FRAMEPILOT_DESKTOP_QA_CULL_HREF__, "/projects/proj-1/cull");
      assert.equal(getDesktopQaCullHref(), "/projects/proj-1/cull");
      assert.equal(seen.includes("/projects/proj-1/cull"), true);
    } finally {
      unsubscribe();
      setDesktopQaCullHref("");
    }
  });
});

test("routeShowsCull reads MemoryRouter pathname written during render", async () => {
  assert.equal(routeShowsCull("/projects/p/cull", "/"), false);
  assert.equal(routeShowsCull("/projects/p/cull", "/projects/p/cull"), true);
  assert.deepEqual(cullLocationFields(undefined), { pathname: "", hash: "" });
  assert.equal(locationShowsCull("/projects/p/cull", { pathname: "/", hash: "" }), false);
  assert.equal(locationShowsCull("/projects/p/cull", { pathname: "/projects/p/cull", hash: "" }), true);
  await withWindow({ location: { pathname: "/", hash: "" } }, () => {
    setDesktopQaRoute("/projects/p/cull");
    assert.equal(readDesktopQaRoute(), "/projects/p/cull");
    assert.equal(routeShowsCull("/projects/p/cull"), true);
  });
});

test("historyPush writes the cull route into location.hash when React navigate is missing", async () => {
  const loc = { pathname: "/index.html", hash: "" };
  await withWindow(
    {
      location: loc,
      dispatchEvent: () => true,
    },
    () => {
      setDesktopQaNavigate(null);
      historyPush("/projects/proj-1/cull");
      assert.equal(loc.hash, "#/projects/proj-1/cull");
      hashPush("/projects/proj-1/cull");
      assert.equal(loc.hash, "#/projects/proj-1/cull");
    },
  );
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
      mode: "cull",
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
      mode: "cull",
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
    mode: "cull",
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
  setDesktopQaMountCull(null);
  setDesktopQaCullHref("");
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
      mode: "cull",
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
    evidence.some((line) => line.includes('"via":"store"')),
    true,
  );
  assert.equal(
    evidence.some((line) => line.includes('"cull_project_id":"proj-1"')),
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
  await withWindow({ location: { pathname: "/", hash: "" }, dispatchEvent: () => true }, async () => {
    setDesktopQaRoute("/");
    setDesktopQaNavigate((href) => {
      calls.push(`react:${href}`);
      setDesktopQaRoute(href);
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
          mode: "cull",
        },
        now: () => "2026-09-07T00:00:00.000Z",
        sleep: async () => {},
      });
    } finally {
      setDesktopQaNavigate(null);
      setDesktopQaMountCull(null);
      setDesktopQaCullHref("");
    }
  });
  assert.equal(calls.includes("react:/projects/proj-1/cull"), true);
  assert.equal(calls.includes("history:/projects/proj-1/cull"), false);
  const cullPush = evidence
    .map((line) => JSON.parse(line) as { milestone?: string; via?: string; cull_project_id?: string })
    .find((line) => line.milestone === "cull_push");
  assert.equal(cullPush?.via, "store");
  assert.equal(cullPush?.cull_project_id, "proj-1");
});

test("runDesktopQa mounts CullingWorkspace through the window-registered setState", async () => {
  const mounted: string[] = [];
  const evidence: string[] = [];
  await withWindow({ location: { pathname: "/", hash: "" }, dispatchEvent: () => true }, async () => {
    setDesktopQaMountCull((projectId) => {
      mounted.push(projectId);
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
        push: () => undefined,
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
          mode: "cull",
        },
        now: () => "2026-09-07T00:00:00.000Z",
        sleep: async () => {},
      });
    } finally {
      setDesktopQaMountCull(null);
      setDesktopQaCullHref("");
    }
  });
  assert.equal(mounted.includes("proj-1"), true);
  const cullPush = evidence
    .map((line) => JSON.parse(line) as { milestone?: string; via?: string; cull_project_id?: string })
    .find((line) => line.milestone === "cull_push");
  assert.equal(cullPush?.via, "mount");
  assert.equal(cullPush?.cull_project_id, "proj-1");
});

test("appendPreviewImage inserts a /previews/ img into document.body", () => {
  const created: Array<{ src: string; alt: string }> = [];
  const body = {
    appendChild(node: { src: string; alt: string }) {
      created.push(node);
      return node;
    },
  };
  const previousDocument = (globalThis as { document?: unknown }).document;
  (globalThis as { document: unknown }).document = {
    body,
    createElement(tag: string) {
      assert.equal(tag, "img");
      return { src: "", alt: "", setAttribute() {} };
    },
  };
  try {
    assert.equal(appendPreviewImage("http://127.0.0.1:9/api/assets/proj-1/thumbnails/a.webp"), false);
    assert.equal(appendPreviewImage("http://127.0.0.1:9/api/assets/proj-1/previews/a.webp"), true);
    assert.equal(created.length, 1);
    assert.equal(created[0]?.src, "http://127.0.0.1:9/api/assets/proj-1/previews/a.webp");
    assert.equal(created[0]?.alt, "framepilot-qa-preview");
  } finally {
    if (previousDocument === undefined) {
      delete (globalThis as { document?: unknown }).document;
    } else {
      (globalThis as { document: unknown }).document = previousDocument;
    }
  }
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
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"done"')),
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

test("parseDesktopQaMode accepts quit-matrix modes and defaults to cull", () => {
  assert.equal(parseDesktopQaMode("quit-clean"), "quit-clean");
  assert.equal(parseDesktopQaMode("quit-import"), "quit-import");
  assert.equal(parseDesktopQaMode("quit-processing"), "quit-processing");
  assert.equal(parseDesktopQaMode("quit-export"), "quit-export");
  assert.equal(parseDesktopQaMode("cull"), "cull");
  assert.equal(parseDesktopQaMode("other"), "cull");
  assert.equal(parseDesktopQaMode(undefined), "cull");
});

test("jobStatusIsActive is true only for queued running interrupted", () => {
  assert.equal(jobStatusIsActive("queued"), true);
  assert.equal(jobStatusIsActive("running"), true);
  assert.equal(jobStatusIsActive("interrupted"), true);
  assert.equal(jobStatusIsActive("complete"), false);
  assert.equal(jobStatusIsActive("cancelled"), false);
});

test("readQuitDialog and clickQuitDialogChoice read #framepilot-quit-dialog", () => {
  const clicks: string[] = [];
  const overlay = {
    querySelector(selector: string) {
      if (selector === "h2") {
        return { textContent: "Import is still running" };
      }
      return null;
    },
    querySelectorAll() {
      return [
        { getAttribute: () => "stay" },
        { getAttribute: () => "cancel_and_quit" },
        { getAttribute: () => "quit_anyway" },
      ];
    },
  };
  const root = {
    getElementById(id: string) {
      return id === "framepilot-quit-dialog" ? overlay : null;
    },
  };
  assert.deepEqual(readQuitDialog(root), {
    title: "Import is still running",
    buttons: ["stay", "cancel_and_quit", "quit_anyway"],
  });
  const clickable = {
    querySelector(selector: string) {
      if (String(selector).includes("cancel_and_quit")) {
        return {
          click() {
            clicks.push("cancel_and_quit");
          },
        };
      }
      return null;
    },
    querySelectorAll() {
      return [];
    },
  };
  const previousHTMLElement = (globalThis as { HTMLElement?: typeof HTMLElement }).HTMLElement;
  class FakeElement {
    click() {
      clicks.push("cancel_and_quit");
    }
  }
  (globalThis as { HTMLElement: typeof FakeElement }).HTMLElement = FakeElement;
  try {
    const clicked = clickQuitDialogChoice("cancel_and_quit", {
      getElementById(id: string) {
        return id === "framepilot-quit-dialog"
          ? {
              querySelector(selector: string) {
                if (String(selector).includes("cancel_and_quit")) {
                  return new FakeElement();
                }
                return null;
              },
            }
          : null;
      },
    });
    assert.equal(clicked, true);
    assert.deepEqual(clicks, ["cancel_and_quit"]);
    assert.equal(clickable.querySelector("h2"), null);
  } finally {
    if (previousHTMLElement === undefined) {
      delete (globalThis as { HTMLElement?: typeof HTMLElement }).HTMLElement;
    } else {
      (globalThis as { HTMLElement: typeof HTMLElement }).HTMLElement = previousHTMLElement;
    }
  }
});

function quitMatrixApi(calls: string[], importStatus: "queued" | "running" | "complete" = "running") {
  return {
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
        accepted_files: 30,
        skipped_files: 0,
        expanded_total: 30,
        job: { id: "import-1", status: importStatus, job_type: "import" },
      };
    },
    processProject: async (projectId: string) => {
      calls.push(`processProject:${projectId}`);
      return { id: "process-1", status: "running" as const, error_message: null };
    },
    getJob: async (projectId: string, jobId: string) => {
      calls.push(`getJob:${projectId}:${jobId}`);
      if (jobId.startsWith("import") || jobId.startsWith("process")) {
        return {
          id: jobId,
          status: "complete" as const,
          job_type: jobId.startsWith("import") ? "import" : "processing",
          error_message: null,
        };
      }
      return { id: jobId, status: "running" as const, job_type: "export", error_message: null };
    },
    listPhotos: async () => [{ id: "photo-1" }],
    batchUpdatePhotos: async () => {
      calls.push("batchUpdatePhotos");
      return [];
    },
    exportSelection: async () => {
      calls.push("exportSelection");
      return { id: "export-1", status: "running" as const };
    },
  };
}

test("runDesktopQaQuitMatrix quit-clean writes idle and done without starting a job", async () => {
  const calls: string[] = [];
  const evidence: string[] = [];
  await runDesktopQaQuitMatrix({
    api: quitMatrixApi(calls),
    writeEvidence: async (line) => {
      evidence.push(line);
    },
    config: {
      photos: "/home/a/.cache/framepilot-desktop-quit-job/photos",
      project: "/home/a/.cache/framepilot-desktop-quit-job/project",
      mode: "quit-clean",
    },
    mode: "quit-clean",
    now: () => "2026-09-08T00:00:00.000Z",
    sleep: async () => {},
  });
  assert.equal(calls.includes("getHealth"), true);
  assert.equal(
    calls.some((call) => call.startsWith("importPhotosFromPaths:")),
    false,
  );
  const milestones = evidence.map((line) => JSON.parse(line) as { milestone: string; row?: string });
  assert.equal(
    milestones.some((row) => row.milestone === "idle"),
    true,
  );
  assert.equal(
    milestones.some((row) => row.milestone === "done" && row.row === "quit-clean"),
    true,
  );
});

test("runDesktopQaQuitMatrix quit-import writes import_running and clicks cancel_and_quit", async () => {
  const calls: string[] = [];
  const evidence: string[] = [];
  const dialog = {
    title: "Import is still running",
    buttons: ["stay", "cancel_and_quit", "quit_anyway"],
  };
  const clicked: string[] = [];
  await runDesktopQaQuitMatrix({
    api: quitMatrixApi(calls),
    writeEvidence: async (line) => {
      evidence.push(line);
    },
    config: {
      photos: "/home/a/.cache/framepilot-desktop-quit-job/photos",
      project: "/home/a/.cache/framepilot-desktop-quit-job/project",
      mode: "quit-import",
    },
    mode: "quit-import",
    now: () => "2026-09-08T00:00:00.000Z",
    sleep: async () => {},
    queryQuitDialog: () => dialog,
    clickQuitChoice: (choice) => {
      clicked.push(choice);
      return true;
    },
  });
  assert.equal(
    calls.includes("importPhotosFromPaths:proj-1:/home/a/.cache/framepilot-desktop-quit-job/photos"),
    true,
  );
  assert.equal(calls.includes("processProject:proj-1"), false);
  assert.deepEqual(clicked, ["cancel_and_quit"]);
  const milestones = evidence.map(
    (line) => JSON.parse(line) as { milestone: string; title?: string; buttons?: string[]; choice?: string },
  );
  assert.equal(
    milestones.some((row) => row.milestone === "import_running"),
    true,
  );
  const dialogLine = milestones.find((row) => row.milestone === "quit_dialog");
  assert.equal(dialogLine?.title, "Import is still running");
  assert.deepEqual(dialogLine?.buttons, ["stay", "cancel_and_quit", "quit_anyway"]);
  assert.equal(
    milestones.some((row) => row.milestone === "quit_choice" && row.choice === "cancel_and_quit"),
    true,
  );
});

test("runDesktopQaQuitMatrix quit-import requests production close immediately", async () => {
  const evidence: string[] = [];
  const closeCalls: number[] = [];
  let dialogVisible = false;
  await runDesktopQaQuitMatrix({
    api: quitMatrixApi([]),
    writeEvidence: async (line) => {
      evidence.push(line);
    },
    config: {
      photos: "/home/a/.cache/framepilot-desktop-quit-job/photos",
      project: "/home/a/.cache/framepilot-desktop-quit-job/project",
      mode: "quit-import",
    },
    mode: "quit-import",
    now: () => "2026-09-08T00:00:00.000Z",
    sleep: async () => {},
    requestClose: async () => {
      closeCalls.push(Date.now());
      dialogVisible = true;
    },
    queryQuitDialog: () =>
      dialogVisible
        ? {
            title: "Import is still running",
            buttons: ["stay", "cancel_and_quit", "quit_anyway"],
          }
        : null,
    clickQuitChoice: () => true,
  });
  assert.equal(closeCalls.length, 1);
  const milestones = evidence.map((line) => JSON.parse(line) as { milestone: string });
  const runningAt = milestones.findIndex((row) => row.milestone === "import_running");
  const closeAt = milestones.findIndex((row) => row.milestone === "close_requested");
  const dialogAt = milestones.findIndex((row) => row.milestone === "quit_dialog");
  assert.equal(runningAt >= 0, true);
  assert.equal(closeAt >= 0, true);
  assert.equal(dialogAt >= 0, true);
  assert.equal(closeAt > runningAt, true);
  assert.equal(dialogAt > closeAt, true);
});

test("runDesktopQaQuitMatrix quit-processing writes process_running without waiting for process complete", async () => {
  const calls: string[] = [];
  const evidence: string[] = [];
  await runDesktopQaQuitMatrix({
    api: quitMatrixApi(calls),
    writeEvidence: async (line) => {
      evidence.push(line);
    },
    config: {
      photos: "/home/a/.cache/framepilot-desktop-quit-job/photos",
      project: "/home/a/.cache/framepilot-desktop-quit-job/project",
      mode: "quit-processing",
    },
    mode: "quit-processing",
    now: () => "2026-09-08T00:00:00.000Z",
    sleep: async () => {},
    queryQuitDialog: () => ({
      title: "Grouping and ranking is still running",
      buttons: ["stay", "cancel_and_quit", "quit_anyway"],
    }),
    clickQuitChoice: () => true,
  });
  assert.equal(calls.includes("processProject:proj-1"), true);
  assert.equal(calls.includes("exportSelection"), false);
  const milestones = evidence.map((line) => JSON.parse(line) as { milestone: string });
  assert.equal(
    milestones.some((row) => row.milestone === "import_complete"),
    true,
  );
  assert.equal(
    milestones.some((row) => row.milestone === "process_running"),
    true,
  );
  assert.equal(
    milestones.some((row) => row.milestone === "process_complete"),
    false,
  );
});

test("runDesktopQaQuitMatrix quit-export writes export_running and does not require preview naturalWidth", async () => {
  const calls: string[] = [];
  const evidence: string[] = [];
  await runDesktopQaQuitMatrix({
    api: quitMatrixApi(calls),
    writeEvidence: async (line) => {
      evidence.push(line);
    },
    config: {
      photos: "/home/a/.cache/framepilot-desktop-quit-job/photos",
      project: "/home/a/.cache/framepilot-desktop-quit-job/project",
      mode: "quit-export",
    },
    mode: "quit-export",
    now: () => "2026-09-08T00:00:00.000Z",
    sleep: async () => {},
    queryQuitDialog: () => ({
      title: "Export is still running",
      buttons: ["stay", "cancel_and_quit", "quit_anyway"],
    }),
    clickQuitChoice: () => true,
  });
  assert.equal(calls.includes("batchUpdatePhotos"), true);
  assert.equal(calls.includes("exportSelection"), true);
  const milestones = evidence.map((line) => JSON.parse(line) as { milestone: string });
  assert.equal(
    milestones.some((row) => row.milestone === "export_running"),
    true,
  );
  assert.equal(
    milestones.some((row) => row.milestone === "first_preview"),
    false,
  );
});

test("startDesktopQaFromWindow dispatches quit-import instead of the cull preview path", async () => {
  const calls: string[] = [];
  const evidence: string[] = [];
  const fakeApi = quitMatrixApi(calls);
  const started = await startDesktopQaFromWindow({
    win: {
      __FRAMEPILOT_DESKTOP__: true,
      __FRAMEPILOT_WINDOW__: "main",
      __FRAMEPILOT_DESKTOP_QA__: {
        photos: "/home/a/.cache/framepilot-desktop-quit-job/photos",
        project: "/home/a/.cache/framepilot-desktop-quit-job/project",
        mode: "quit-import",
      },
    },
    api: fakeApi,
    writeEvidence: async (line) => {
      evidence.push(line);
    },
    push: (href) => {
      calls.push(`push:${href}`);
    },
    queryPreviewImages: () => {
      throw new Error("quit-import must not wait for /previews/ naturalWidth");
    },
    now: () => "2026-09-08T00:00:00.000Z",
    sleep: async () => {},
    queryQuitDialog: () => ({
      title: "Import is still running",
      buttons: ["stay", "cancel_and_quit", "quit_anyway"],
    }),
    clickQuitChoice: () => true,
  });
  assert.equal(started, true);
  assert.equal(
    calls.some((call) => call.startsWith("push:")),
    false,
  );
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"import_running"')),
    true,
  );
  assert.equal(
    evidence.some((line) => line.includes('"milestone":"cull_push"')),
    false,
  );
});
