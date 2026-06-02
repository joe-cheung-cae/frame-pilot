import { create } from "zustand";

type ReviewState = {
  activePhotoId: string | null;
  filter: string;
  largePreview: boolean;
  setActivePhotoId: (photoId: string | null) => void;
  setFilter: (filter: string) => void;
  toggleLargePreview: () => void;
};

export const useReviewStore = create<ReviewState>((set) => ({
  activePhotoId: null,
  filter: "All",
  largePreview: false,
  setActivePhotoId: (activePhotoId) => set({ activePhotoId }),
  setFilter: (filter) => set({ filter }),
  toggleLargePreview: () => set((state) => ({ largePreview: !state.largePreview })),
}));

