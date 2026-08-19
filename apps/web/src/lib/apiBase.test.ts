import test from "node:test";
import assert from "node:assert/strict";

import { resolveApiBase } from "./apiBase.ts";

const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const ENV_API_BASE_KEY = "NEXT_PUBLIC_API_BASE_URL";

type TestWindow = {
  __FRAMEPILOT_API_BASE__?: string;
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

function withEnv<T>(value: string | undefined, run: () => T): T {
  const hadEnv = Object.prototype.hasOwnProperty.call(process.env, ENV_API_BASE_KEY);
  const previous = process.env[ENV_API_BASE_KEY];
  if (value === undefined) {
    delete process.env[ENV_API_BASE_KEY];
  } else {
    process.env[ENV_API_BASE_KEY] = value;
  }
  try {
    return run();
  } finally {
    if (hadEnv) {
      process.env[ENV_API_BASE_KEY] = previous;
    } else {
      delete process.env[ENV_API_BASE_KEY];
    }
  }
}

test("window __FRAMEPILOT_API_BASE__ wins over env and the default", () => {
  const windowBase = "http://127.0.0.1:18000";
  withEnv("http://127.0.0.1:19000", () => {
    withWindow({ __FRAMEPILOT_API_BASE__: windowBase }, () => {
      assert.equal(resolveApiBase(), windowBase);
    });
  });
});

test("NEXT_PUBLIC_API_BASE_URL is used when the window base is missing", () => {
  const envBase = "http://127.0.0.1:19000";
  withEnv(envBase, () => {
    withWindow(undefined, () => {
      assert.equal(resolveApiBase(), envBase);
    });
    withWindow({}, () => {
      assert.equal(resolveApiBase(), envBase);
    });
  });
});

test("defaults to the loopback API when window and env bases are missing", () => {
  withEnv(undefined, () => {
    withWindow(undefined, () => {
      assert.equal(resolveApiBase(), DEFAULT_API_BASE);
    });
  });
});

test("trims a trailing slash from the resolved API base", () => {
  withEnv(undefined, () => {
    withWindow({ __FRAMEPILOT_API_BASE__: "http://127.0.0.1:18000/" }, () => {
      assert.equal(resolveApiBase(), "http://127.0.0.1:18000");
    });
  });
  withWindow(undefined, () => {
    withEnv("http://127.0.0.1:19000/", () => {
      assert.equal(resolveApiBase(), "http://127.0.0.1:19000");
    });
  });
});

test("missing window does not throw", () => {
  withEnv(undefined, () => {
    withWindow(undefined, () => {
      assert.equal(typeof globalThis.window, "undefined");
      assert.doesNotThrow(() => resolveApiBase());
      assert.equal(resolveApiBase(), DEFAULT_API_BASE);
    });
  });
});
