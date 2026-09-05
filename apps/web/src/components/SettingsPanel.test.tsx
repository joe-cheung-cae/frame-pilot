import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { nativeFsState, revealInFileManager, pickDirectory, applyDataDirectory, getMeta, getSettings, patchSettings, registerDesktopProjectRoot, changeDesktopDataDir } = vi.hoisted(() => ({
  nativeFsState: {
    current: null as {
      pickDirectory: () => Promise<string | null>;
      pickImageFiles: () => Promise<string[] | null>;
      revealInFileManager: (targetPath: string) => Promise<void>;
      subscribeDragDrop: () => Promise<() => void>;
      applyDataDirectory?: (path: string) => Promise<void>;
    } | null,
  },
  revealInFileManager: vi.fn(async () => undefined),
  pickDirectory: vi.fn(async () => "/tmp/new-framepilot-data"),
  applyDataDirectory: vi.fn(async () => undefined),
  getMeta: vi.fn(async () => ({
    version: "2.0.0-rc2",
    service: "framepilot-api",
    data_dir: "/tmp/framepilot-data",
    desktop_mode: false,
  })),
  getSettings: vi.fn(async () => ({ import_workers: 1 })),
  patchSettings: vi.fn(async (payload: { import_workers?: number }) => ({
    import_workers: payload.import_workers ?? 1,
  })),
  registerDesktopProjectRoot: vi.fn(async (path: string) => ({ path })),
  changeDesktopDataDir: vi.fn(async (path: string) => ({ data_dir: path })),
}));

vi.mock("@/lib/nativeFs", () => ({
  getNativeFs: () => nativeFsState.current,
}));

vi.mock("@/lib/api", () => ({
  api: {
    getMeta,
    getSettings,
    patchSettings,
    registerDesktopProjectRoot,
    changeDesktopDataDir,
  },
}));

import { DATA_DIR_CHANGE_CONFIRM, SettingsPanel } from "./SettingsPanel";

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
    pickDirectory.mockClear();
    applyDataDirectory.mockClear();
    getMeta.mockClear();
    getSettings.mockClear();
    patchSettings.mockClear();
    registerDesktopProjectRoot.mockClear();
    changeDesktopDataDir.mockClear();
    getSettings.mockResolvedValue({ import_workers: 1 });
    pickDirectory.mockResolvedValue("/tmp/new-framepilot-data");
    getMeta.mockResolvedValue({
      version: "2.0.0-rc2",
      service: "framepilot-api",
      data_dir: DATA_DIR,
      desktop_mode: false,
    });
    nativeFsState.current = null;
    delete window.__FRAMEPILOT_DESKTOP__;
    vi.stubGlobal("confirm", vi.fn(() => true));
  });

  afterEach(() => {
    cleanup();
    delete window.__FRAMEPILOT_DESKTOP__;
    vi.unstubAllGlobals();
  });

  it("shows the read-only data directory from GET /api/meta", async () => {
    renderSettings();

    await waitFor(() => {
      expect(screen.getByLabelText("Data directory").textContent).toContain(DATA_DIR);
    });
    expect(screen.queryByRole("button", { name: "Open data folder" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Change data directory" })).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.getByText("Default export statuses")).toBeTruthy();
  });

  it("opens the data folder on desktop when native FS is available", async () => {
    window.__FRAMEPILOT_DESKTOP__ = true;
    nativeFsState.current = {
      pickDirectory,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
      applyDataDirectory,
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
      pickDirectory,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
      applyDataDirectory,
    };

    renderSettings();

    await waitFor(() => {
      expect(screen.getByText(DATA_DIR)).toBeTruthy();
    });
    expect(screen.queryByRole("button", { name: "Open data folder" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Change data directory" })).toBeNull();
  });

  it("changes the data directory on desktop with native FS after confirm", async () => {
    window.__FRAMEPILOT_DESKTOP__ = true;
    nativeFsState.current = {
      pickDirectory,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
      applyDataDirectory,
    };
    getMeta
      .mockResolvedValueOnce({
        version: "2.0.0-rc2",
        service: "framepilot-api",
        data_dir: DATA_DIR,
        desktop_mode: true,
      })
      .mockResolvedValue({
        version: "2.0.0-rc2",
        service: "framepilot-api",
        data_dir: "/tmp/new-framepilot-data",
        desktop_mode: true,
      });

    renderSettings();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Change data directory" })).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Change data directory" }));

    await waitFor(() => {
      expect(pickDirectory).toHaveBeenCalled();
      expect(registerDesktopProjectRoot).toHaveBeenCalledWith("/tmp/new-framepilot-data");
      expect(window.confirm).toHaveBeenCalledWith(DATA_DIR_CHANGE_CONFIRM);
      expect(changeDesktopDataDir).toHaveBeenCalledWith("/tmp/new-framepilot-data");
      expect(applyDataDirectory).toHaveBeenCalledWith("/tmp/new-framepilot-data");
    });
    await waitFor(() => {
      expect(screen.getByLabelText("Data directory").textContent).toContain("/tmp/new-framepilot-data");
    });
  });
});

describe("SettingsPanel import workers", () => {
  beforeEach(() => {
    cleanup();
    getMeta.mockClear();
    getSettings.mockClear();
    patchSettings.mockClear();
    getSettings.mockResolvedValue({ import_workers: 1 });
    nativeFsState.current = null;
    delete window.__FRAMEPILOT_DESKTOP__;
  });

  afterEach(() => {
    cleanup();
    delete window.__FRAMEPILOT_DESKTOP__;
  });

  it("shows import workers 1 by default", async () => {
    renderSettings();

    const control = await screen.findByLabelText("Import workers");
    expect((control as HTMLSelectElement).value).toBe("1");
    expect(screen.getByRole("heading", { name: "Import workers" })).toBeTruthy();
    expect(getSettings).toHaveBeenCalled();
  });

  it("patches import_workers 3 when the control is changed", async () => {
    renderSettings();
    const control = await screen.findByLabelText("Import workers");

    fireEvent.change(control, { target: { value: "3" } });

    await waitFor(() => {
      expect(patchSettings).toHaveBeenCalledWith({ import_workers: 3 });
    });
    expect(window.localStorage.getItem("import_workers")).toBeNull();
  });
});
