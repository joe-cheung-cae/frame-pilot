import assert from "node:assert/strict";
import { mock, test } from "node:test";

const listeners = new Map<string, Array<(event: { payload: unknown }) => void>>();

mock.module("@tauri-apps/api/event", {
  namedExports: {
    async listen(event: string, handler: (event: { payload: unknown }) => void) {
      const bucket = listeners.get(event) ?? [];
      bucket.push(handler);
      listeners.set(event, bucket);
      return () => {
        const current = listeners.get(event) ?? [];
        const index = current.indexOf(handler);
        if (index >= 0) {
          current.splice(index, 1);
        }
      };
    },
  },
});

const {
  ALLOW_TAKE_MENU_COMMAND,
  hrefForNativeMenuCommand,
  menuCommandFromPayload,
  menuCommandFromSidecarPayload,
  SIDECAR_MENU_COMMAND_PATH,
  subscribeNativeMenu,
  TAKE_MENU_COMMAND,
  takeSidecarMenuCommand,
} = await import("./nativeMenu.ts");

test("home without lastOpened Import goes to create-project workflow", () => {
  assert.equal(hrefForNativeMenuCommand("import", "/", null), "/projects/new?workflow=import");
});

test("lastOpened Import goes to that project Import Images", () => {
  assert.equal(
    hrefForNativeMenuCommand("import", "/", "project-1"),
    "/projects/project-1/import",
  );
});

test("native menu listen on home without lastOpened navigates Import", async () => {
  listeners.clear();
  const hrefs: string[] = [];
  const unlisten = await subscribeNativeMenu((payload) => {
    const href = hrefForNativeMenuCommand(payload, "/", null);
    if (href) {
      hrefs.push(href);
    }
  });
  for (const handler of listeners.get("framepilot-menu") ?? []) {
    handler({ payload: "import" });
  }
  assert.deepEqual(hrefs, ["/projects/new?workflow=import"]);
  unlisten();
});

test("wrapped emit payload still navigates Import", () => {
  assert.equal(menuCommandFromPayload({ payload: "import" }), "import");
  assert.equal(
    hrefForNativeMenuCommand({ payload: "import" }, "/", null),
    "/projects/new?workflow=import",
  );
});

test("take_menu_command is the packaged IPC name", () => {
  assert.equal(TAKE_MENU_COMMAND, "take_menu_command");
  assert.equal(ALLOW_TAKE_MENU_COMMAND, "allow-take-menu-command");
});

test("sidecar menu command path is the packaged HTTP take", () => {
  assert.equal(SIDECAR_MENU_COMMAND_PATH, "/api/desktop/menu-command");
  assert.equal(menuCommandFromSidecarPayload({ command: "import" }), "import");
  assert.equal(menuCommandFromSidecarPayload({ command: null }), null);
  assert.equal(menuCommandFromSidecarPayload({}), null);
});

test("takeSidecarMenuCommand reads Import from loopback GET", async () => {
  const previousFetch = globalThis.fetch;
  const urls: string[] = [];
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    urls.push(String(input));
    return {
      ok: true,
      json: async () => ({ command: "import" }),
    } as Response;
  }) as typeof fetch;
  try {
    const command = await takeSidecarMenuCommand("http://127.0.0.1:4192");
    assert.equal(command, "import");
    assert.deepEqual(urls, ["http://127.0.0.1:4192/api/desktop/menu-command"]);
  } finally {
    globalThis.fetch = previousFetch;
  }
});

test("native menu listen with lastOpened navigates Import", async () => {
  listeners.clear();
  const hrefs: string[] = [];
  const unlisten = await subscribeNativeMenu((payload) => {
    const href = hrefForNativeMenuCommand(payload, "/", "project-1");
    if (href) {
      hrefs.push(href);
    }
  });
  for (const handler of listeners.get("framepilot-menu") ?? []) {
    handler({ payload: "import" });
  }
  assert.deepEqual(hrefs, ["/projects/project-1/import"]);
  unlisten();
});
