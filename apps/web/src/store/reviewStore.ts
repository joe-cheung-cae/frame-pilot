import { create } from "zustand";

type ReviewState = {
  activePhotoId: string | null;
  activeGroupId: string | null;
  filter: string;
  compareMode: boolean;
  largePreview: boolean;
  zoomPreview: boolean;
  setReviewProgress: (progress: {
    activeGroupId: string | null;
    activePhotoId: string | null;
    compareMode: boolean;
    filter: string;
    largePreview: boolean;
    zoomPreview: boolean;
  }) => void;
  setActiveGroupId: (groupId: string | null) => void;
  setActivePhotoId: (photoId: string | null) => void;
  setFilter: (filter: string) => void;
  toggleCompareMode: () => void;
  toggleLargePreview: () => void;
  toggleZoomPreview: () => void;
};

export const useReviewStore = create<ReviewState>((set) => ({
  activePhotoId: null,
  activeGroupId: null,
  compareMode: false,
  filter: "All",
  largePreview: false,
  zoomPreview: false,
  setReviewProgress: (progress) => set(progress),
  setActiveGroupId: (activeGroupId) => set({ activeGroupId }),
  setActivePhotoId: (activePhotoId) => set({ activePhotoId }),
  setFilter: (filter) => set({ filter, activeGroupId: null }),
  toggleCompareMode: () => set((state) => ({ compareMode: !state.compareMode })),
  toggleLargePreview: () => set((state) => ({ largePreview: !state.largePreview })),
  toggleZoomPreview: () => set((state) => ({ zoomPreview: !state.zoomPreview })),
}));
