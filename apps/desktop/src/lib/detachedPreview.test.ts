import assert from "node:assert/strict";
import { mock, test } from "node:test";

const invokeCalls: Array<{ cmd: string; args?: unknown }> = [];
const emitCalls: Array<{ event: string; payload?: unknown }> = [];
const listeners = new Map<string, Array<(event: { payload: unknown }) => void>>();
let toggleResult: boolean | Error = true;
let closeResult: boolean | Error = false;

mock.module("@tauri-apps/api/core", {
  namedExports: {
    async invoke(cmd: string, args?: unknown) {
      invokeCalls.push({ cmd, args });
      if (cmd === "toggle_detached_preview") {
        if (toggleResult instanceof Error) {
          throw toggleResult;
        }
        return toggleResult;
      }
      if (cmd === "close_detached_preview") {
        if (closeResult instanceof Error) {
          throw closeResult;
        }
        return closeResult;
      }
      throw new Error(`unexpected invoke ${cmd}`);
    },
  },
});

mock.module("@tauri-apps/api/event", {
  namedExports: {
    async emit(event: string, payload?: unknown) {
      emitCalls.push({ event, payload });
    },
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

type TestWindow = {
  __FRAMEPILOT_WINDOW__?: unknown;
  __FRAMEPILOT_DESKTOP__?: unknown;
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

const {
  emitReviewCommand,
  emitReviewSync,
  emitReviewSyncRequest,
  requestDetachedPreviewClose,
  requestDetachedPreviewToggle,
  subscribePreviewClosed,
  subscribePreviewOpened,
  subscribeReviewCommand,
  subscribeReviewSync,
  subscribeReviewSyncRequest,
  toReviewSyncPayload,
} = await import("./detachedPreview.ts");

test("desktop toggle invokes toggle_detached_preview", async () => {
  invokeCalls.length = 0;
  toggleResult = true;
  const result = await requestDetachedPreviewToggle();
  assert.deepEqual(result, { ok: true, open: true });
  assert.deepEqual(
    invokeCalls.map((call) => call.cmd),
    ["toggle_detached_preview"],
  );
});

test("desktop close invokes close_detached_preview and does not toggle", async () => {
  invokeCalls.length = 0;
  closeResult = false;
  const result = await requestDetachedPreviewClose();
  assert.deepEqual(result, { ok: true, open: false });
  assert.deepEqual(
    invokeCalls.map((call) => call.cmd),
    ["close_detached_preview"],
  );
  assert.equal(
    invokeCalls.some((call) => call.cmd === "toggle_detached_preview"),
    false,
  );
});

test("desktop toggle create failure keeps in-shell preview", async () => {
  invokeCalls.length = 0;
  toggleResult = new Error("webview failed");
  const result = await requestDetachedPreviewToggle();
  assert.equal(result.ok, false);
  if (result.ok === false) {
    assert.match(result.reason, /webview failed/);
  }
});

test("desktop main emits sanitized sync and ignores review-sync listeners", async () => {
  emitCalls.length = 0;
  listeners.clear();
  await withWindow({ __FRAMEPILOT_WINDOW__: "main", __FRAMEPILOT_DESKTOP__: true }, async () => {
    const dirty = {
      projectId: "project-1",
      activePhotoId: "photo-1",
      activeGroupId: "group-1",
      filename: "hero.jpg",
      previewPath: "previews/hero.webp",
      originalPath: "/camera/hero.jpg",
      project_copy_path: "originals/hero.jpg",
      compareMode: false,
      compare: [],
      previewZoom: 1,
    };
    await emitReviewSync(dirty);
    assert.equal(emitCalls.length, 1);
    assert.equal(emitCalls[0]?.event, "framepilot-review-sync");
    const payload = emitCalls[0]?.payload as { previewPath?: string };
    assert.equal(payload.previewPath, "previews/hero.webp");
    assert.equal(JSON.stringify(payload).includes("originalPath"), false);
    assert.equal(JSON.stringify(payload).includes("project_copy_path"), false);

    let syncHits = 0;
    const unlistenSync = await subscribeReviewSync(() => {
      syncHits += 1;
    });
    for (const handler of listeners.get("framepilot-review-sync") ?? []) {
      handler({ payload: toReviewSyncPayload(dirty) });
    }
    assert.equal(syncHits, 0);
    unlistenSync();

    let commandHits = 0;
    const unlistenCommand = await subscribeReviewCommand(() => {
      commandHits += 1;
    });
    for (const handler of listeners.get("framepilot-review-command") ?? []) {
      handler({ payload: { type: "toggle_large_preview" } });
    }
    assert.equal(commandHits, 1);
    unlistenCommand();
  });
});

test("desktop preview forwards commands and ignores review-command listeners", async () => {
  emitCalls.length = 0;
  listeners.clear();
  await withWindow({ __FRAMEPILOT_WINDOW__: "preview", __FRAMEPILOT_DESKTOP__: true }, async () => {
    await emitReviewCommand({ type: "mark", status: "Pick" });
    await emitReviewSyncRequest();
    assert.deepEqual(
      emitCalls.map((call) => call.event),
      ["framepilot-review-command", "framepilot-review-sync-request"],
    );

    let commandHits = 0;
    const unlistenCommand = await subscribeReviewCommand(() => {
      commandHits += 1;
    });
    for (const handler of listeners.get("framepilot-review-command") ?? []) {
      handler({ payload: { type: "mark", status: "Pick" } });
    }
    assert.equal(commandHits, 0);
    unlistenCommand();

    let syncHits = 0;
    const unlistenSync = await subscribeReviewSync(() => {
      syncHits += 1;
    });
    for (const handler of listeners.get("framepilot-review-sync") ?? []) {
      handler({
        payload: toReviewSyncPayload({
          projectId: "p",
          activePhotoId: "photo-1",
          activeGroupId: null,
          filename: "hero.jpg",
          previewPath: "previews/hero.webp",
          compareMode: false,
          compare: [],
          previewZoom: 1,
        }),
      });
    }
    assert.equal(syncHits, 1);
    unlistenSync();
  });
});

test("desktop opened and closed subscriptions are no-ops until listen fires", async () => {
  listeners.clear();
  await withWindow({ __FRAMEPILOT_WINDOW__: "main", __FRAMEPILOT_DESKTOP__: true }, async () => {
    let opened = 0;
    let closed = 0;
    const unlistenOpened = await subscribePreviewOpened(() => {
      opened += 1;
    });
    const unlistenClosed = await subscribePreviewClosed(() => {
      closed += 1;
    });
    const unlistenRequest = await subscribeReviewSyncRequest(() => {
      opened += 10;
    });
    for (const handler of listeners.get("framepilot-preview-opened") ?? []) {
      handler({ payload: null });
    }
    for (const handler of listeners.get("framepilot-preview-closed") ?? []) {
      handler({ payload: null });
    }
    assert.equal(opened, 1);
    assert.equal(closed, 1);
    unlistenOpened();
    unlistenClosed();
    unlistenRequest();
  });
});
