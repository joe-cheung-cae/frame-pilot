import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { desktopShell, importPhotos, importPhotosFromPaths, nativeFsState } = vi.hoisted(() => ({
  desktopShell: { current: false },
  importPhotos: vi.fn(),
  importPhotosFromPaths: vi.fn(async () => ({
    imported: [],
    skipped: [],
    remaining_paths: [],
    expanded_total: 0,
  })),
  nativeFsState: {
    current: null as {
      pickDirectory: () => Promise<string | null>;
      pickImageFiles: () => Promise<string[] | null>;
      revealInFileManager: (targetPath: string) => Promise<void>;
    } | null,
  },
}));

vi.mock("@/lib/shell", () => ({
  isDesktopShell: () => desktopShell.current,
}));

vi.mock("@/lib/nativeFs", () => ({
  getNativeFs: () => nativeFsState.current,
}));

vi.mock("@/lib/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@/lib/api", () => ({
  api: {
    importPhotos: (...args: unknown[]) => importPhotos(...args),
    importPhotosFromPaths: (...args: unknown[]) => importPhotosFromPaths(...args),
  },
  assetUrl: () => null,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: ({ queryKey }: { queryKey: unknown[] }) => {
    if (queryKey[0] === "project") {
      return {
        isLoading: false,
        isError: false,
        error: null,
        data: { name: "Shoot", root_path: "/tmp/project", total_images: 0 },
      };
    }
    return { isLoading: false, isError: false, error: null, data: [] };
  },
  useMutation: ({ mutationFn }: { mutationFn: (input: unknown) => Promise<unknown> }) => ({
    mutate: (input: unknown) => {
      void mutationFn(input);
    },
    isPending: false,
    error: null,
    isError: false,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

import { ImportPanel } from "./ImportPanel";

describe("ImportPanel desktop path import", () => {
  beforeEach(() => {
    cleanup();
    desktopShell.current = false;
    nativeFsState.current = null;
    importPhotos.mockClear();
    importPhotosFromPaths.mockClear();
  });

  it("keeps both file inputs when the desktop shell flag is false", () => {
    const { container } = render(<ImportPanel projectId="project-1" />);
    expect(container.querySelectorAll('input[type="file"]')).toHaveLength(2);
    expect(screen.queryByRole("button", { name: /Choose image files/ })).toBeNull();
  });

  it("picks image files then imports from local paths", async () => {
    desktopShell.current = true;
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => ["/abs/a.jpg", "/abs/b.png"],
      revealInFileManager: async () => undefined,
    };
    const { container } = render(<ImportPanel projectId="project-1" />);
    expect(container.querySelectorAll('input[type="file"]')).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: /Choose image files/ }));
    await waitFor(() => {
      expect(importPhotosFromPaths).toHaveBeenCalledTimes(1);
    });
    expect(importPhotosFromPaths).toHaveBeenCalledWith("project-1", ["/abs/a.jpg", "/abs/b.png"], expect.any(Object));
    expect(importPhotos).not.toHaveBeenCalled();
  });

  it("picks a folder then imports from that local path", async () => {
    desktopShell.current = true;
    nativeFsState.current = {
      pickDirectory: async () => "/abs/card",
      pickImageFiles: async () => null,
      revealInFileManager: async () => undefined,
    };
    render(<ImportPanel projectId="project-1" />);
    fireEvent.click(screen.getByRole("button", { name: /Choose a folder/ }));
    await waitFor(() => {
      expect(importPhotosFromPaths).toHaveBeenCalledWith("project-1", ["/abs/card"], expect.any(Object));
    });
    expect(importPhotos).not.toHaveBeenCalled();
  });

  it("does not start path import when the native picker is cancelled", async () => {
    desktopShell.current = true;
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager: async () => undefined,
    };
    render(<ImportPanel projectId="project-1" />);
    fireEvent.click(screen.getByRole("button", { name: /Choose image files/ }));
    fireEvent.click(screen.getByRole("button", { name: /Choose a folder/ }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Choose a folder/ })).toBeTruthy();
    });
    expect(importPhotosFromPaths).not.toHaveBeenCalled();
  });
});
