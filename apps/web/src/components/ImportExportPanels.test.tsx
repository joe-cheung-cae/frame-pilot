import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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

describe("ImportPanel", () => {
  it("shows project load errors", () => {
    render(<ImportPanel projectId="project-1" />);
    expect(screen.getAllByText("API offline").length).toBeGreaterThan(0);
  });
});

describe("ExportPanel", () => {
  it("shows project load errors", () => {
    render(<ExportPanel projectId="project-1" />);
    expect(screen.getAllByText("API offline").length).toBeGreaterThan(0);
  });
});
