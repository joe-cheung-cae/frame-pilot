import { create } from "zustand";

import { reviewProgressAfterFilterChange, type ReviewProgress } from "@/lib/reviewProgress";

type ReviewState = {
  activePhotoId: string | null;
  activeGroupId: string | null;
  filter: string;
  compareMode: boolean;
  largePreview: boolean;
  previewZoom: number;
  setReviewProgress: (progress: ReviewProgress) => void;
  setActiveGroupId: (groupId: string | null) => void;
  setActivePhotoId: (photoId: string | null) => void;
  setFilter: (filter: string) => void;
  toggleCompareMode: () => void;
  toggleLargePreview: () => void;
  resetPreviewZoom: () => void;
  zoomPreviewIn: () => void;
  zoomPreviewOut: () => void;
};

const PREVIEW_ZOOM_STEP = 0.25;
const MIN_PREVIEW_ZOOM = 0.25;
const MAX_PREVIEW_ZOOM = 4;

function clampPreviewZoom(zoom: number): number {
  return Math.min(Math.max(zoom, MIN_PREVIEW_ZOOM), MAX_PREVIEW_ZOOM);
}

export const useReviewStore = create<ReviewState>((set) => ({
  activePhotoId: null,
  activeGroupId: null,
  compareMode: false,
  filter: "All",
  largePreview: false,
  previewZoom: 1,
  setReviewProgress: (progress) => set(progress),
  setActiveGroupId: (activeGroupId) => set({ activeGroupId }),
  setActivePhotoId: (activePhotoId) => set({ activePhotoId }),
  setFilter: (filter) => set((state) => reviewProgressAfterFilterChange(state, filter)),
  toggleCompareMode: () => set((state) => ({ compareMode: !state.compareMode })),
  toggleLargePreview: () => set((state) => ({ largePreview: !state.largePreview })),
  resetPreviewZoom: () => set({ previewZoom: 1 }),
  zoomPreviewIn: () => set((state) => ({ previewZoom: clampPreviewZoom(state.previewZoom + PREVIEW_ZOOM_STEP) })),
  zoomPreviewOut: () => set((state) => ({ previewZoom: clampPreviewZoom(state.previewZoom - PREVIEW_ZOOM_STEP) })),
}));
