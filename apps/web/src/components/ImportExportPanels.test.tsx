import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

type NativeFsMock = {
  pickDirectory: () => Promise<string | null>;
  pickImageFiles: () => Promise<string[] | null>;
  revealInFileManager: (targetPath: string) => Promise<void>;
  subscribeDragDrop: () => Promise<() => void>;
};

type ExportRecordMock = {
  id: string;
  project_id: string;
  mode: "csv" | "folder" | "zip";
  status: "running" | "complete" | "failed";
  selected_count: number;
  processed_count: number;
  total_count: number;
  statuses: string;
  include_xmp?: boolean;
  output_path: string;
  error_message: string | null;
  completed_at: string | null;
  created_at: string;
};

const { nativeFsState, queryMode, mutationData, mutationPending, exportRecords, exportSelection, revealInFileManager } =
  vi.hoisted(() => ({
    nativeFsState: { current: null as NativeFsMock | null },
    queryMode: { current: "error" as "error" | "success" },
    mutationData: { current: undefined as ExportRecordMock | undefined },
    mutationPending: { current: false },
    exportRecords: { current: [] as ExportRecordMock[] },
    exportSelection: vi.fn(),
    revealInFileManager: vi.fn(async () => undefined),
  }));

vi.mock("@/lib/nativeFs", () => ({
  getNativeFs: () => nativeFsState.current,
}));

vi.mock("@/lib/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: ({ queryKey }: { queryKey: unknown[] }) => {
    if (queryMode.current === "error") {
      return {
        isLoading: false,
        isError: true,
        error: new Error("API offline"),
        data: undefined,
        isSuccess: false,
        refetchInterval: false,
        isFetching: false,
      };
    }
    if (queryKey[0] === "project") {
      return {
        isLoading: false,
        isError: false,
        error: null,
        data: { id: "project-1", name: "Shoot", root_path: "/projects/shoot" },
      };
    }
    if (queryKey[0] === "photo-status-counts") {
      return {
        isLoading: false,
        isError: false,
        error: null,
        data: { Pick: 2, Maybe: 0, Reject: 0, Unreviewed: 0 },
      };
    }
    return {
      isLoading: false,
      isError: false,
      error: null,
      data: exportRecords.current,
      isFetching: false,
    };
  },
  useMutation: ({ mutationFn }: { mutationFn: () => Promise<unknown> }) => ({
    mutate: () => {
      void mutationFn();
    },
    isPending: mutationPending.current,
    error: null,
    isError: false,
    data: mutationData.current,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
  }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      exportSelection: (...args: unknown[]) => exportSelection(...args),
    },
  };
});

import { exportDownloadUrl } from "@/lib/api";
import { ExportPanel } from "./ExportPanel";
import { ImportPanel } from "./ImportPanel";

const csvLatest: ExportRecordMock = {
  id: "export-latest",
  project_id: "project-1",
  mode: "csv",
  status: "complete",
  selected_count: 2,
  processed_count: 2,
  total_count: 2,
  statuses: '["Pick"]',
  output_path: "/projects/shoot/exports/csv/latest.csv",
  error_message: null,
  completed_at: "2026-08-21T00:00:00Z",
  created_at: "2026-08-21T00:00:00Z",
};

const csvHistory: ExportRecordMock = {
  id: "export-csv",
  project_id: "project-1",
  mode: "csv",
  status: "complete",
  selected_count: 2,
  processed_count: 2,
  total_count: 2,
  statuses: '["Pick"]',
  output_path: "/projects/shoot/exports/csv/selection.csv",
  error_message: null,
  completed_at: "2026-08-20T00:00:00Z",
  created_at: "2026-08-20T00:00:00Z",
};

const zipHistory: ExportRecordMock = {
  id: "export-zip",
  project_id: "project-1",
  mode: "zip",
  status: "complete",
  selected_count: 2,
  processed_count: 2,
  total_count: 2,
  statuses: '["Pick"]',
  output_path: "/projects/shoot/exports/zip/selection.zip",
  error_message: null,
  completed_at: "2026-08-20T00:00:00Z",
  created_at: "2026-08-20T00:00:00Z",
};

const folderHistory: ExportRecordMock = {
  id: "export-folder",
  project_id: "project-1",
  mode: "folder",
  status: "complete",
  selected_count: 2,
  processed_count: 2,
  total_count: 2,
  statuses: '["Pick"]',
  output_path: "/projects/shoot/exports/folders/selection-1",
  error_message: null,
  completed_at: "2026-08-20T00:00:00Z",
  created_at: "2026-08-20T00:00:00Z",
};

function renderSuccessfulExportPanel() {
  queryMode.current = "success";
  mutationData.current = csvLatest;
  exportRecords.current = [csvHistory, zipHistory, folderHistory];
  return render(<ExportPanel projectId="project-1" />);
}

afterEach(() => {
  cleanup();
  window.__FRAMEPILOT_DESKTOP__ = undefined;
  nativeFsState.current = null;
  queryMode.current = "error";
  mutationData.current = undefined;
  mutationPending.current = false;
  exportRecords.current = [];
  exportSelection.mockReset();
  revealInFileManager.mockClear();
});

describe("ImportPanel", () => {
  it("shows project load errors", () => {
    render(<ImportPanel projectId="project-1" />);
    expect(screen.getAllByText("API offline").length).toBeGreaterThan(0);
  });

  it("shows the empty import chooser when the project loads with no active import", () => {
    queryMode.current = "success";
    render(<ImportPanel projectId="project-1" />);
    expect(screen.getByText("Choose image files")).toBeTruthy();
    expect(screen.getByText(/Choose a folder|Choose folder/i)).toBeTruthy();
  });

  it("keeps both browser file inputs including webkitdirectory", () => {
    const { container } = render(<ImportPanel projectId="project-1" />);
    const inputs = Array.from(container.querySelectorAll('input[type="file"]')) as HTMLInputElement[];
    expect(inputs).toHaveLength(2);
    expect(inputs[0]?.multiple).toBe(true);
    expect(inputs[1]?.multiple).toBe(true);
    expect(inputs[0]?.disabled).toBe(false);
    expect(inputs[1]?.disabled).toBe(false);
    expect(inputs[1]?.hasAttribute("webkitdirectory")).toBe(true);
    expect(inputs[0]?.closest("label")?.textContent).toContain("Choose image files");
    expect(inputs[1]?.closest("label")?.textContent).toContain("Choose a folder");
    expect(container.querySelectorAll("label input[type='file']")).toHaveLength(2);
  });
});

describe("ExportPanel", () => {
  it("shows project load errors", () => {
    render(<ExportPanel projectId="project-1" />);
    expect(screen.getAllByText("API offline").length).toBeGreaterThan(0);
  });

  it("shows an empty export history state", () => {
    queryMode.current = "success";
    mutationData.current = undefined;
    exportRecords.current = [];
    render(<ExportPanel projectId="project-1" />);
    expect(screen.getByText("No exports yet.")).toBeTruthy();
  });

  it("shows fine-grained running export progress in history", () => {
    queryMode.current = "success";
    mutationData.current = undefined;
    exportRecords.current = [
      {
        id: "export-running",
        project_id: "project-1",
        mode: "zip",
        status: "running",
        selected_count: 12,
        processed_count: 3,
        total_count: 12,
        statuses: '["Pick"]',
        include_xmp: false,
        output_path: "pending",
        error_message: null,
        completed_at: null,
        created_at: "2026-08-21T00:00:00Z",
      },
    ];
    render(<ExportPanel projectId="project-1" />);
    expect(screen.getByText("Running (3/12)")).toBeTruthy();
  });

  it("keeps browser download hrefs when the desktop flag is unset", () => {
    const { container } = renderSuccessfulExportPanel();

    expect(screen.queryByRole("button", { name: "Show in folder" })).toBeNull();
    expect(container.querySelector("a[download]")).toBeNull();

    expect(screen.getByRole("link", { name: "Download CSV" })).toHaveAttribute(
      "href",
      exportDownloadUrl("project-1", "export-latest"),
    );

    const historyDownloads = screen.getAllByRole("link", { name: "Download" });
    expect(historyDownloads).toHaveLength(2);
    expect(historyDownloads[0]).toHaveAttribute("href", exportDownloadUrl("project-1", "export-csv"));
    expect(historyDownloads[1]).toHaveAttribute("href", exportDownloadUrl("project-1", "export-zip"));
    expect(container.querySelectorAll('a[href*="/download"]')).toHaveLength(3);
  });

  it("replaces download anchors with Show in folder when __FRAMEPILOT_DESKTOP__ is true", async () => {
    window.__FRAMEPILOT_DESKTOP__ = true;
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
    };

    const { container } = renderSuccessfulExportPanel();

    expect(container.querySelector("a[download]")).toBeNull();
    expect(container.querySelectorAll('a[href*="/download"]')).toHaveLength(0);
    expect(screen.queryByRole("link", { name: "Download CSV" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Download" })).toBeNull();

    const revealButtons = screen.getAllByRole("button", { name: "Show in folder" });
    expect(revealButtons).toHaveLength(3);

    for (const button of revealButtons) {
      fireEvent.click(button);
    }

    await waitFor(() => {
      expect(revealInFileManager).toHaveBeenCalledWith("/projects/shoot/exports/csv/latest.csv");
      expect(revealInFileManager).toHaveBeenCalledWith("/projects/shoot/exports/csv/selection.csv");
      expect(revealInFileManager).toHaveBeenCalledWith("/projects/shoot/exports/zip/selection.zip");
    });
    expect(revealInFileManager).not.toHaveBeenCalledWith("/projects/shoot/exports/folders/selection-1");
  });

  it("keeps Write XMP sidecars unchecked by default", () => {
    queryMode.current = "success";
    render(<ExportPanel projectId="project-1" />);
    const checkbox = screen.getByRole("checkbox", { name: /Write XMP sidecars/i });
    expect(checkbox).not.toBeChecked();
  });

  it("posts include_xmp true when the XMP checkbox is checked", async () => {
    queryMode.current = "success";
    exportSelection.mockResolvedValue({
      ...csvLatest,
      include_xmp: true,
    });
    render(<ExportPanel projectId="project-1" />);
    fireEvent.click(screen.getByRole("checkbox", { name: /Write XMP sidecars/i }));
    fireEvent.click(screen.getByRole("button", { name: "Export" }));
    await waitFor(() => {
      expect(exportSelection).toHaveBeenCalledWith("project-1", "csv", expect.arrayContaining(["Pick"]), true);
    });
  });

  it("disables the XMP checkbox while an export is running", () => {
    queryMode.current = "success";
    mutationPending.current = true;
    render(<ExportPanel projectId="project-1" />);
    expect(screen.getByRole("checkbox", { name: /Write XMP sidecars/i })).toBeDisabled();
  });

  it("shows XMP in export history when include_xmp is true", () => {
    queryMode.current = "success";
    exportRecords.current = [{ ...zipHistory, include_xmp: true }];
    render(<ExportPanel projectId="project-1" />);
    expect(
      screen.getByText((_content, element) => {
        if (!(element instanceof HTMLElement) || element.tagName !== "P") {
          return false;
        }
        const text = element.textContent ?? "";
        return element.className.includes("font-medium") && text.includes("ZIP") && text.includes("XMP");
      }),
    ).toBeTruthy();
  });
});
