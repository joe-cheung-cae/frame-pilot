import test from "node:test";
import assert from "node:assert/strict";

import { invalidateProjectWorkflowQueries, projectWorkflowQueryKeys } from "./queryInvalidation.ts";

test("lists project workflow queries invalidated after imports", () => {
  assert.deepEqual(projectWorkflowQueryKeys("project-1"), [
    ["project", "project-1"],
    ["projects"],
    ["photos", "project-1"],
    ["groups", "project-1"],
    ["photo-status-counts", "project-1"],
    ["jobs", "project-1"],
    ["job", "project-1"],
  ]);
});

test("invalidates every project workflow query", async () => {
  const invalidated: (readonly unknown[])[] = [];
  await invalidateProjectWorkflowQueries(
    {
      invalidateQueries: async ({ queryKey }) => {
        invalidated.push(queryKey);
      },
    },
    "project-2",
  );

  assert.deepEqual(invalidated, projectWorkflowQueryKeys("project-2"));
});
