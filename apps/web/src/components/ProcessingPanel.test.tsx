import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const queryMode = vi.hoisted(() => ({
  current: "error" as "error" | "empty" | "success" | "running" | "cancelling" | "cancelled",
}));

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
        data: {
          id: "project-1",
          name: "Shoot",
          total_images: queryMode.current === "empty" || queryMode.current === "success" ? 0 : 3,
          processed_images: 0,
          active_import_job: null,
        },
        isSuccess: true,
        isFetching: false,
      };
    }
    const runningJob = {
      id: "job-1",
      job_type: "processing",
      status: "running",
      current_step: "grouping photos",
      cancellation_requested: false,
      failed_items: 0,
      processed_items: 1,
      progress_percent: 33,
      retryable: false,
      total_items: 3,
    };
    const displayedJob =
      queryMode.current === "cancelling"
        ? { ...runningJob, cancellation_requested: true, current_step: "cancellation_requested" }
        : queryMode.current === "cancelled"
          ? {
              ...runningJob,
              status: "cancelled",
              current_step: "cancelled",
              cancellation_requested: true,
              progress_percent: 33,
            }
          : queryMode.current === "running"
            ? runningJob
            : { id: "job-1", job_type: "processing", status: "complete", current_step: "complete" };
    if (queryKey[0] === "job") {
      return {
        isLoading: false,
        isError: false,
        error: null,
        data: queryMode.current === "empty" ? undefined : displayedJob,
        isSuccess: true,
        isFetching: false,
      };
    }
    return {
      isLoading: false,
      isError: false,
      error: null,
      data: queryMode.current === "empty" ? [] : [displayedJob],
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

  it("shows cancel control while grouping and ranking is running", () => {
    queryMode.current = "running";
    render(<ProcessingPanel projectId="project-1" />);
    expect(screen.getByRole("button", { name: "Cancel Grouping and Ranking" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Run Grouping and Ranking" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("hides cancel control while processing cancellation is pending", () => {
    queryMode.current = "cancelling";
    render(<ProcessingPanel projectId="project-1" />);
    expect(screen.queryByRole("button", { name: "Cancel Grouping and Ranking" })).toBeNull();
    expect(screen.getByText("Cancellation requested. FramePilot will stop after a safe checkpoint.")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Run Grouping and Ranking" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("hides cancel control after processing is cancelled and enables a new run", () => {
    queryMode.current = "cancelled";
    render(<ProcessingPanel projectId="project-1" />);
    expect(screen.queryByRole("button", { name: "Cancel Grouping and Ranking" })).toBeNull();
    expect(
      screen.getByText("Processing stopped at a safe checkpoint. Run grouping and ranking again when you are ready."),
    ).toBeTruthy();
    expect((screen.getByRole("button", { name: "Run Grouping and Ranking" }) as HTMLButtonElement).disabled).toBe(
      false,
    );
    expect(screen.queryByRole("button", { name: "Retry Grouping and Ranking" })).toBeNull();
  });
});
