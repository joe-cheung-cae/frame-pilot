import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
const pathnameState = vi.hoisted(() => ({ current: "/projects/new" }));
const lastOpenedState = vi.hoisted(() => ({ current: null as string | null }));

vi.mock("@/lib/navigation", () => ({
  useNavigator: () => ({ push }),
  usePathname: () => pathnameState.current,
}));

vi.mock("@/lib/recentProjects", () => ({
  loadLastOpenedProjectId: () => lastOpenedState.current,
}));

import { MENU_EVENT } from "@/lib/menuRoutes";
import { MenuCommandListener } from "./MenuCommandListener";

describe("MenuCommandListener", () => {
  afterEach(() => {
    cleanup();
    push.mockReset();
    pathnameState.current = "/projects/new";
    lastOpenedState.current = null;
  });

  it("opens Export on the current project after create", () => {
    pathnameState.current = "/projects/project-1/import";
    render(<MenuCommandListener />);
    window.dispatchEvent(new CustomEvent(MENU_EVENT, { detail: "export" }));
    expect(push).toHaveBeenCalledWith("/projects/project-1/export");
  });

  it("shows a visible create-project prompt when Import has no project", () => {
    render(<MenuCommandListener />);
    window.dispatchEvent(new CustomEvent(MENU_EVENT, { detail: "import" }));
    expect(push).toHaveBeenCalledWith("/projects/new?workflow=import");
  });

  it("uses the last opened project when the create form is still open", () => {
    lastOpenedState.current = "project-1";
    render(<MenuCommandListener />);
    window.dispatchEvent(new CustomEvent(MENU_EVENT, { detail: "export" }));
    expect(push).toHaveBeenCalledWith("/projects/project-1/export");
  });
});
