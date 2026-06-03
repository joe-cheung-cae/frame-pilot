"use client";

/* eslint-disable @next/next/no-img-element */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Columns2,
  Eye,
  ImageOff,
  Loader2,
  Play,
  Star,
  StarOff,
  Upload,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { api, assetUrl, Photo, PhotoPatch } from "@/lib/api";
import { applyStatusCountChange, type ExportStatus } from "@/lib/exportSelection";
import { groupConfidenceLabel, parseGroupScoreSummary } from "@/lib/groupScoreSummary";
import { parseReviewProgress, reviewProgressStorageKey } from "@/lib/reviewProgress";
import {
  groupAfterMove,
  nextPhotoIdAfterMark,
  windowedCompareRefs,
  windowedGroupRefs,
  windowedPhotoRefs,
} from "@/lib/reviewNavigation";
import { reviewShortcutCommandForKey, reviewShortcutNeedsPreventDefault } from "@/lib/reviewShortcuts";
import { useReviewStore } from "@/store/reviewStore";

const FILTERS = [
  "All",
  "Picks",
  "Maybes",
  "Rejects",
  "Unreviewed",
  "AI recommended",
  "Blurry photos",
  "Duplicate groups",
  "Photos with faces",
];

const FILMSTRIP_WINDOW_SIZE = 80;
const GROUP_WINDOW_SIZE = 80;
const COMPARE_WINDOW_SIZE = 6;

function statusForFilter(photo: Photo, filter: string, duplicateGroupIds: Set<string>) {
  if (filter === "All") return true;
  if (filter === "Picks") return photo.user_status === "Pick";
  if (filter === "Maybes") return photo.user_status === "Maybe";
  if (filter === "Rejects") return photo.user_status === "Reject";
  if (filter === "Unreviewed") return photo.user_status === "Unreviewed";
  if (filter === "AI recommended") return photo.ai_recommendation === "Pick";
  if (filter === "Blurry photos") return photo.blur_score >= 0.55;
  if (filter === "Duplicate groups") return Boolean(photo.group_id && duplicateGroupIds.has(photo.group_id));
  if (filter === "Photos with faces") return photo.face_presence;
  return true;
}

function formatCaptureTime(value: string | null): string | null {
  return value ? value.replace("T", " ").slice(0, 16) : null;
}

export function CullingWorkspace({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const filterButtonRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const skipNextProgressSave = useRef<string | null>(null);
  const project = useQuery({ queryKey: ["project", projectId], queryFn: () => api.getProject(projectId) });
  const photosQuery = useQuery({ queryKey: ["photos", projectId], queryFn: () => api.listAllPhotos(projectId) });
  const groupsQuery = useQuery({ queryKey: ["groups", projectId], queryFn: () => api.listAllGroups(projectId) });
  const {
    activeGroupId,
    activePhotoId,
    compareMode,
    filter,
    largePreview,
    zoomPreview,
    setActiveGroupId,
    setActivePhotoId,
    setFilter,
    setReviewProgress,
    toggleCompareMode,
    toggleLargePreview,
    toggleZoomPreview,
  } = useReviewStore();
  const photos = useMemo(() => photosQuery.data ?? [], [photosQuery.data]);
  const groups = useMemo(() => groupsQuery.data ?? [], [groupsQuery.data]);
  const duplicateGroupIds = useMemo(
    () => new Set(groups.filter((group) => group.photo_count > 1).map((group) => group.id)),
    [groups],
  );
  const filteredPhotos = useMemo(
    () => photos.filter((photo) => statusForFilter(photo, filter, duplicateGroupIds)),
    [duplicateGroupIds, filter, photos],
  );
  const visiblePhotos = useMemo(() => {
    if (!activeGroupId) {
      return filteredPhotos;
    }
    return filteredPhotos.filter((photo) => photo.group_id === activeGroupId);
  }, [activeGroupId, filteredPhotos]);
  const activeIndex = Math.max(
    0,
    visiblePhotos.findIndex((photo) => photo.id === activePhotoId),
  );
  const activePhoto = visiblePhotos[activeIndex] ?? visiblePhotos[0] ?? null;
  const activeGroup = useMemo(() => {
    const groupId = activePhoto?.group_id ?? activeGroupId;
    return groupId ? (groups.find((group) => group.id === groupId) ?? null) : null;
  }, [activeGroupId, activePhoto?.group_id, groups]);
  const groupIndexById = useMemo(() => new Map(groups.map((group, index) => [group.id, index])), [groups]);
  const activeGroupIndex = activeGroup ? (groupIndexById.get(activeGroup.id) ?? -1) : -1;
  const activeGroupSummary = useMemo(
    () => parseGroupScoreSummary(activeGroup?.score_summary),
    [activeGroup?.score_summary],
  );
  const compareCandidates = useMemo(() => {
    if (!activeGroup) {
      return activePhoto ? [activePhoto] : [];
    }
    return filteredPhotos.filter((photo) => photo.group_id === activeGroup.id);
  }, [activeGroup, activePhoto, filteredPhotos]);
  const comparePhotos = useMemo(
    () => windowedCompareRefs(compareCandidates, activePhoto?.id ?? null, COMPARE_WINDOW_SIZE),
    [activePhoto?.id, compareCandidates],
  );
  const filmstripPhotos = useMemo(
    () => windowedPhotoRefs(visiblePhotos, activePhoto?.id ?? null, FILMSTRIP_WINDOW_SIZE),
    [activePhoto?.id, visiblePhotos],
  );
  const sidebarGroups = useMemo(
    () => windowedGroupRefs(groups, activeGroup?.id ?? activeGroupId, GROUP_WINDOW_SIZE),
    [activeGroup?.id, activeGroupId, groups],
  );
  const visiblePhotoIds = useMemo(() => visiblePhotos.map((photo) => photo.id), [visiblePhotos]);
  const metadataRows = useMemo(() => {
    if (!activePhoto) {
      return [];
    }
    return [
      ["Captured", formatCaptureTime(activePhoto.capture_time)],
      ["Camera", activePhoto.camera_model],
      ["Lens", activePhoto.lens_model],
      ["Focal length", activePhoto.focal_length ? `${activePhoto.focal_length} mm` : null],
      ["Aperture", activePhoto.aperture ? `f/${activePhoto.aperture}` : null],
      ["Shutter", activePhoto.shutter_speed],
      ["ISO", activePhoto.iso ? String(activePhoto.iso) : null],
    ].filter((row): row is [string, string] => Boolean(row[1]));
  }, [activePhoto]);
  const photoStatusCountsQueryKey = useMemo(() => ["photo-status-counts", projectId], [projectId]);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = window.localStorage.getItem(reviewProgressStorageKey(projectId));
    } catch {
      stored = null;
    }
    skipNextProgressSave.current = projectId;
    setReviewProgress(parseReviewProgress(stored, FILTERS));
  }, [projectId, setReviewProgress]);

  useEffect(() => {
    if (skipNextProgressSave.current === projectId) {
      skipNextProgressSave.current = null;
      return;
    }

    try {
      window.localStorage.setItem(
        reviewProgressStorageKey(projectId),
        JSON.stringify({
          activeGroupId,
          activePhotoId,
          compareMode,
          filter,
          largePreview,
          zoomPreview,
        }),
      );
    } catch {
      // Keep review usable if browser storage is unavailable.
    }
  }, [activeGroupId, activePhotoId, compareMode, filter, largePreview, projectId, zoomPreview]);

  const updateMutation = useMutation({
    mutationFn: ({ photo, patch }: { photo: Photo; patch: PhotoPatch }) => api.updatePhoto(projectId, photo.id, patch),
    onMutate: async ({ photo, patch }) => {
      const queryKey = ["photos", projectId];
      await queryClient.cancelQueries({ queryKey });
      const previousPhotos = queryClient.getQueryData<Photo[]>(queryKey);
      const previousStatusCounts =
        queryClient.getQueryData<Record<ExportStatus, number>>(photoStatusCountsQueryKey);
      queryClient.setQueryData<Photo[]>(queryKey, (currentPhotos) =>
        currentPhotos?.map((item) => (item.id === photo.id ? { ...item, ...patch } : item)),
      );
      if (patch.user_status) {
        const nextStatus = patch.user_status;
        queryClient.setQueryData<Record<ExportStatus, number>>(photoStatusCountsQueryKey, (currentCounts) =>
          currentCounts ? applyStatusCountChange(currentCounts, photo.user_status, nextStatus) : currentCounts,
        );
      }
      return { previousPhotos, previousStatusCounts };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousPhotos) {
        queryClient.setQueryData(["photos", projectId], context.previousPhotos);
      }
      if (context?.previousStatusCounts) {
        queryClient.setQueryData(photoStatusCountsQueryKey, context.previousStatusCounts);
      }
    },
    onSuccess: (updatedPhoto) => {
      queryClient.setQueryData<Photo[]>(["photos", projectId], (currentPhotos) =>
        currentPhotos?.map((item) => (item.id === updatedPhoto.id ? updatedPhoto : item)),
      );
    },
  });

  const batchUpdateMutation = useMutation({
    mutationFn: ({ photoIds, patch }: { photoIds: string[]; patch: PhotoPatch }) =>
      api.batchUpdatePhotos(projectId, photoIds, patch),
    onMutate: async ({ photoIds, patch }) => {
      const queryKey = ["photos", projectId];
      const targetIds = new Set(photoIds);
      await queryClient.cancelQueries({ queryKey });
      const previousPhotos = queryClient.getQueryData<Photo[]>(queryKey);
      const previousStatusCounts =
        queryClient.getQueryData<Record<ExportStatus, number>>(photoStatusCountsQueryKey);
      queryClient.setQueryData<Photo[]>(queryKey, (currentPhotos) =>
        currentPhotos?.map((item) => (targetIds.has(item.id) ? { ...item, ...patch } : item)),
      );
      if (patch.user_status && previousPhotos) {
        const nextStatus = patch.user_status;
        const targetPhotos = previousPhotos.filter((photo) => targetIds.has(photo.id));
        queryClient.setQueryData<Record<ExportStatus, number>>(photoStatusCountsQueryKey, (currentCounts) =>
          currentCounts
            ? targetPhotos.reduce(
                (counts, photo) => applyStatusCountChange(counts, photo.user_status, nextStatus),
                currentCounts,
              )
            : currentCounts,
        );
      }
      return { previousPhotos, previousStatusCounts };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousPhotos) {
        queryClient.setQueryData(["photos", projectId], context.previousPhotos);
      }
      if (context?.previousStatusCounts) {
        queryClient.setQueryData(photoStatusCountsQueryKey, context.previousStatusCounts);
      }
    },
    onSuccess: (updatedPhotos) => {
      const updatedById = new Map(updatedPhotos.map((photo) => [photo.id, photo]));
      queryClient.setQueryData<Photo[]>(["photos", projectId], (currentPhotos) =>
        currentPhotos?.map((item) => updatedById.get(item.id) ?? item),
      );
    },
  });

  useEffect(() => {
    if (!activePhotoId && activePhoto) {
      setActivePhotoId(activePhoto.id);
    }
  }, [activePhoto, activePhotoId, setActivePhotoId]);

  useEffect(() => {
    if (activePhoto && activePhoto.id !== activePhotoId) {
      setActivePhotoId(activePhoto.id);
    }
  }, [activePhoto, activePhotoId, setActivePhotoId]);

  function move(delta: number) {
    if (!visiblePhotos.length) return;
    const next = Math.min(Math.max(activeIndex + delta, 0), visiblePhotos.length - 1);
    setActivePhotoId(visiblePhotos[next].id);
  }

  function selectGroup(groupId: string | null, representativePhotoId?: string | null) {
    setActiveGroupId(groupId);
    if (representativePhotoId) {
      setActivePhotoId(representativePhotoId);
    }
  }

  function cycleGroup() {
    if (!groups.length) return;
    const nextIndex = activeGroupIndex >= 0 ? (activeGroupIndex + 1) % groups.length : 0;
    const nextGroup = groups[nextIndex];
    selectGroup(nextGroup.id, nextGroup.representative_photo_id);
  }

  function moveGroup(delta: -1 | 1) {
    const nextGroup = groupAfterMove(groups, activeGroup?.id ?? activeGroupId, delta);
    if (nextGroup) {
      selectGroup(nextGroup.id, nextGroup.representative_photo_id);
    }
  }

  function mark(status: Photo["user_status"]) {
    if (activePhoto) {
      const nextPhotoId = nextPhotoIdAfterMark(visiblePhotos, activePhoto.id);
      if (nextPhotoId) {
        setActivePhotoId(nextPhotoId);
      }
      updateMutation.mutate({ photo: activePhoto, patch: { user_status: status } });
    }
  }

  function batchMark(status: Photo["user_status"]) {
    if (visiblePhotoIds.length) {
      batchUpdateMutation.mutate({ photoIds: visiblePhotoIds, patch: { user_status: status } });
    }
  }

  function rate(star_rating: number) {
    if (activePhoto) {
      updateMutation.mutate({ photo: activePhoto, patch: { star_rating } });
    }
  }

  function focusFilterControls() {
    const activeFilterIndex = Math.max(FILTERS.indexOf(filter), 0);
    filterButtonRefs.current[activeFilterIndex]?.focus();
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      const command = reviewShortcutCommandForKey(event.key);
      if (!command) return;
      if (reviewShortcutNeedsPreventDefault(command)) {
        event.preventDefault();
      }

      if (command.type === "move_photo") move(command.delta);
      if (command.type === "move_group") moveGroup(command.delta);
      if (command.type === "mark") mark(command.status);
      if (command.type === "rate") rate(command.rating);
      if (command.type === "toggle_large_preview") toggleLargePreview();
      if (command.type === "toggle_zoom") toggleZoomPreview();
      if (command.type === "toggle_compare") toggleCompareMode();
      if (command.type === "cycle_group") cycleGroup();
      if (command.type === "focus_filters") focusFilterControls();
      if (command.type === "export") {
        router.push(`/projects/${projectId}/export`);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const preview = activePhoto ? assetUrl(projectId, activePhoto.preview_path) : null;
  const picks = photos.filter((photo) => photo.user_status === "Pick").length;
  const reviewed = photos.filter((photo) => photo.user_status !== "Unreviewed").length;
  const isLoading = project.isLoading || photosQuery.isLoading || groupsQuery.isLoading;
  const loadError = project.error ?? photosQuery.error ?? groupsQuery.error;
  const saveError = updateMutation.error ?? batchUpdateMutation.error;

  if (isLoading) {
    return (
      <section className="grid min-h-[calc(100vh-73px)] place-items-center px-5">
        <div className="inline-flex items-center gap-2 text-sm text-neutral-700">
          <Loader2 className="animate-spin text-leaf" size={18} />
          Loading culling workspace...
        </div>
      </section>
    );
  }

  if (loadError) {
    return (
      <section className="mx-auto grid max-w-3xl gap-4 px-5 py-10">
        <h1 className="text-2xl font-semibold">Culling Workspace</h1>
        <p className="text-sm text-coral">Could not load this project. Start the local API and try again.</p>
      </section>
    );
  }

  if (!photos.length) {
    return (
      <section className="mx-auto grid max-w-3xl gap-4 px-5 py-10">
        <div>
          <p className="text-sm text-neutral-600">{project.data?.name ?? "Project"}</p>
          <h1 className="mt-1 text-2xl font-semibold">No Photos Imported</h1>
        </div>
        <p className="text-sm text-neutral-700">
          Import JPEG, PNG, or WebP images before opening the culling workspace.
        </p>
        <Link
          className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-white"
          href={`/projects/${projectId}/import`}
        >
          <Upload size={18} />
          Import Images
        </Link>
      </section>
    );
  }

  if (!groups.length && (project.data?.processed_images ?? 0) === 0) {
    return (
      <section className="mx-auto grid max-w-3xl gap-4 px-5 py-10">
        <div>
          <p className="text-sm text-neutral-600">{project.data?.name ?? "Project"}</p>
          <h1 className="mt-1 text-2xl font-semibold">Processing Needed</h1>
        </div>
        <p className="text-sm text-neutral-700">Run grouping and ranking before reviewing recommendations.</p>
        <Link
          className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-white"
          href={`/projects/${projectId}/process`}
        >
          <Play size={18} />
          Process Project
        </Link>
      </section>
    );
  }

  return (
    <section className="grid min-h-[calc(100vh-73px)] grid-rows-[auto_1fr_auto]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-white px-5 py-3">
        <div>
          <h1 className="text-lg font-semibold">{project.data?.name ?? "Culling Workspace"}</h1>
          <p className="text-sm text-neutral-600">
            {reviewed}/{photos.length} reviewed · {picks} picks
            {activeGroupIndex >= 0 ? ` · Group ${activeGroupIndex + 1} of ${groups.length}` : ""}
          </p>
        </div>
        <Link
          className="focus-ring rounded bg-ink px-4 py-2 text-sm font-medium text-white"
          href={`/projects/${projectId}/export`}
        >
          Export
        </Link>
      </div>
      <div className="grid min-h-0 grid-cols-1 lg:grid-cols-[260px_1fr_320px]">
        <aside className="border-b border-line bg-white p-4 lg:border-b-0 lg:border-r">
          <h2 className="mb-3 text-sm font-semibold">Filters</h2>
          <div className="grid gap-1">
            {FILTERS.map((item, index) => (
              <button
                className={`focus-ring rounded px-3 py-2 text-left text-sm ${filter === item ? "bg-leaf text-white" : "hover:bg-mist"}`}
                key={item}
                onClick={() => setFilter(item)}
                ref={(node) => {
                  filterButtonRefs.current[index] = node;
                }}
              >
                {item}
              </button>
            ))}
          </div>
          <h2 className="mb-3 mt-6 text-sm font-semibold">Groups</h2>
          <div className="grid gap-2 text-sm text-neutral-700">
            {activeGroupId ? (
              <button
                className="focus-ring rounded border border-line bg-white px-3 py-2 text-left"
                onClick={() => selectGroup(null)}
              >
                Show filtered photos
              </button>
            ) : null}
            {groups.length > sidebarGroups.length ? (
              <span className="rounded border border-line px-3 py-2 text-xs text-neutral-600">
                {sidebarGroups.length} of {groups.length} groups
              </span>
            ) : null}
            {sidebarGroups.map((group) => {
              const summary = parseGroupScoreSummary(group.score_summary);
              const groupNumber = (groupIndexById.get(group.id) ?? 0) + 1;
              return (
                <button
                  className={`focus-ring rounded border px-3 py-2 text-left ${activeGroupId === group.id ? "border-leaf bg-mist" : "border-line bg-white"}`}
                  key={group.id}
                  onClick={() => selectGroup(group.id, group.representative_photo_id)}
                >
                  <span className="flex items-center justify-between gap-3">
                    <span>Group {groupNumber}</span>
                    <span>{group.photo_count}</span>
                  </span>
                  <span className="mt-1 block text-xs text-neutral-500">{groupConfidenceLabel(summary)}</span>
                </button>
              );
            })}
          </div>
        </aside>
        <div
          className={`grid min-h-[420px] place-items-center overflow-auto bg-neutral-900 p-4 ${
            largePreview ? "lg:col-span-2" : ""
          }`}
        >
          {compareMode && comparePhotos.length > 1 ? (
            <div className="grid w-full gap-3 md:grid-cols-2">
              {compareCandidates.length > comparePhotos.length ? (
                <span className="md:col-span-2 justify-self-start rounded bg-white/90 px-2 py-1 text-xs text-ink">
                  {comparePhotos.length} of {compareCandidates.length} compare candidates
                </span>
              ) : null}
              {comparePhotos.map((photo) => {
                const comparePreview = assetUrl(projectId, photo.preview_path);
                return (
                  <button
                    className={`focus-ring grid min-h-72 place-items-center overflow-hidden rounded border bg-neutral-950 p-2 ${
                      photo.id === activePhoto?.id ? "border-leaf" : "border-neutral-700"
                    }`}
                    key={photo.id}
                    onClick={() => setActivePhotoId(photo.id)}
                  >
                    {comparePreview ? (
                      <img
                        className="max-h-[56vh] max-w-full object-contain"
                        src={comparePreview}
                        alt={`Compare ${photo.filename}`}
                        loading="lazy"
                        decoding="async"
                      />
                    ) : (
                      <span className="text-sm text-white">No preview</span>
                    )}
                    <span className="mt-2 justify-self-start rounded bg-white/90 px-2 py-1 text-xs text-ink">
                      {photo.filename} · {photo.ai_recommendation}
                    </span>
                  </button>
                );
              })}
            </div>
          ) : preview ? (
            <img
              className={
                zoomPreview
                  ? "mx-auto max-w-none object-contain"
                  : "mx-auto max-h-[72vh] max-w-full object-contain"
              }
              src={preview}
              alt={activePhoto?.filename ?? "Preview"}
              decoding="async"
            />
          ) : (
            <div className="grid place-items-center gap-3 text-center text-white">
              <ImageOff size={38} />
              <p>
                {activeGroupId ? "No photos in this group match the current filter." : "No photos match this filter."}
              </p>
            </div>
          )}
        </div>
        {!largePreview ? (
          <aside className="border-t border-line bg-white p-4 lg:border-l lg:border-t-0">
            {activePhoto ? (
              <div className="grid gap-5">
                <div>
                  <h2 className="font-semibold">{activePhoto.filename}</h2>
                  <p className="text-sm text-neutral-600">
                    {activePhoto.width} x {activePhoto.height}
                  </p>
                </div>
                {metadataRows.length ? (
                  <div className="rounded border border-line p-3 text-sm">
                    <p className="font-semibold">Metadata</p>
                    <div className="mt-2 grid gap-1 text-neutral-700">
                      {metadataRows.map(([label, value]) => (
                        <p className="flex justify-between gap-3" key={label}>
                          <span className="text-neutral-500">{label}</span>
                          <span className="text-right">{value}</span>
                        </p>
                      ))}
                    </div>
                  </div>
                ) : null}
                {activeGroup ? (
                  <div className="rounded border border-line bg-mist p-3 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold">{groupConfidenceLabel(activeGroupSummary)}</p>
                      <p className="text-neutral-600">{activeGroup.photo_count} photos</p>
                    </div>
                    {activeGroupSummary ? (
                      <>
                        <p className="mt-2 text-neutral-700">{activeGroupSummary.explanation}</p>
                        <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-neutral-700">
                          <span>Best {activeGroupSummary.best_score.toFixed(2)}</span>
                          <span>Gap {activeGroupSummary.score_gap.toFixed(2)}</span>
                          <span>Pick {activeGroupSummary.recommendation_counts.Pick ?? 0}</span>
                          <span>Reject {activeGroupSummary.recommendation_counts.Reject ?? 0}</span>
                        </div>
                      </>
                    ) : null}
                  </div>
                ) : null}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {[
                    ["Sharpness", activePhoto.sharpness_score],
                    ["Exposure", activePhoto.exposure_score],
                    ["Contrast", activePhoto.contrast_score],
                    ["Blur risk", activePhoto.blur_score],
                    ["Face sharpness", activePhoto.face_sharpness_score],
                    ["Eye open", activePhoto.eye_open_confidence ?? 0],
                    ["Face quality", activePhoto.face_quality_score],
                    ["Aesthetic", activePhoto.aesthetic_score],
                    ["Overall", activePhoto.overall_score],
                  ].map(([label, value]) => (
                    <div className="rounded border border-line p-3" key={label}>
                      <p className="text-neutral-600">{label}</p>
                      <p className="mt-1 font-semibold">{Number(value).toFixed(2)}</p>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-neutral-600">
                  {activePhoto.face_presence
                    ? "Experimental face signals detected for this frame."
                    : "No experimental face signals detected."}
                </p>
                <p className="rounded border border-line bg-mist p-3 text-sm">
                  {activePhoto.recommendation_explanation}
                </p>
                <div className="rounded border border-line p-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold">Batch visible</p>
                    <p className="text-xs text-neutral-600">{visiblePhotos.length} photos</p>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <button
                      className="focus-ring rounded bg-leaf px-2 py-2 text-xs font-medium text-white disabled:opacity-50"
                      disabled={!visiblePhotos.length || batchUpdateMutation.isPending}
                      onClick={() => batchMark("Pick")}
                      aria-label="Set visible photos to selected"
                    >
                      Pick
                    </button>
                    <button
                      className="focus-ring rounded bg-gold px-2 py-2 text-xs font-medium text-white disabled:opacity-50"
                      disabled={!visiblePhotos.length || batchUpdateMutation.isPending}
                      onClick={() => batchMark("Maybe")}
                      aria-label="Set visible photos to tentative"
                    >
                      Maybe
                    </button>
                    <button
                      className="focus-ring rounded bg-coral px-2 py-2 text-xs font-medium text-white disabled:opacity-50"
                      disabled={!visiblePhotos.length || batchUpdateMutation.isPending}
                      onClick={() => batchMark("Reject")}
                      aria-label="Set visible photos to rejected"
                    >
                      Reject
                    </button>
                    <button
                      className="focus-ring rounded border border-line px-2 py-2 text-xs font-medium disabled:opacity-50"
                      disabled={!visiblePhotos.length || batchUpdateMutation.isPending}
                      onClick={() => batchMark("Unreviewed")}
                      aria-label="Set visible photos to unreviewed"
                    >
                      Unreviewed
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    className="focus-ring rounded bg-leaf px-3 py-2 text-sm font-medium text-white"
                    onClick={() => mark("Pick")}
                  >
                    Pick
                  </button>
                  <button
                    className="focus-ring rounded bg-gold px-3 py-2 text-sm font-medium text-white"
                    onClick={() => mark("Maybe")}
                  >
                    Maybe
                  </button>
                  <button
                    className="focus-ring rounded bg-coral px-3 py-2 text-sm font-medium text-white"
                    onClick={() => mark("Reject")}
                  >
                    Reject
                  </button>
                  <button
                    className="focus-ring rounded border border-line px-3 py-2 text-sm font-medium"
                    onClick={() => mark("Unreviewed")}
                  >
                    Unreviewed
                  </button>
                </div>
                {saveError ? <p className="text-sm text-coral">{saveError.message}</p> : null}
                <div className="flex gap-1">
                  <button
                    className="focus-ring rounded p-2 text-neutral-600"
                    onClick={() => rate(0)}
                    aria-label="Clear rating"
                  >
                    <StarOff size={20} />
                  </button>
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      className="focus-ring rounded p-2 text-gold"
                      key={rating}
                      onClick={() => rate(rating)}
                      aria-label={`${rating} stars`}
                    >
                      <Star fill={activePhoto.star_rating >= rating ? "currentColor" : "none"} size={20} />
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </aside>
        ) : null}
      </div>
      <div className="flex min-h-28 items-center gap-3 overflow-x-auto border-t border-line bg-white px-4 py-3">
        <button
          className="focus-ring grid h-10 w-10 shrink-0 place-items-center rounded border border-line"
          onClick={() => move(-1)}
          aria-label="Previous photo"
        >
          <ArrowLeft size={18} />
        </button>
        {visiblePhotos.length > filmstripPhotos.length ? (
          <span className="shrink-0 rounded border border-line px-3 py-2 text-xs text-neutral-600">
            {filmstripPhotos.length} of {visiblePhotos.length}
          </span>
        ) : null}
        {filmstripPhotos.map((photo) => {
          const thumbnail = assetUrl(projectId, photo.thumbnail_path);
          return (
            <button
              className={`focus-ring relative h-20 w-28 shrink-0 overflow-hidden rounded border ${photo.id === activePhoto?.id ? "border-leaf" : "border-line"}`}
              key={photo.id}
              onClick={() => setActivePhotoId(photo.id)}
            >
              {thumbnail ? (
                <img
                  className="h-full w-full object-cover"
                  src={thumbnail}
                  alt={photo.filename}
                  loading="lazy"
                  decoding="async"
                />
              ) : (
                <span className="grid h-full place-items-center text-xs">No preview</span>
              )}
              <span className="absolute bottom-1 left-1 rounded bg-white/90 px-1 text-xs">{photo.user_status}</span>
              {photo.ai_recommendation === "Pick" ? (
                <Check className="absolute right-1 top-1 rounded bg-leaf text-white" size={16} />
              ) : null}
            </button>
          );
        })}
        <button
          className="focus-ring grid h-10 w-10 shrink-0 place-items-center rounded border border-line"
          onClick={() => move(1)}
          aria-label="Next photo"
        >
          <ArrowRight size={18} />
        </button>
        <button
          className="focus-ring grid h-10 w-10 shrink-0 place-items-center rounded border border-line"
          onClick={toggleLargePreview}
          aria-label="Toggle large preview"
          aria-pressed={largePreview}
        >
          {largePreview ? <X size={18} /> : <Eye size={18} />}
        </button>
        <button
          className={`focus-ring grid h-10 w-10 shrink-0 place-items-center rounded border ${
            compareMode ? "border-leaf bg-mist text-leaf" : "border-line"
          }`}
          onClick={toggleCompareMode}
          aria-label="Toggle compare"
          aria-pressed={compareMode}
        >
          <Columns2 size={18} />
        </button>
        <button
          className={`focus-ring grid h-10 w-10 shrink-0 place-items-center rounded border ${
            zoomPreview ? "border-leaf bg-mist text-leaf" : "border-line"
          }`}
          onClick={toggleZoomPreview}
          aria-label="Toggle zoom"
          aria-pressed={zoomPreview}
        >
          {zoomPreview ? <ZoomOut size={18} /> : <ZoomIn size={18} />}
        </button>
      </div>
    </section>
  );
}
