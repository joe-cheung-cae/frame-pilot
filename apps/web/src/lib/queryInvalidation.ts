type QueryInvalidator = {
  invalidateQueries: (filters: { queryKey: readonly unknown[] }) => Promise<unknown>;
};

export function projectWorkflowQueryKeys(projectId: string): readonly unknown[][] {
  return [
    ["project", projectId],
    ["projects"],
    ["photos", projectId],
    ["groups", projectId],
    ["photo-status-counts", projectId],
    ["jobs", projectId],
    ["job", projectId],
  ];
}

export async function invalidateProjectWorkflowQueries(queryClient: QueryInvalidator, projectId: string) {
  await Promise.all(
    projectWorkflowQueryKeys(projectId).map((queryKey) => queryClient.invalidateQueries({ queryKey })),
  );
}

export async function invalidateProjectExportQueries(queryClient: QueryInvalidator, projectId: string) {
  await queryClient.invalidateQueries({ queryKey: ["exports", projectId] });
}
