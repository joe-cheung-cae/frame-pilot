import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_EXPORT_STATUS_PREFERENCE,
  EXPORT_STATUS_PREFERENCE_KEY,
  loadExportStatusPreference,
  normalizeExportStatusPreference,
  saveExportStatusPreference,
  isOnlySelectedExportStatus,
  toggleSavedExportStatusPreference,
  toggleExportStatusPreference,
} from "./settings.ts";

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

test("normalizes export status preferences to supported order", () => {
  assert.deepEqual(normalizeExportStatusPreference(["Reject", "Pick", "Missing"]), ["Pick", "Reject"]);
});

test("falls back to default export statuses for empty or invalid preferences", () => {
  assert.deepEqual(normalizeExportStatusPreference([]), DEFAULT_EXPORT_STATUS_PREFERENCE);
  assert.deepEqual(normalizeExportStatusPreference("Pick"), DEFAULT_EXPORT_STATUS_PREFERENCE);
});

test("loads default export statuses when storage is missing or malformed", () => {
  assert.deepEqual(loadExportStatusPreference(undefined), DEFAULT_EXPORT_STATUS_PREFERENCE);
  assert.deepEqual(
    loadExportStatusPreference(memoryStorage({ [EXPORT_STATUS_PREFERENCE_KEY]: "not json" })),
    DEFAULT_EXPORT_STATUS_PREFERENCE,
  );
});

test("saves normalized export status preferences locally", () => {
  const storage = memoryStorage();

  const saved = saveExportStatusPreference(["Maybe", "Pick"], storage);

  assert.deepEqual(saved, ["Pick", "Maybe"]);
  assert.equal(storage.values[EXPORT_STATUS_PREFERENCE_KEY], '["Pick","Maybe"]');
});

test("toggles and saves non-empty export status preferences", () => {
  const storage = memoryStorage();

  const saved = toggleExportStatusPreference(["Pick"], "Maybe", storage);

  assert.deepEqual(saved, ["Pick", "Maybe"]);
  assert.equal(storage.values[EXPORT_STATUS_PREFERENCE_KEY], '["Pick","Maybe"]');
});

test("allows a temporary empty export status selection without overwriting storage", () => {
  const storage = memoryStorage({ [EXPORT_STATUS_PREFERENCE_KEY]: '["Pick"]' });

  const selected = toggleExportStatusPreference(["Pick"], "Pick", storage);

  assert.deepEqual(selected, []);
  assert.equal(storage.values[EXPORT_STATUS_PREFERENCE_KEY], '["Pick"]');
});

test("detects the final selected export status", () => {
  assert.equal(isOnlySelectedExportStatus(["Pick"], "Pick"), true);
  assert.equal(isOnlySelectedExportStatus(["Pick", "Maybe"], "Pick"), false);
  assert.equal(isOnlySelectedExportStatus(["Pick"], "Maybe"), false);
});

test("keeps settings preferences non-empty when toggling the final status", () => {
  const storage = memoryStorage({ [EXPORT_STATUS_PREFERENCE_KEY]: '["Pick"]' });

  const result = toggleSavedExportStatusPreference(["Pick"], "Pick", storage);

  assert.deepEqual(result, {
    message: "Keep at least one default export status.",
    statuses: ["Pick"],
  });
  assert.equal(storage.values[EXPORT_STATUS_PREFERENCE_KEY], '["Pick"]');
});

test("saves settings preferences after valid toggles", () => {
  const storage = memoryStorage({ [EXPORT_STATUS_PREFERENCE_KEY]: '["Pick"]' });

  const result = toggleSavedExportStatusPreference(["Pick"], "Maybe", storage);

  assert.deepEqual(result, {
    message: "Saved locally.",
    statuses: ["Pick", "Maybe"],
  });
  assert.equal(storage.values[EXPORT_STATUS_PREFERENCE_KEY], '["Pick","Maybe"]');
});
