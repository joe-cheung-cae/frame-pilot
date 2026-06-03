import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command:
        "NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost http_proxy= https_proxy= all_proxy= FRAMEPILOT_DATA_DIR=.framepilot-e2e-data .venv/bin/uvicorn app.main:app --app-dir apps/api --port 8000",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command:
        "NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost http_proxy= https_proxy= all_proxy= FRAMEPILOT_NEXT_DIST_DIR=.next-e2e npm --prefix apps/web run dev -- --port 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
