import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { nativeFsState, revealInFileManager } = vi.hoisted(() => ({
  nativeFsState: {
    current: null as {
      pickDirectory: () => Promise<string | null>;
      pickImageFiles: () => Promise<string[] | null>;
      revealInFileManager: (targetPath: string) => Promise<void>;
      subscribeDragDrop: () => Promise<() => void>;
    } | null,
  },
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
      data: [
        {
          id: "export-1",
          project_id: "project-1",
          mode: "folder",
          status: "complete",
          selected_count: 2,
          statuses: '["Pick"]',
          output_path: "/projects/shoot/exports/folders/selection-1",
          error_message: null,
          completed_at: null,
          created_at: "2026-08-20T00:00:00Z",
        },
      ],
      isFetching: false,
    };
  },
  useMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    error: null,
    isError: false,
    data: undefined,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
  }),
}));

import { ExportPanel } from "./ExportPanel";

describe("ExportPanel reveal", () => {
  beforeEach(() => {
    cleanup();
    revealInFileManager.mockClear();
    nativeFsState.current = null;
  });

  it("hides Open export folder when native FS is unavailable", () => {
    render(<ExportPanel projectId="project-1" />);
    expect(screen.queryByRole("button", { name: "Open export folder" })).toBeNull();
  });

  it("reveals output_path when Open export folder is clicked", async () => {
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
    };
    render(<ExportPanel projectId="project-1" />);
    const buttons = screen.getAllByRole("button", { name: "Open export folder" });
    expect(buttons.length).toBeGreaterThan(0);
    fireEvent.click(buttons[buttons.length - 1]);
    await waitFor(() => {
      expect(revealInFileManager).toHaveBeenCalledWith("/projects/shoot/exports/folders/selection-1");
    });
  });
});
