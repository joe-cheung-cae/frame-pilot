"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

export function ProjectCreator() {
  const [name, setName] = useState("");
  const [rootPath, setRootPath] = useState("");
  const router = useRouter();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ projectName, projectRootPath }: { projectName: string; projectRootPath?: string }) =>
      api.createProject(projectName, projectRootPath),
    onSuccess: async (project) => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      router.push(`/projects/${project.id}/import`);
    },
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (name.trim()) {
      mutation.mutate({ projectName: name.trim(), projectRootPath: rootPath.trim() || undefined });
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-4">
      <label className="grid gap-2 text-sm font-medium text-ink">
        Project name
        <input
          className="focus-ring rounded border border-line bg-white px-3 py-3 text-base"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Saturday portrait session"
        />
      </label>
      <label className="grid gap-2 text-sm font-medium text-ink">
        Project data folder
        <input
          className="focus-ring rounded border border-line bg-white px-3 py-3 text-base"
          value={rootPath}
          onChange={(event) => setRootPath(event.target.value)}
          placeholder="/Users/name/Pictures/FramePilot project"
        />
      </label>
      <p className="-mt-2 text-sm text-muted">Leave blank to use the FramePilot managed local data folder.</p>
      <button
        className="focus-ring inline-flex min-h-11 items-center justify-center gap-2 rounded bg-leaf px-4 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!name.trim() || mutation.isPending}
      >
        {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <ArrowRight size={18} />}
        Create and Import
      </button>
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
    </form>
  );
}
