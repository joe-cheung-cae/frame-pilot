import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const pathnameState = vi.hoisted(() => ({ current: "/projects/project-1/import" }));

vi.mock("@/lib/navigation", () => ({
  Link: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    role?: string;
    "aria-selected"?: boolean;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
  usePathname: () => pathnameState.current,
}));

import { ProjectWorkflowNav } from "./ProjectWorkflowNav";

describe("ProjectWorkflowNav", () => {
  afterEach(() => {
    cleanup();
    pathnameState.current = "/projects/project-1/import";
  });

  it("hides workflow tabs on the create-project page", () => {
    pathnameState.current = "/projects/new";
    render(<ProjectWorkflowNav />);
    expect(screen.queryByRole("tablist", { name: "Project workflow" })).toBeNull();
  });

  it("opens Import and Export on their own pages for a new project", () => {
    render(<ProjectWorkflowNav />);
    const importTab = screen.getByRole("tab", { name: "Import" });
    const exportTab = screen.getByRole("tab", { name: "Export" });
    expect(importTab).toHaveAttribute("href", "/projects/project-1/import");
    expect(importTab).toHaveAttribute("aria-selected", "true");
    expect(exportTab).toHaveAttribute("href", "/projects/project-1/export");
    expect(exportTab).toHaveAttribute("aria-selected", "false");
  });
});
