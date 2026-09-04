import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

type NativeDragDropHandler = (event: { type: "enter" | "over" | "drop" | "leave"; paths?: string[] }) => void;

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
      subscribeDragDrop: (handler: NativeDragDropHandler) => Promise<() => void>;
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
    importPhotos,
    importPhotosFromPaths,
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

import { IMPORT_IMAGE_ACCEPT, ImportPanel } from "./ImportPanel";

function fileWithPath(filePath: string, name = "a.jpg"): File {
  const file = new File(["jpeg"], name, { type: "image/jpeg" });
  Object.defineProperty(file, "path", { value: filePath });
  return file;
}

function filesDataTransfer(files: File[]) {
  return {
    files,
    items: files.map((file) => ({ kind: "file", type: file.type, getAsFile: () => file })),
    types: ["Files"],
    dropEffect: "copy",
    effectAllowed: "all",
    getData: () => "",
  };
}

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

  it("accepts HEIC/HEIF on file inputs in addition to JPEG PNG WebP", () => {
    const { container } = render(<ImportPanel projectId="project-1" />);
    const inputs = [...container.querySelectorAll('input[type="file"]')];
    expect(inputs).toHaveLength(2);
    for (const input of inputs) {
      expect(input.getAttribute("accept")).toBe(IMPORT_IMAGE_ACCEPT);
    }
    expect(IMPORT_IMAGE_ACCEPT).toContain("image/jpeg");
    expect(IMPORT_IMAGE_ACCEPT).toContain("image/png");
    expect(IMPORT_IMAGE_ACCEPT).toContain("image/webp");
    expect(IMPORT_IMAGE_ACCEPT).toContain("image/heic");
    expect(IMPORT_IMAGE_ACCEPT).toContain("image/heif");
    expect(IMPORT_IMAGE_ACCEPT).toContain(".heic");
    expect(IMPORT_IMAGE_ACCEPT).toContain(".heif");
    expect(screen.getByText("JPEG, PNG, WebP, and HEIC/HEIF are supported. RAW files are skipped.")).toBeTruthy();
  });

  it("picks image files then imports from local paths", async () => {
    desktopShell.current = true;
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => ["/abs/a.jpg", "/abs/b.png"],
      revealInFileManager: async () => undefined,
      subscribeDragDrop: async () => () => undefined,
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
      subscribeDragDrop: async () => () => undefined,
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
      subscribeDragDrop: async () => () => undefined,
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

describe("ImportPanel drag and drop", () => {
  beforeEach(() => {
    cleanup();
    desktopShell.current = false;
    nativeFsState.current = null;
    importPhotos.mockClear();
    importPhotosFromPaths.mockClear();
  });

  it("keeps the drop overlay pointer-events none until a drag is active", () => {
    const { container } = render(<ImportPanel projectId="project-1" />);
    const overlay = container.querySelector('[data-testid="import-drop-overlay"]');
    expect(overlay).toBeTruthy();
    expect((overlay as HTMLElement).style.pointerEvents).toBe("none");
    expect(container.querySelectorAll('input[type="file"]')).toHaveLength(2);

    fireEvent.dragEnter(window, { dataTransfer: filesDataTransfer([]) });
    expect((overlay as HTMLElement).style.pointerEvents).toBe("auto");

    fireEvent.dragLeave(window, { dataTransfer: filesDataTransfer([]), relatedTarget: null });
    expect((overlay as HTMLElement).style.pointerEvents).toBe("none");
  });

  it("imports dropped filesystem paths via from-paths and never multipart", async () => {
    render(<ImportPanel projectId="project-1" />);
    fireEvent.drop(window, {
      dataTransfer: filesDataTransfer([fileWithPath("/abs/drop.jpg", "drop.jpg"), fileWithPath("/abs/card")]),
    });
    await waitFor(() => {
      expect(importPhotosFromPaths).toHaveBeenCalledWith(
        "project-1",
        ["/abs/drop.jpg", "/abs/card"],
        expect.any(Object),
      );
    });
    expect(importPhotos).not.toHaveBeenCalled();
  });

  it("does not import when a drop has no filesystem paths", async () => {
    render(<ImportPanel projectId="project-1" />);
    const file = new File(["jpeg"], "upload.jpg", { type: "image/jpeg" });
    fireEvent.drop(window, { dataTransfer: filesDataTransfer([file]) });
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Import Images" })).toBeTruthy();
    });
    expect(importPhotosFromPaths).not.toHaveBeenCalled();
    expect(importPhotos).not.toHaveBeenCalled();
  });

  it("uses Tauri drag-drop paths when HTML5 drop has no filesystem paths", async () => {
    let onDragDrop: NativeDragDropHandler | undefined;
    desktopShell.current = true;
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager: async () => undefined,
      subscribeDragDrop: async (handler) => {
        onDragDrop = handler;
        return () => {
          onDragDrop = undefined;
        };
      },
    };
    render(<ImportPanel projectId="project-1" />);
    await waitFor(() => {
      expect(onDragDrop).toEqual(expect.any(Function));
    });
    onDragDrop?.({ type: "drop", paths: ["/abs/from-tauri.jpg"] });
    await waitFor(() => {
      expect(importPhotosFromPaths).toHaveBeenCalledWith("project-1", ["/abs/from-tauri.jpg"], expect.any(Object));
    });
    expect(importPhotos).not.toHaveBeenCalled();
  });

  it("does not import twice when HTML5 already supplied filesystem paths", async () => {
    let onDragDrop: NativeDragDropHandler | undefined;
    desktopShell.current = true;
    nativeFsState.current = {
      pickDirectory: async () => null,
      pickImageFiles: async () => null,
      revealInFileManager: async () => undefined,
      subscribeDragDrop: async (handler) => {
        onDragDrop = handler;
        return () => {
          onDragDrop = undefined;
        };
      },
    };
    render(<ImportPanel projectId="project-1" />);
    await waitFor(() => {
      expect(onDragDrop).toEqual(expect.any(Function));
    });
    fireEvent.drop(window, { dataTransfer: filesDataTransfer([fileWithPath("/abs/html5.jpg")]) });
    onDragDrop?.({ type: "drop", paths: ["/abs/html5.jpg"] });
    await waitFor(() => {
      expect(importPhotosFromPaths).toHaveBeenCalledTimes(1);
    });
    expect(importPhotosFromPaths).toHaveBeenCalledWith("project-1", ["/abs/html5.jpg"], expect.any(Object));
  });
});
