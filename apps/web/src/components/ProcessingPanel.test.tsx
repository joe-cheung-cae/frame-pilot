import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const queryMode = vi.hoisted(() => ({ current: "error" as "error" | "empty" | "success" }));

vi.mock("@/lib/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: ({ queryKey }: { queryKey: unknown[] }) => {
    if (queryMode.current === "error") {
      return {
        isLoading: false,
        isError: true,
        error: new Error("API offline"),
        data: undefined,
        isSuccess: false,
        isFetching: false,
      };
    }
    if (queryKey[0] === "project") {
      return {
        isLoading: false,
        isError: false,
        error: null,
        data: { id: "project-1", name: "Shoot", total_images: 0, processed_images: 0, active_import_job: null },
        isSuccess: true,
        isFetching: false,
      };
    }
    return {
      isLoading: false,
      isError: false,
      error: null,
      data: queryMode.current === "empty" ? [] : [{ id: "job-1", job_type: "processing", status: "complete", current_step: "complete" }],
      isSuccess: true,
      isFetching: false,
    };
  },
  useMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    error: null,
    data: undefined,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

import { ProcessingPanel } from "./ProcessingPanel";

afterEach(() => {
  cleanup();
  queryMode.current = "error";
});

describe("ProcessingPanel", () => {
  it("shows an error state when the project cannot be loaded", () => {
    render(<ProcessingPanel projectId="project-1" />);
    expect(screen.getAllByText("API offline").length).toBeGreaterThan(0);
  });

  it("shows an empty job history state", () => {
    queryMode.current = "empty";
    render(<ProcessingPanel projectId="project-1" />);
    expect(screen.getByText("No jobs yet.")).toBeTruthy();
  });
});
