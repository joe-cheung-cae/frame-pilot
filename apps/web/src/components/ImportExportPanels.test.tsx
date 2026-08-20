import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({
    isLoading: false,
    isError: true,
    error: new Error("API offline"),
    data: undefined,
    isSuccess: false,
    refetchInterval: false,
  }),
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

import { ExportPanel } from "./ExportPanel";
import { ImportPanel } from "./ImportPanel";

afterEach(() => {
  cleanup();
});

describe("ImportPanel", () => {
  it("shows project load errors", () => {
    render(<ImportPanel projectId="project-1" />);
    expect(screen.getAllByText("API offline").length).toBeGreaterThan(0);
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
});
