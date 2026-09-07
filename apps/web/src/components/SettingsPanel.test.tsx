import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const {
  nativeFsState,
  revealInFileManager,
  pickDirectory,
  applyDataDirectory,
  getMeta,
  getSettings,
  patchSettings,
  getCache,
  clearDerivatives,
  registerDesktopProjectRoot,
  changeDesktopDataDir,
} = vi.hoisted(() => ({
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
  getCache: vi.fn(async () => ({
    derivative_bytes: 0,
    file_count: 0,
    project_count: 0,
    deleted_files: 0,
  })),
  clearDerivatives: vi.fn(async () => ({
    derivative_bytes: 0,
    file_count: 0,
    project_count: 0,
    deleted_files: 0,
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
    getCache,
    clearDerivatives,
    registerDesktopProjectRoot,
    changeDesktopDataDir,
  },
}));

import { CLEAR_DERIVATIVES_CONFIRM, DATA_DIR_CHANGE_CONFIRM, SettingsPanel } from "./SettingsPanel";

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
    getCache.mockClear();
    clearDerivatives.mockClear();
    registerDesktopProjectRoot.mockClear();
    changeDesktopDataDir.mockClear();
    getSettings.mockResolvedValue({ import_workers: 1 });
    getCache.mockResolvedValue({
      derivative_bytes: 0,
      file_count: 0,
      project_count: 0,
      deleted_files: 0,
    });
    pickDirectory.mockResolvedValue("/tmp/new-framepilot-data");
    getMeta.mockResolvedValue({
      version: "2.0.0-rc2",
      service: "framepilot-api",
      data_dir: DATA_DIR,
      desktop_mode: false,
    });
    nativeFsState.current = null;
    delete window.__FRAMEPILOT_DESKTOP__;
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
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
    getCache.mockClear();
    clearDerivatives.mockClear();
    getSettings.mockResolvedValue({ import_workers: 1 });
    getCache.mockResolvedValue({
      derivative_bytes: 0,
      file_count: 0,
      project_count: 0,
      deleted_files: 0,
    });
    nativeFsState.current = null;
    delete window.__FRAMEPILOT_DESKTOP__;
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
  });

  afterEach(() => {
    cleanup();
    delete window.__FRAMEPILOT_DESKTOP__;
    vi.unstubAllGlobals();
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

describe("SettingsPanel derivative cache", () => {
  beforeEach(() => {
    cleanup();
    getMeta.mockClear();
    getSettings.mockClear();
    getCache.mockClear();
    clearDerivatives.mockClear();
    getSettings.mockResolvedValue({ import_workers: 1 });
    getCache.mockResolvedValue({
      derivative_bytes: 1536,
      file_count: 2,
      project_count: 1,
      deleted_files: 0,
    });
    nativeFsState.current = null;
    delete window.__FRAMEPILOT_DESKTOP__;
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
  });

  afterEach(() => {
    cleanup();
    delete window.__FRAMEPILOT_DESKTOP__;
    vi.unstubAllGlobals();
  });

  it("shows measured thumbnail and preview cache size", async () => {
    renderSettings();

    expect(await screen.findByRole("heading", { name: "Derivative cache" })).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByLabelText("Derivative cache size").textContent).toContain("1.5 KB");
    });
    expect(screen.getByLabelText("Derivative cache size").textContent).toContain("2 files");
    expect(screen.getByLabelText("Derivative cache size").textContent).toContain("1 project");
    expect(getCache).toHaveBeenCalled();
  });

  it("disables clear when the cache is empty", async () => {
    getCache.mockResolvedValue({
      derivative_bytes: 0,
      file_count: 0,
      project_count: 0,
      deleted_files: 0,
    });
    renderSettings();

    await waitFor(() => {
      expect(screen.getByLabelText("Derivative cache size").textContent).toContain("0 B");
    });
    expect((screen.getByRole("button", { name: "Clear thumbnails and previews" }) as HTMLButtonElement).disabled).toBe(
      true,
    );
  });

  it("clears derivatives after confirm", async () => {
    let cleared = false;
    getCache.mockImplementation(async () =>
      cleared
        ? { derivative_bytes: 0, file_count: 0, project_count: 0, deleted_files: 2 }
        : { derivative_bytes: 1536, file_count: 2, project_count: 1, deleted_files: 0 },
    );
    clearDerivatives.mockImplementation(async () => {
      cleared = true;
      return { derivative_bytes: 0, file_count: 0, project_count: 0, deleted_files: 2 };
    });

    renderSettings();
    await waitFor(() => {
      expect(screen.getByLabelText("Derivative cache size").textContent).toContain("1.5 KB");
    });
    fireEvent.click(screen.getByRole("button", { name: "Clear thumbnails and previews" }));

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith(CLEAR_DERIVATIVES_CONFIRM);
      expect(clearDerivatives).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByLabelText("Derivative cache size").textContent).toContain("0 B");
    });
  });

  it("does not clear when confirm is cancelled", async () => {
    vi.stubGlobal(
      "confirm",
      vi.fn(() => false),
    );
    renderSettings();
    await waitFor(() => {
      expect(screen.getByLabelText("Derivative cache size").textContent).toContain("1.5 KB");
    });
    fireEvent.click(screen.getByRole("button", { name: "Clear thumbnails and previews" }));

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith(CLEAR_DERIVATIVES_CONFIRM);
    });
    expect(clearDerivatives).not.toHaveBeenCalled();
  });

  it("shows a conflict message when a job is running", async () => {
    clearDerivatives.mockRejectedValue(
      new Error("Cannot clear derivatives while an import or processing job is active"),
    );
    renderSettings();
    await waitFor(() => {
      expect(screen.getByLabelText("Derivative cache size").textContent).toContain("1.5 KB");
    });
    fireEvent.click(screen.getByRole("button", { name: "Clear thumbnails and previews" }));

    await waitFor(() => {
      expect(screen.getByText("Cannot clear derivatives while an import or processing job is active")).toBeTruthy();
    });
  });
});
