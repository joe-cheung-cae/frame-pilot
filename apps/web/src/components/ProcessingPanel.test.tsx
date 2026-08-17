import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({
    isLoading: false,
    isError: true,
    error: new Error("API offline"),
    data: undefined,
    isSuccess: false,
  }),
  useMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

import { ProcessingPanel } from "./ProcessingPanel";

describe("ProcessingPanel", () => {
  it("shows an error state when the project cannot be loaded", () => {
    render(<ProcessingPanel projectId="project-1" />);
    expect(screen.getAllByText("API offline").length).toBeGreaterThan(0);
  });
});
