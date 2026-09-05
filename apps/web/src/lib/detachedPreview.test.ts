import test from "node:test";
import assert from "node:assert/strict";

import {
  emitReviewCommand,
  emitReviewSync,
  emitReviewSyncRequest,
  isPreviewWindow,
  requestDetachedPreviewClose,
  requestDetachedPreviewToggle,
  shouldApplyReviewCommand,
  shouldApplyReviewSync,
  subscribePreviewClosed,
  subscribePreviewOpened,
  subscribeReviewCommand,
  subscribeReviewSync,
  subscribeReviewSyncRequest,
  toReviewSyncPayload,
} from "./detachedPreview.ts";

type TestWindow = {
  __FRAMEPILOT_WINDOW__?: unknown;
  __FRAMEPILOT_DESKTOP__?: unknown;
};

function withWindow<T>(windowValue: TestWindow | undefined, run: () => T): T {
  const globalObject = globalThis as { window?: TestWindow };
  const hadWindow = Object.prototype.hasOwnProperty.call(globalThis, "window");
  const previous = globalObject.window;
  if (windowValue === undefined) {
    delete globalObject.window;
  } else {
    globalObject.window = windowValue;
  }
  try {
    return run();
  } finally {
    if (hadWindow) {
      globalObject.window = previous;
    } else {
      delete globalObject.window;
    }
  }
}

test("toReviewSyncPayload keeps previewPath and drops original paths", () => {
  const payload = toReviewSyncPayload({
    projectId: "project-1",
    activePhotoId: "photo-1",
    activeGroupId: "group-1",
    filename: "hero.jpg",
    previewPath: "previews/hero.webp",
    originalPath: "/camera/hero.jpg",
    original_path: "/camera/hero.jpg",
    project_copy_path: "originals/hero.jpg",
    source_identity: "sha-secret",
    compareMode: true,
    compare: [
      {
        photoId: "photo-1",
        filename: "hero.jpg",
        previewPath: "previews/hero.webp",
        originalPath: "/camera/hero.jpg",
        original_path: "/camera/hero.jpg",
        project_copy_path: "originals/hero.jpg",
        source_identity: "sha-secret",
      },
    ],
    previewZoom: 1.25,
  });

  assert.equal(payload.previewPath, "previews/hero.webp");
  assert.equal(payload.filename, "hero.jpg");
  assert.equal(payload.projectId, "project-1");
  assert.equal(payload.activePhotoId, "photo-1");
  assert.equal(payload.compareMode, true);
  assert.equal(payload.previewZoom, 1.25);
  assert.deepEqual(Object.keys(payload).sort(), [
    "activeGroupId",
    "activePhotoId",
    "compare",
    "compareMode",
    "filename",
    "previewPath",
    "previewZoom",
    "projectId",
  ]);
  assert.deepEqual(Object.keys(payload.compare[0] ?? {}).sort(), ["filename", "photoId", "previewPath"]);
  const serialized = JSON.stringify(payload);
  assert.equal(serialized.includes("originalPath"), false);
  assert.equal(serialized.includes("original_path"), false);
  assert.equal(serialized.includes("project_copy_path"), false);
  assert.equal(serialized.includes("source_identity"), false);
  assert.equal(serialized.includes("/camera/hero.jpg"), false);
  assert.equal(serialized.includes("originals/hero.jpg"), false);
});

test("requestDetachedPreviewToggle is not-desktop in the web stub", async () => {
  assert.deepEqual(await requestDetachedPreviewToggle(), { ok: false, reason: "not-desktop" });
});

test("requestDetachedPreviewClose does not toggle", async () => {
  const toggle = await requestDetachedPreviewToggle();
  const close = await requestDetachedPreviewClose();
  assert.deepEqual(toggle, { ok: false, reason: "not-desktop" });
  assert.notDeepEqual(close, toggle);
  assert.equal(close.ok === true ? close.open : null, false);
});

test("web event helpers are no-ops", async () => {
  await emitReviewSync(
    toReviewSyncPayload({
      projectId: "p",
      activePhotoId: null,
      activeGroupId: null,
      filename: null,
      previewPath: null,
      compareMode: false,
      compare: [],
      previewZoom: 1,
    }),
  );
  await emitReviewSyncRequest();
  await emitReviewCommand({ type: "toggle_large_preview" });
  const unlistens = await Promise.all([
    subscribeReviewSync(() => {
      throw new Error("web stub must not deliver review sync");
    }),
    subscribeReviewSyncRequest(() => {
      throw new Error("web stub must not deliver sync request");
    }),
    subscribeReviewCommand(() => {
      throw new Error("web stub must not deliver review command");
    }),
    subscribePreviewOpened(() => {
      throw new Error("web stub must not deliver preview opened");
    }),
    subscribePreviewClosed(() => {
      throw new Error("web stub must not deliver preview closed");
    }),
  ]);
  for (const unlisten of unlistens) {
    assert.equal(typeof unlisten, "function");
    unlisten();
  }
});

test("main ignores review sync and preview ignores review command", () => {
  withWindow({ __FRAMEPILOT_WINDOW__: "main", __FRAMEPILOT_DESKTOP__: true }, () => {
    assert.equal(isPreviewWindow(), false);
    assert.equal(shouldApplyReviewSync(), false);
    assert.equal(shouldApplyReviewCommand(), true);
  });
  withWindow({ __FRAMEPILOT_WINDOW__: "preview", __FRAMEPILOT_DESKTOP__: true }, () => {
    assert.equal(isPreviewWindow(), true);
    assert.equal(shouldApplyReviewSync(), true);
    assert.equal(shouldApplyReviewCommand(), false);
  });
});
