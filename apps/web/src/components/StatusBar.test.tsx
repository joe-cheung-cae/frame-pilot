import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
  usePathname: () => "/projects/project-1/cull",
}));

vi.mock("@/lib/recentProjects", () => ({
  loadLastOpenedProjectId: () => "project-1",
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: ({ queryKey }: { queryKey: unknown[] }) => {
    if (queryKey[0] === "health") {
      return {
        isLoading: false,
        isError: false,
        isSuccess: true,
        data: { status: "ok", version: "2.0.0-rc2", service: "framepilot-api" },
        error: null,
      };
    }
    if (queryKey[0] === "project") {
      return {
        isLoading: false,
        isError: false,
        isSuccess: true,
        data: { id: "project-1", name: "Coast shoot" },
        error: null,
      };
    }
    if (queryKey[0] === "jobs") {
      return {
        isLoading: false,
        isError: false,
        isSuccess: true,
        data: [
          {
            id: "job-1",
            job_type: "processing",
            status: "running",
            current_step: "Building groups",
            progress_percent: 42.4,
            processed_items: 8,
            total_items: 20,
            failed_items: 0,
          },
        ],
        error: null,
      };
    }
    return { isLoading: false, isError: false, isSuccess: true, data: undefined, error: null };
  },
}));

import { Shell } from "./Shell";
import { StatusBar } from "./StatusBar";

describe("StatusBar", () => {
  afterEach(() => {
    cleanup();
    delete window.__FRAMEPILOT_DESKTOP__;
  });

  it("does not render a status region in the browser shell", () => {
    render(
      <Shell>
        <p>Child</p>
      </Shell>,
    );
    expect(screen.queryByRole("status")).toBeNull();
    expect(screen.getByRole("link", { name: "Help" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Settings" })).toBeTruthy();
    expect(screen.getByRole("link", { name: /New Project/ })).toBeTruthy();
    expect(screen.getByText("Child")).toBeTruthy();
    expect(StatusBar()).toBeNull();
  });

  it("renders sidecar, project, and job when isDesktopShell is true", () => {
    window.__FRAMEPILOT_DESKTOP__ = true;
    render(
      <Shell>
        <p>Child</p>
      </Shell>,
    );
    const status = screen.getByRole("status");
    expect(status.textContent).toContain("Sidecar connected");
    expect(status.textContent).toContain("Coast shoot");
    expect(status.textContent).toContain("Grouping and ranking");
    expect(status.textContent).toContain("Building groups");
    expect(status.textContent).toContain("42%");
    expect(screen.getByRole("link", { name: "Help" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Settings" })).toBeTruthy();
    expect(screen.getByRole("link", { name: /New Project/ })).toBeTruthy();
  });
});
