import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { nativeFsState, revealInFileManager, getMeta } = vi.hoisted(() => ({
  nativeFsState: {
    current: null as {
      pickDirectory: () => Promise<string | null>;
      pickImageFiles: () => Promise<string[] | null>;
      revealInFileManager: (targetPath: string) => Promise<void>;
      subscribeDragDrop: () => Promise<() => void>;
    } | null,
  },
  revealInFileManager: vi.fn(async () => undefined),
  getMeta: vi.fn(async () => ({
    version: "2.0.0-rc2",
    service: "framepilot-api",
    data_dir: "/tmp/framepilot-data",
    desktop_mode: false,
  })),
}));

vi.mock("@/lib/nativeFs", () => ({
  getNativeFs: () => nativeFsState.current,
}));

vi.mock("@/lib/api", () => ({
  api: {
    getMeta,
  },
}));

import { SettingsPanel } from "./SettingsPanel";

const DATA_DIR = "/tmp/framepilot-data";

function renderSettings() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <SettingsPanel />
    </QueryClientProvider>,
  );
}

describe("SettingsPanel data directory", () => {
  beforeEach(() => {
    cleanup();
    revealInFileManager.mockClear();
    getMeta.mockClear();
    nativeFsState.current = null;
    delete window.__FRAMEPILOT_DESKTOP__;
  });

  afterEach(() => {
    cleanup();
    delete window.__FRAMEPILOT_DESKTOP__;
  });

  it("shows the read-only data directory from GET /api/meta", async () => {
    renderSettings();

    await waitFor(() => {
      expect(screen.getByLabelText("Data directory").textContent).toContain(DATA_DIR);
    });
    expect(screen.queryByRole("button", { name: "Open data folder" })).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.getByText("Default export statuses")).toBeTruthy();
  });

  it("opens the data folder on desktop when native FS is available", async () => {
    window.__FRAMEPILOT_DESKTOP__ = true;
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
    };

    renderSettings();

    await waitFor(() => {
      expect(screen.getByText(DATA_DIR)).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Open data folder" }));
    await waitFor(() => {
      expect(revealInFileManager).toHaveBeenCalledWith(DATA_DIR);
    });
  });

  it("hides Open data folder in the browser shell even when native FS is mocked", async () => {
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
    };

    renderSettings();

    await waitFor(() => {
      expect(screen.getByText(DATA_DIR)).toBeTruthy();
    });
    expect(screen.queryByRole("button", { name: "Open data folder" })).toBeNull();
  });
});
