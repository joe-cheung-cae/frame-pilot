import { create } from "zustand";

type ReviewState = {
  activePhotoId: string | null;
  activeGroupId: string | null;
  filter: string;
  largePreview: boolean;
  setActiveGroupId: (groupId: string | null) => void;
  setActivePhotoId: (photoId: string | null) => void;
  setFilter: (filter: string) => void;
  toggleLargePreview: () => void;
};

export const useReviewStore = create<ReviewState>((set) => ({
  activePhotoId: null,
  activeGroupId: null,
  filter: "All",
  largePreview: false,
  setActiveGroupId: (activeGroupId) => set({ activeGroupId }),
  setActivePhotoId: (activePhotoId) => set({ activePhotoId }),
  setFilter: (filter) => set({ filter, activeGroupId: null }),
  toggleLargePreview: () => set((state) => ({ largePreview: !state.largePreview })),
}));
