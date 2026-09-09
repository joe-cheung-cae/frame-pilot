"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, Suspense, useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { MENU_WORKFLOW_QUERY, menuWorkflowPrompt } from "@/lib/menuRoutes";
import { getNativeFs } from "@/lib/nativeFs";
import { useNavigator, useQueryParams } from "@/lib/navigation";
import {
  createProjectWithNonemptyConfirm,
  normalizeProjectCreateDraft,
  type NormalizedProjectCreateDraft,
  projectCreateActionBlockMessage,
  projectCreationRecoveryHint,
  projectDataFolderHint,
  registerPickedProjectRoot,
} from "@/lib/projectCreation";
import { saveLastOpenedProjectId } from "@/lib/recentProjects";

function CreateProjectWorkflowPrompt() {
  const queryParams = useQueryParams();
  const workflowPrompt = menuWorkflowPrompt(queryParams.get(MENU_WORKFLOW_QUERY));
  if (!workflowPrompt) {
    return null;
  }
  return <p className="text-sm text-coral">{workflowPrompt}</p>;
}

export function ProjectCreator() {
  const nativeFs = getNativeFs();
  const [name, setName] = useState("");
  const [rootPath, setRootPath] = useState("");
  const [browseError, setBrowseError] = useState("");
  const navigator = useNavigator();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (draft: NormalizedProjectCreateDraft) =>
      createProjectWithNonemptyConfirm(draft, {
        createProject: api.createProject,
        confirmNonempty: (message) => window.confirm(message),
      }),
    onSuccess: async (project) => {
      saveLastOpenedProjectId(project.id);
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigator.push(`/projects/${project.id}/import`);
    },
  });
  const createBlockMessage = projectCreateActionBlockMessage({ isCreating: mutation.isPending, name });
  const errorMessage = browseError || (mutation.isError ? mutation.error.message : "");

  async function onBrowse() {
    if (!nativeFs) {
      return;
    }
    setBrowseError("");
    try {
      const registeredPath = await registerPickedProjectRoot({
        pickDirectory: () => nativeFs.pickDirectory(),
        registerRoot: (path) => api.registerDesktopProjectRoot(path),
      });
      if (registeredPath) {
        setRootPath(registeredPath);
      }
    } catch (error) {
      setBrowseError(error instanceof Error ? error.message : String(error));
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!createBlockMessage) {
      setBrowseError("");
      mutation.mutate(normalizeProjectCreateDraft({ name, rootPath }));
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-4">
      <label className="grid gap-2 text-sm font-medium text-ink">
        Project name
        <input
          className="focus-ring rounded border border-line bg-surface px-3 py-3 text-base"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Saturday portrait session"
        />
      </label>
      <label className="grid gap-2 text-sm font-medium text-ink">
        Project data folder
        {nativeFs ? (
          <div className="flex gap-2">
            <input
              className="focus-ring min-w-0 flex-1 rounded border border-line bg-surface px-3 py-3 text-base"
              value={rootPath}
              onChange={(event) => setRootPath(event.target.value)}
              placeholder="/Users/name/Pictures/FramePilot project"
            />
            <button
              type="button"
              className="focus-ring inline-flex min-h-11 shrink-0 items-center justify-center rounded border border-line bg-surface px-4 font-medium text-ink"
              onClick={() => {
                void onBrowse();
              }}
            >
              Browse
            </button>
          </div>
        ) : (
          <input
            className="focus-ring rounded border border-line bg-surface px-3 py-3 text-base"
            value={rootPath}
            onChange={(event) => setRootPath(event.target.value)}
            placeholder="/Users/name/Pictures/FramePilot project"
          />
        )}
      </label>
      <p className="-mt-2 text-sm text-muted">{projectDataFolderHint(rootPath)}</p>
      <button
        className="focus-ring inline-flex min-h-11 items-center justify-center gap-2 rounded bg-leaf px-4 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
        disabled={Boolean(createBlockMessage)}
      >
        {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <ArrowRight size={18} />}
        Create and Import
      </button>
      {createBlockMessage ? <p className="text-sm text-muted">{createBlockMessage}</p> : null}
      <Suspense fallback={null}>
        <CreateProjectWorkflowPrompt />
      </Suspense>
      {errorMessage ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{errorMessage}</p>
          <p className="text-muted">{projectCreationRecoveryHint(rootPath)}</p>
        </div>
      ) : null}
    </form>
  );
}
