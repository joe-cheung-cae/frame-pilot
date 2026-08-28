import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { maxRenderedVirtualItems } from "@/lib/virtualRenderBudget";

const push = vi.fn();
const updatePhoto = vi.fn();
const setQueryData = vi.fn();
const getQueryData = vi.fn();
const cancelQueries = vi.fn();

type PhotoFixture = {
  id: string;
  project_id: string;
  filename: string;
  file_ext: string;
  file_size: number;
  file_mtime: number | null;
  content_hash: string | null;
  project_copy_path: string | null;
  source_identity: string | null;
  width: number;
  height: number;
  capture_time: string | null;
  camera_model: string | null;
  lens_model: string | null;
  focal_length: string | null;
  aperture: string | null;
  shutter_speed: string | null;
  iso: number | null;
  thumbnail_path: string | null;
  preview_path: string | null;
  user_status: "Pick" | "Maybe" | "Reject" | "Unreviewed";
  star_rating: number;
  group_id: string | null;
  ai_recommendation: "Pick" | "Maybe" | "Reject" | "Unreviewed";
  overall_score: number;
  sharpness_score: number;
  exposure_score: number;
  contrast_score: number;
  noise_score: number;
  aesthetic_score: number;
  face_presence: boolean;
  face_count: number;
  face_sharpness_score: number;
  eye_open_confidence: number | null;
  face_quality_score: number;
  perceptual_hash: string | null;
  embedding_path: string | null;
  recommendation_explanation: string;
  processing_state: string;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
};

const { photosState } = vi.hoisted(() => ({
  photosState: { current: [] as PhotoFixture[] },
}));

function makePhoto(index: number, overrides: Partial<PhotoFixture> = {}): PhotoFixture {
  return {
    id: `photo-${index}`,
    project_id: "project-1",
    filename: `frame-${index}.jpg`,
    file_ext: ".jpg",
    file_size: 1000,
    file_mtime: null,
    content_hash: null,
    project_copy_path: null,
    source_identity: null,
    width: 100,
    height: 80,
    capture_time: null,
    camera_model: null,
    lens_model: null,
    focal_length: null,
    aperture: null,
    shutter_speed: null,
    iso: null,
    thumbnail_path: null,
    preview_path: null,
    user_status: "Unreviewed",
    star_rating: 0,
    group_id: null,
    ai_recommendation: "Unreviewed",
    overall_score: 0.5,
    sharpness_score: 0.5,
    exposure_score: 0.5,
    contrast_score: 0.5,
    noise_score: 0.1,
    aesthetic_score: 0.4,
    face_presence: false,
    face_count: 0,
    face_sharpness_score: 0,
    eye_open_confidence: null,
    face_quality_score: 0,
    perceptual_hash: null,
    embedding_path: null,
    recommendation_explanation: "Deterministic score.",
    processing_state: "processed",
    processing_error: null,
    created_at: "2026-08-21T00:00:00Z",
    updated_at: "2026-08-21T00:00:00Z",
    ...overrides,
  };
}

vi.mock("@/lib/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
  useNavigator: () => ({ push }),
  useQueryParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      getProject: vi.fn(async () => ({
        id: "project-1",
        name: "Demo",
        root_path: "/tmp/demo",
        source_mode: "copy",
        source_root_path: null,
        total_images: photosState.current.length,
        processed_images: photosState.current.length,
        last_processed_at: null,
        schema_version: 3,
        created_at: "2026-08-21T00:00:00Z",
        updated_at: "2026-08-21T00:00:00Z",
        active_import_job: null,
      })),
      listJobs: vi.fn(async () => []),
      listPhotos: vi.fn(async () => photosState.current),
      listAllPhotos: vi.fn(async () => photosState.current),
      listAllGroups: vi.fn(async () => []),
      updatePhoto: (...args: unknown[]) => updatePhoto(...args),
      batchUpdatePhotos: vi.fn(async () => []),
    },
    assetUrl: () => null,
  };
});

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
          total_images: photosState.current.length,
          processed_images: photosState.current.length,
          active_import_job: null,
        },
        error: null,
      };
    }
    if (queryKey[0] === "jobs") {
      return { isLoading: false, isError: false, isSuccess: true, data: [], error: null };
    }
    if (queryKey[0] === "photos") {
      return { isLoading: false, isError: false, isSuccess: true, data: photosState.current, error: null };
    }
    if (queryKey[0] === "groups") {
      return { isLoading: false, isError: false, isSuccess: true, data: [], error: null };
    }
    return { isLoading: false, isError: false, isSuccess: true, data: [], error: null };
  },
  useMutation: (options: {
    mutationFn: (input: unknown) => Promise<unknown>;
    onMutate?: (input: unknown) => Promise<unknown> | unknown;
    onError?: (error: Error, input: unknown, context: unknown) => void;
    onSuccess?: (data: unknown, input: unknown) => void;
  }) => ({
    mutate: (input: unknown) => {
      void (async () => {
        let context: unknown;
        try {
          context = options.onMutate ? await options.onMutate(input) : undefined;
          const result = await options.mutationFn(input);
          options.onSuccess?.(result, input);
        } catch (error) {
          options.onError?.(error as Error, input, context);
        }
      })();
    },
    isPending: false,
    error: null,
    isError: false,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
    setQueryData,
    getQueryData,
    cancelQueries,
  }),
}));

vi.mock("@/store/reviewStore", () => ({
  useReviewStore: () => ({
    activeGroupId: null,
    activePhotoId: photosState.current[0]?.id ?? null,
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

function mockFilmstripViewport(width = 960) {
  Object.defineProperty(HTMLElement.prototype, "clientWidth", {
    configurable: true,
    get() {
      return width;
    },
  });
  Object.defineProperty(HTMLElement.prototype, "clientHeight", {
    configurable: true,
    get() {
      return 80;
    },
  });
  Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
    configurable: true,
    get() {
      return width;
    },
  });
  Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
    configurable: true,
    get() {
      return 80;
    },
  });
  Object.defineProperty(HTMLElement.prototype, "getBoundingClientRect", {
    configurable: true,
    value() {
      return {
        width,
        height: 80,
        top: 0,
        left: 0,
        bottom: 80,
        right: width,
        x: 0,
        y: 0,
        toJSON() {
          return {};
        },
      };
    },
  });
}

describe("CullingWorkspace", () => {
  beforeEach(() => {
    push.mockReset();
    updatePhoto.mockReset();
    setQueryData.mockReset();
    getQueryData.mockReset();
    cancelQueries.mockReset();
    photosState.current = [];
    getQueryData.mockImplementation((key: unknown[]) => {
      if (key[0] === "photos") {
        return photosState.current;
      }
      return undefined;
    });
    setQueryData.mockImplementation((key: unknown[], updater: unknown) => {
      if (key[0] === "photos" && typeof updater === "function") {
        photosState.current = (updater as (current: PhotoFixture[]) => PhotoFixture[])(photosState.current);
      }
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("shows an empty import state when the project has no photos", () => {
    render(<CullingWorkspace projectId="project-1" />);
    expect(screen.getByText("No Photos Imported")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Import Images/i })).toBeTruthy();
  });

  it("keeps filmstrip DOM bounded for a 2000-photo workspace", async () => {
    photosState.current = Array.from({ length: 2000 }, (_value, index) => makePhoto(index));
    mockFilmstripViewport(960);
    const budget = maxRenderedVirtualItems({
      itemCount: 2000,
      viewportSize: 960,
      estimateSize: 120,
      overscan: 6,
    });

    render(<CullingWorkspace projectId="project-1" />);

    await waitFor(() => {
      expect(screen.getByLabelText("Photo filmstrip")).toBeTruthy();
    });

    const filmstrip = screen.getByLabelText("Photo filmstrip");
    const renderedOptions = within(filmstrip).queryAllByRole("option");
    expect(renderedOptions.length).toBeGreaterThan(0);
    expect(renderedOptions.length).toBeLessThanOrEqual(budget);
    expect(renderedOptions.length).toBeLessThan(100);
  });

  it("marks the active photo with a keyboard shortcut", async () => {
    photosState.current = [makePhoto(0), makePhoto(1)];
    updatePhoto.mockResolvedValue(makePhoto(0, { user_status: "Pick" }));

    render(<CullingWorkspace projectId="project-1" />);
    await waitFor(() => {
      expect(screen.getByLabelText("Photo filmstrip")).toBeTruthy();
    });

    fireEvent.keyDown(window, { key: "p" });

    await waitFor(() => {
      expect(updatePhoto).toHaveBeenCalled();
    });
    expect(updatePhoto.mock.calls[0]?.[0]).toBe("project-1");
    expect(updatePhoto.mock.calls[0]?.[1]).toBe("photo-0");
    expect(updatePhoto.mock.calls[0]?.[2]).toEqual({ user_status: "Pick" });
  });

  it("rolls back optimistic status when a save fails", async () => {
    photosState.current = [makePhoto(0, { user_status: "Unreviewed" }), makePhoto(1)];
    updatePhoto.mockRejectedValue(new Error("API offline"));

    render(<CullingWorkspace projectId="project-1" />);
    await waitFor(() => {
      expect(screen.getByLabelText("Photo filmstrip")).toBeTruthy();
    });

    fireEvent.keyDown(window, { key: "p" });

    await waitFor(() => {
      expect(updatePhoto).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(photosState.current[0]?.user_status).toBe("Unreviewed");
    });
  });
});
