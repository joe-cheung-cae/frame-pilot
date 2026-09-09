import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { nativeFsState, registerDesktopProjectRoot, queryParams } = vi.hoisted(() => ({
  nativeFsState: { current: null as { pickDirectory: () => Promise<string | null> } | null },
  registerDesktopProjectRoot: vi.fn(async (path: string) => ({ path })),
  queryParams: { current: new URLSearchParams() },
}));

vi.mock("@/lib/nativeFs", () => ({
  getNativeFs: () => nativeFsState.current,
}));

vi.mock("@/lib/navigation", () => ({
  useNavigator: () => ({ push: vi.fn() }),
  useQueryParams: () => queryParams.current,
}));

vi.mock("@/lib/api", () => ({
  api: {
    createProject: vi.fn(),
    registerDesktopProjectRoot: (path: string) => registerDesktopProjectRoot(path),
  },
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    error: null,
    isError: false,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

import { ProjectCreator } from "./ProjectCreator";

describe("ProjectCreator", () => {
  beforeEach(() => {
    cleanup();
    nativeFsState.current = null;
    registerDesktopProjectRoot.mockClear();
    queryParams.current = new URLSearchParams();
  });

  it("keeps the browser text field and hides Browse when native FS is unavailable", () => {
    render(<ProjectCreator />);
    expect(screen.getByPlaceholderText("/Users/name/Pictures/FramePilot project")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Browse" })).toBeNull();
  });

  it("explains that Import and Export need a project first", () => {
    queryParams.current = new URLSearchParams("workflow=export");
    render(<ProjectCreator />);
    expect(screen.getByText("Create a project before opening Export.")).toBeTruthy();
  });

  it("registers a picked directory then fills root_path", async () => {
    nativeFsState.current = {
      pickDirectory: async () => "/picked/folder",
    };
    const view = render(<ProjectCreator />);
    fireEvent.click(view.getByRole("button", { name: "Browse" }));
    await waitFor(() => {
      expect(registerDesktopProjectRoot).toHaveBeenCalledWith("/picked/folder");
    });
    expect((view.getByPlaceholderText("/Users/name/Pictures/FramePilot project") as HTMLInputElement).value).toBe(
      "/picked/folder",
    );
  });
});
