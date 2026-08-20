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
  useQuery: () => ({
    isLoading: false,
    isError: false,
    error: null,
    data: {
      id: "project-1",
      name: "Shoot",
      root_path: "/projects/shoot",
      total_images: 0,
      processed_images: 0,
      pick_count: 0,
      maybe_count: 0,
      reject_count: 0,
      unreviewed_count: 0,
    },
  }),
}));

import { ProjectDashboard } from "./ProjectDashboard";

describe("ProjectDashboard reveal", () => {
  beforeEach(() => {
    cleanup();
    revealInFileManager.mockClear();
    nativeFsState.current = null;
  });

  it("hides Open project folder when native FS is unavailable", () => {
    render(<ProjectDashboard projectId="project-1" />);
    expect(screen.queryByRole("button", { name: "Open project folder" })).toBeNull();
  });

  it("reveals root_path when Open project folder is clicked", async () => {
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager,
      subscribeDragDrop: async () => () => undefined,
    };
    render(<ProjectDashboard projectId="project-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Open project folder" }));
    await waitFor(() => {
      expect(revealInFileManager).toHaveBeenCalledWith("/projects/shoot");
    });
  });
});
