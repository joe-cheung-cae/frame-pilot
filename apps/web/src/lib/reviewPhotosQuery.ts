/** React Query key for culling photos. Mode must match queryFn so refetches never
 *  truncate a full load that was written via setQueryData. */
export function photosQueryKey(projectId: string, allLoaded: boolean) {
  return ["photos", projectId, allLoaded ? "all" : "page"] as const;
}
