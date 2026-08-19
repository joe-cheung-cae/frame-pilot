import test from "node:test";
import assert from "node:assert/strict";

import { applyShellDataset, isDesktopShell } from "./shell.ts";

type TestWindow = {
  __FRAMEPILOT_DESKTOP__?: unknown;
};

type TestDocument = {
  documentElement: {
    dataset: Record<string, string>;
  };
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

function withDocument<T>(documentValue: TestDocument | undefined, run: () => T): T {
  const globalObject = globalThis as { document?: TestDocument };
  const hadDocument = Object.prototype.hasOwnProperty.call(globalThis, "document");
  const previous = globalObject.document;
  if (documentValue === undefined) {
    delete globalObject.document;
  } else {
    globalObject.document = documentValue;
  }
  try {
    return run();
  } finally {
    if (hadDocument) {
      globalObject.document = previous;
    } else {
      delete globalObject.document;
    }
  }
}

test("isDesktopShell is true only for the literal boolean true", () => {
  withWindow({ __FRAMEPILOT_DESKTOP__: true }, () => {
    assert.equal(isDesktopShell(), true);
  });
});

test("isDesktopShell is false for undefined, string 1, and 0", () => {
  withWindow({ __FRAMEPILOT_DESKTOP__: undefined }, () => {
    assert.equal(isDesktopShell(), false);
  });
  withWindow({ __FRAMEPILOT_DESKTOP__: "1" }, () => {
    assert.equal(isDesktopShell(), false);
  });
  withWindow({ __FRAMEPILOT_DESKTOP__: 0 }, () => {
    assert.equal(isDesktopShell(), false);
  });
});

test("isDesktopShell is false and does not throw without window", () => {
  withWindow(undefined, () => {
    assert.equal(typeof globalThis.window, "undefined");
    assert.doesNotThrow(() => isDesktopShell());
    assert.equal(isDesktopShell(), false);
  });
});

test("applyShellDataset no-ops without document", () => {
  withDocument(undefined, () => {
    assert.equal(typeof globalThis.document, "undefined");
    assert.doesNotThrow(() => applyShellDataset());
  });
});

test("applyShellDataset sets dataset.shell to desktop or browser", () => {
  const dataset: Record<string, string> = {};
  withDocument({ documentElement: { dataset } }, () => {
    withWindow(undefined, () => {
      applyShellDataset();
      assert.equal(dataset.shell, "browser");
    });
    withWindow({ __FRAMEPILOT_DESKTOP__: true }, () => {
      applyShellDataset();
      assert.equal(dataset.shell, "desktop");
    });
    withWindow({ __FRAMEPILOT_DESKTOP__: "1" }, () => {
      applyShellDataset();
      assert.equal(dataset.shell, "browser");
    });
  });
});
