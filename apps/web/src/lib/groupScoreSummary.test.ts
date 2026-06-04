import test from "node:test";
import assert from "node:assert/strict";

import { groupConfidenceLabel, groupScoreSummaryRows, parseGroupScoreSummary } from "./groupScoreSummary.ts";

test("parses persisted group score summaries", () => {
  const summary = parseGroupScoreSummary(
    JSON.stringify({
      best_score: 0.82,
      confidence: "medium",
      explanation: "Medium confidence because the top photo leads the next candidate by 0.07.",
      recommendation_counts: { Maybe: 1, Pick: 1, Reject: 0, Unreviewed: 0 },
      score_gap: 0.07,
      top_photo_id: "photo-1",
    }),
  );

  assert.deepEqual(summary, {
    best_score: 0.82,
    confidence: "medium",
    explanation: "Medium confidence because the top photo leads the next candidate by 0.07.",
    recommendation_counts: { Maybe: 1, Pick: 1, Reject: 0, Unreviewed: 0 },
    score_gap: 0.07,
    top_photo_id: "photo-1",
  });
  assert.equal(groupConfidenceLabel(summary), "Medium confidence");
});

test("ignores missing or malformed group score summaries", () => {
  assert.equal(parseGroupScoreSummary("{}"), null);
  assert.equal(parseGroupScoreSummary("not json"), null);
  assert.equal(groupConfidenceLabel(null), "Confidence pending");
});

test("formats group score summary rows", () => {
  assert.deepEqual(
    groupScoreSummaryRows({
      best_score: 0.823,
      confidence: "medium",
      explanation: "Medium confidence.",
      recommendation_counts: { Pick: 1 },
      score_gap: 0.074,
      top_photo_id: "photo-1",
    }),
    [
      ["Best", "0.82"],
      ["Gap", "0.07"],
      ["Pick", "1"],
      ["Reject", "0"],
    ],
  );
});
