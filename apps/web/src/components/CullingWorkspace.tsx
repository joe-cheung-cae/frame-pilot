"use client";

/* eslint-disable @next/next/no-img-element */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useMemo } from "react";
import { ArrowLeft, ArrowRight, Check, Eye, ImageOff, Loader2, Play, Star, Upload, X, ZoomIn, ZoomOut } from "lucide-react";
import { api, assetUrl, Photo } from "@/lib/api";
import { groupConfidenceLabel, parseGroupScoreSummary } from "@/lib/groupScoreSummary";
import { groupAfterMove, nextPhotoIdAfterMark } from "@/lib/reviewNavigation";
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

type PhotoPatch = Partial<Pick<Photo, "user_status" | "star_rating">>;

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

export function CullingWorkspace({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const project = useQuery({ queryKey: ["project", projectId], queryFn: () => api.getProject(projectId) });
  const photosQuery = useQuery({ queryKey: ["photos", projectId], queryFn: () => api.listPhotos(projectId) });
  const groupsQuery = useQuery({ queryKey: ["groups", projectId], queryFn: () => api.listGroups(projectId) });
  const {
    activeGroupId,
    activePhotoId,
    filter,
    largePreview,
    zoomPreview,
    setActiveGroupId,
    setActivePhotoId,
    setFilter,
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
  const activeGroupIndex = activeGroup ? groups.findIndex((group) => group.id === activeGroup.id) : -1;
  const activeGroupSummary = useMemo(
    () => parseGroupScoreSummary(activeGroup?.score_summary),
    [activeGroup?.score_summary],
  );

  const updateMutation = useMutation({
    mutationFn: ({ photo, patch }: { photo: Photo; patch: PhotoPatch }) => api.updatePhoto(projectId, photo.id, patch),
    onMutate: async ({ photo, patch }) => {
      const queryKey = ["photos", projectId];
      await queryClient.cancelQueries({ queryKey });
      const previousPhotos = queryClient.getQueryData<Photo[]>(queryKey);
      queryClient.setQueryData<Photo[]>(queryKey, (currentPhotos) =>
        currentPhotos?.map((item) => (item.id === photo.id ? { ...item, ...patch } : item)),
      );
      return { previousPhotos };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousPhotos) {
        queryClient.setQueryData(["photos", projectId], context.previousPhotos);
      }
    },
    onSuccess: (updatedPhoto) => {
      queryClient.setQueryData<Photo[]>(["photos", projectId], (currentPhotos) =>
        currentPhotos?.map((item) => (item.id === updatedPhoto.id ? updatedPhoto : item)),
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

  function rate(star_rating: number) {
    if (activePhoto) {
      updateMutation.mutate({ photo: activePhoto, patch: { star_rating } });
    }
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      if (event.key === "ArrowLeft") move(-1);
      if (event.key === "ArrowRight") move(1);
      if (event.key === "ArrowUp") {
        event.preventDefault();
        moveGroup(-1);
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        moveGroup(1);
      }
      if (event.key.toLowerCase() === "p") mark("Pick");
      if (event.key.toLowerCase() === "m") mark("Maybe");
      if (event.key.toLowerCase() === "x") mark("Reject");
      if (event.key.toLowerCase() === "u") mark("Unreviewed");
      if (event.key === " ") {
        event.preventDefault();
        toggleLargePreview();
      }
      if (event.key.toLowerCase() === "z") toggleZoomPreview();
      if (event.key.toLowerCase() === "g") cycleGroup();
      const numeric = Number(event.key);
      if (numeric === 0) rate(0);
      if (numeric >= 1 && numeric <= 5) rate(numeric);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const preview = activePhoto ? assetUrl(projectId, activePhoto.preview_path) : null;
  const picks = photos.filter((photo) => photo.user_status === "Pick").length;
  const reviewed = photos.filter((photo) => photo.user_status !== "Unreviewed").length;
  const isLoading = project.isLoading || photosQuery.isLoading || groupsQuery.isLoading;
  const loadError = project.error ?? photosQuery.error ?? groupsQuery.error;

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
            {FILTERS.map((item) => (
              <button
                className={`focus-ring rounded px-3 py-2 text-left text-sm ${filter === item ? "bg-leaf text-white" : "hover:bg-mist"}`}
                key={item}
                onClick={() => setFilter(item)}
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
            {groups.map((group, index) => {
              const summary = parseGroupScoreSummary(group.score_summary);
              return (
                <button
                  className={`focus-ring rounded border px-3 py-2 text-left ${activeGroupId === group.id ? "border-leaf bg-mist" : "border-line bg-white"}`}
                  key={group.id}
                  onClick={() => selectGroup(group.id, group.representative_photo_id)}
                >
                  <span className="flex items-center justify-between gap-3">
                    <span>Group {index + 1}</span>
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
          {preview ? (
            <img
              className={
                zoomPreview
                  ? "mx-auto max-w-none object-contain"
                  : "mx-auto max-h-[72vh] max-w-full object-contain"
              }
              src={preview}
              alt={activePhoto?.filename ?? "Preview"}
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
                <div className="flex gap-1">
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
        {visiblePhotos.map((photo) => {
          const thumbnail = assetUrl(projectId, photo.thumbnail_path);
          return (
            <button
              className={`focus-ring relative h-20 w-28 shrink-0 overflow-hidden rounded border ${photo.id === activePhoto?.id ? "border-leaf" : "border-line"}`}
              key={photo.id}
              onClick={() => setActivePhotoId(photo.id)}
            >
              {thumbnail ? (
                <img className="h-full w-full object-cover" src={thumbnail} alt={photo.filename} />
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
          aria-label="Toggle preview"
        >
          {largePreview ? <X size={18} /> : <Eye size={18} />}
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
