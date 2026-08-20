import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();

vi.mock("@/lib/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
  useNavigator: () => ({ push }),
  useQueryParams: () => new URLSearchParams(),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: ({ queryKey }: { queryKey: unknown[] }) => {
    if (queryKey[0] === "project") {
      return {
        isLoading: false,
        isError: false,
        isSuccess: true,
        data: {
          id: "project-1",
          name: "Demo",
          total_images: 0,
          processed_images: 0,
          active_import_job: null,
        },
        error: null,
      };
    }
    return {
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [],
      error: null,
    };
  },
  useMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    error: null,
    isError: false,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
  }),
}));

vi.mock("@/store/reviewStore", () => ({
  useReviewStore: () => ({
    activeGroupId: null,
    activePhotoId: null,
    compareMode: false,
    filter: "All",
    largePreview: false,
    previewZoom: 1,
    resetPreviewZoom: vi.fn(),
    setActiveGroupId: vi.fn(),
    setActivePhotoId: vi.fn(),
    setFilter: vi.fn(),
    setReviewProgress: vi.fn(),
    toggleCompareMode: vi.fn(),
    toggleLargePreview: vi.fn(),
    zoomPreviewIn: vi.fn(),
    zoomPreviewOut: vi.fn(),
  }),
}));

import { CullingWorkspace } from "./CullingWorkspace";

describe("CullingWorkspace", () => {
  beforeEach(() => {
    push.mockReset();
  });

  it("shows an empty import state when the project has no photos", () => {
    render(<CullingWorkspace projectId="project-1" />);
    expect(screen.getByText("No Photos Imported")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Import Images/i })).toBeTruthy();
  });
});
