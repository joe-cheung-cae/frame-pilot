import test from "node:test";
import assert from "node:assert/strict";

import { projectExportRoot, revealFolder } from "./revealFolder.ts";

test("reveal callback is invoked with output_path", async () => {
  const revealed: string[] = [];
  const opened = await revealFolder(
    "export",
    {
      rootPath: "/projects/shoot",
      outputPath: "/projects/shoot/exports/folders/selection-1",
    },
    async (targetPath) => {
      revealed.push(targetPath);
    },
  );

  assert.equal(opened, true);
  assert.deepEqual(revealed, ["/projects/shoot/exports/folders/selection-1"]);
});

test("reveal callback is invoked with root_path for the project folder", async () => {
  const revealed: string[] = [];
  const opened = await revealFolder(
    "project",
    { rootPath: "/projects/shoot" },
    async (targetPath) => {
      revealed.push(targetPath);
    },
  );

  assert.equal(opened, true);
  assert.deepEqual(revealed, ["/projects/shoot"]);
});

test("open export folder falls back to the project exports directory", async () => {
  const revealed: string[] = [];
  const opened = await revealFolder(
    "export",
    { rootPath: "/projects/shoot/" },
    async (targetPath) => {
      revealed.push(targetPath);
    },
  );

  assert.equal(opened, true);
  assert.equal(projectExportRoot("/projects/shoot/"), "/projects/shoot/exports");
  assert.deepEqual(revealed, ["/projects/shoot/exports"]);
});

test("does not invoke the reveal callback without a path or native adapter", async () => {
  const revealed: string[] = [];
  assert.equal(await revealFolder("project", { rootPath: "   " }, async (targetPath) => {
    revealed.push(targetPath);
  }), false);
  assert.equal(await revealFolder("export", { outputPath: "/exports/out" }, null), false);
  assert.deepEqual(revealed, []);
});
