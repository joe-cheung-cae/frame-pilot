/** Upper bound on how many virtual rows/columns a windowed list should mount. */
export function maxRenderedVirtualItems({
  estimateSize,
  itemCount,
  overscan,
  viewportSize,
}: {
  estimateSize: number;
  itemCount: number;
  overscan: number;
  viewportSize: number;
}): number {
  if (itemCount <= 0 || viewportSize <= 0 || estimateSize <= 0) {
    return 0;
  }

  return Math.min(itemCount, Math.ceil(viewportSize / estimateSize) + overscan * 2);
}
