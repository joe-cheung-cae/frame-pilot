import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";

import {
  LAST_OPENED_PROJECT_KEY,
  loadLastOpenedProjectId,
  orderProjectsByLastOpened,
  saveLastOpenedProjectId,
} from "./recentProjects.ts";

function memoryStorage(initial: Record<string, string> = {}) {
  const values = { ...initial };
  return {
    getItem: (key: string) => values[key] ?? null,
    setItem: (key: string, value: string) => {
      values[key] = value;
    },
    values,
  };
}

function throwingStorage() {
  return {
    getItem: () => {
      throw new Error("Storage unavailable");
    },
    setItem: () => {
      throw new Error("Storage unavailable");
    },
  };
}

const here = path.dirname(fileURLToPath(import.meta.url));
const projectListSource = fs.readFileSync(path.resolve(here, "../components/ProjectList.tsx"), "utf8");
const projectDashboardSource = fs.readFileSync(path.resolve(here, "../components/ProjectDashboard.tsx"), "utf8");
const apiSource = fs.readFileSync(path.resolve(here, "api.ts"), "utf8");

test("saves last-opened project id in localStorage", () => {
  const storage = memoryStorage();

  assert.equal(saveLastOpenedProjectId("project-42", storage), "project-42");
  assert.equal(storage.values[LAST_OPENED_PROJECT_KEY], "project-42");
});

test("loads last-opened project id from localStorage", () => {
  const storage = memoryStorage({ [LAST_OPENED_PROJECT_KEY]: "project-7" });

  assert.equal(loadLastOpenedProjectId(storage), "project-7");
});

test("returns null when last-opened storage is missing or blank", () => {
  assert.equal(loadLastOpenedProjectId(undefined), null);
  assert.equal(loadLastOpenedProjectId(memoryStorage()), null);
  assert.equal(loadLastOpenedProjectId(memoryStorage({ [LAST_OPENED_PROJECT_KEY]: "   " })), null);
});

test("does not persist a blank last-opened project id", () => {
  const storage = memoryStorage({ [LAST_OPENED_PROJECT_KEY]: "project-keep" });

  assert.equal(saveLastOpenedProjectId("  ", storage), null);
  assert.equal(storage.values[LAST_OPENED_PROJECT_KEY], "project-keep");
});

test("keeps last-opened id usable when browser storage throws", () => {
  assert.equal(loadLastOpenedProjectId(throwingStorage()), null);
  assert.equal(saveLastOpenedProjectId("project-9", throwingStorage()), "project-9");
});

test("orders last-opened project first without changing the remaining GET /api/projects order", () => {
  const projects = [
    { id: "newest" },
    { id: "middle" },
    { id: "oldest" },
  ];

  assert.deepEqual(orderProjectsByLastOpened(projects, "oldest"), [
    { id: "oldest" },
    { id: "newest" },
    { id: "middle" },
  ]);
  assert.deepEqual(projects, [{ id: "newest" }, { id: "middle" }, { id: "oldest" }]);
});

test("keeps the GET /api/projects list unchanged when last-opened is missing or unknown", () => {
  const projects = [{ id: "a" }, { id: "b" }];

  assert.deepEqual(orderProjectsByLastOpened(projects, null), [{ id: "a" }, { id: "b" }]);
  assert.deepEqual(orderProjectsByLastOpened(projects, "missing"), [{ id: "a" }, { id: "b" }]);
});

test("GET /api/projects remains the project list with no second database", () => {
  assert.match(apiSource, /listProjects:\s*\(\)\s*=>\s*request<Project\[]>\("\/api\/projects"\)/);
  assert.match(projectListSource, /queryFn:\s*api\.listProjects/);
  assert.doesNotMatch(projectListSource, /indexedDB|sqlite|openDatabase/i);
  assert.match(projectListSource, /orderProjectsByLastOpened/);
  assert.match(projectListSource, /saveLastOpenedProjectId/);
  assert.match(projectDashboardSource, /saveLastOpenedProjectId\(projectId\)/);
});
