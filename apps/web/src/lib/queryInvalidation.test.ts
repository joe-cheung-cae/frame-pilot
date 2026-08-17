import test from "node:test";
import assert from "node:assert/strict";

import {
  invalidateProjectExportQueries,
  invalidateProjectWorkflowQueries,
  projectWorkflowQueryKeys,
} from "./queryInvalidation.ts";

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

test("invalidates export history for a project", async () => {
  const invalidated: (readonly unknown[])[] = [];
  await invalidateProjectExportQueries(
    {
      invalidateQueries: async ({ queryKey }) => {
        invalidated.push(queryKey);
      },
    },
    "project-3",
  );

  assert.deepEqual(invalidated, [["exports", "project-3"]]);
});
