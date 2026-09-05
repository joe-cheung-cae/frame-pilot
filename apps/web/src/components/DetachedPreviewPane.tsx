"use client";

/* eslint-disable @next/next/no-img-element */

import { useEffect, useState } from "react";
import { ImageOff } from "lucide-react";
import { assetUrl } from "@/lib/api";
import {
  emitReviewCommand,
  emitReviewSyncRequest,
  subscribeReviewSync,
  type ReviewSyncPayload,
} from "@/lib/detachedPreview";
import { reviewShortcutCommandFromEvent, reviewShortcutNeedsPreventDefault } from "@/lib/reviewShortcuts";

export function DetachedPreviewPane() {
  const [sync, setSync] = useState<ReviewSyncPayload | null>(null);

  useEffect(() => {
    let cancelled = false;
    let unlisten = () => {};
    void subscribeReviewSync((payload) => setSync(payload)).then((fn) => {
      if (cancelled) {
        fn();
        return;
      }
      unlisten = fn;
    });
    void emitReviewSyncRequest();
    return () => {
      cancelled = true;
      unlisten();
    };
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const command = reviewShortcutCommandFromEvent(event);
      if (!command) {
        return;
      }
      if (reviewShortcutNeedsPreventDefault(command)) {
        event.preventDefault();
      }
      void emitReviewCommand(command);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  if (!sync?.activePhotoId) {
    return (
      <section
        className="grid h-full min-h-0 place-items-center bg-neutral-900 p-6 text-white"
        aria-label="Detached preview"
      >
        <p className="text-sm text-white/75">No photo selected</p>
      </section>
    );
  }

  const preview = assetUrl(sync.projectId, sync.previewPath);
  const zoom = sync.previewZoom > 0 ? sync.previewZoom : 1;
  const compare = sync.compareMode && sync.compare.length > 1;

  return (
    <section
      className="grid h-full min-h-0 grid-rows-[1fr_auto] bg-neutral-900 text-white"
      aria-label="Detached preview"
    >
      <div className="grid min-h-0 place-items-center overflow-auto p-4">
        {compare ? (
          <div className="grid h-full w-full min-w-0 gap-3 md:grid-cols-2">
            {sync.compare.map((item) => {
              const src = assetUrl(sync.projectId, item.previewPath);
              return (
                <div
                  className={`grid min-h-72 min-w-0 place-items-center overflow-auto rounded border bg-neutral-950 p-2 ${
                    item.photoId === sync.activePhotoId ? "border-leaf" : "border-neutral-700"
                  }`}
                  key={item.photoId}
                >
                  {src ? (
                    <img className="block h-full w-full object-contain" src={src} alt={item.filename} />
                  ) : (
                    <ImageOff size={38} />
                  )}
                  <span className="mt-2 justify-self-start rounded bg-surface/90 px-2 py-1 text-xs text-ink">
                    {item.filename}
                  </span>
                </div>
              );
            })}
          </div>
        ) : preview ? (
          <div className={`h-full w-full min-w-0 ${zoom <= 1 ? "grid place-items-center" : ""}`}>
            <div
              className={`grid place-items-center ${zoom <= 1 ? "" : "origin-top-left"}`}
              style={{ height: `${zoom * 100}%`, minHeight: 0, minWidth: 0, width: `${zoom * 100}%` }}
            >
              <img
                className="block h-full w-full object-contain"
                src={preview}
                alt={sync.filename ?? "Preview"}
              />
            </div>
          </div>
        ) : (
          <div className="grid place-items-center gap-3 text-center">
            <ImageOff size={38} />
            <p>Preview unavailable</p>
          </div>
        )}
      </div>
      <p className="truncate border-t border-neutral-800 px-4 py-2 text-sm text-white/80">
        {sync.filename ?? ""} · {Math.round(zoom * 100)}%
      </p>
    </section>
  );
}
