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

const { hrefForNativeMenuCommand, menuCommandFromPayload, subscribeNativeMenu, TAKE_MENU_COMMAND } =
  await import("./nativeMenu.ts");

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
