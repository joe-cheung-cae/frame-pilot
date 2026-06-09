export type GroupScoreSummary = {
  best_score: number;
  confidence: "low" | "medium" | "high";
  explanation: string;
  recommendation_counts: Partial<Record<"Pick" | "Maybe" | "Reject" | "Unreviewed", number>>;
  score_gap: number;
  top_photo_id: string | null;
};

export type GroupScoreSummaryRow = [label: string, value: string];

const CONFIDENCE_LABELS = {
  high: "High confidence",
  medium: "Medium confidence",
  low: "Low confidence",
} as const;

export function parseGroupScoreSummary(raw: string | null | undefined): GroupScoreSummary | null {
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as Partial<GroupScoreSummary>;
    if (
      parsed.confidence !== "high" &&
      parsed.confidence !== "medium" &&
      parsed.confidence !== "low"
    ) {
      return null;
    }
    return {
      best_score: Number(parsed.best_score ?? 0),
      confidence: parsed.confidence,
      explanation: typeof parsed.explanation === "string" ? parsed.explanation : "",
      recommendation_counts:
        parsed.recommendation_counts && typeof parsed.recommendation_counts === "object"
          ? parsed.recommendation_counts
          : {},
      score_gap: Number(parsed.score_gap ?? 0),
      top_photo_id: typeof parsed.top_photo_id === "string" ? parsed.top_photo_id : null,
    };
  } catch {
    return null;
  }
}

export function groupConfidenceLabel(summary: GroupScoreSummary | null): string {
  return summary ? CONFIDENCE_LABELS[summary.confidence] : "Confidence pending";
}

export function groupPhotoCountLabel(count: number): string {
  return `${count} ${count === 1 ? "photo" : "photos"}`;
}

export function groupScoreSummaryRows(summary: GroupScoreSummary): GroupScoreSummaryRow[] {
  return [
    ["Best", summary.best_score.toFixed(2)],
    ["Gap", summary.score_gap.toFixed(2)],
    ["Pick", String(summary.recommendation_counts.Pick ?? 0)],
    ["Reject", String(summary.recommendation_counts.Reject ?? 0)],
  ];
}
