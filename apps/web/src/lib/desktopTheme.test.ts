import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";

import { colorHex, colors } from "../theme/tokens.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const srcRoot = path.resolve(here, "..");
const repoRoot = path.resolve(here, "../../../..");

function read(relFromSrc: string): string {
  return fs.readFileSync(path.join(srcRoot, relFromSrc), "utf8");
}

function readRepo(relFromRoot: string): string {
  return fs.readFileSync(path.join(repoRoot, relFromRoot), "utf8");
}

function rgbLuma(triplet: string): number {
  const parts = triplet.trim().split(/\s+/).map(Number);
  assert.equal(parts.length, 3, `expected rgb triplet, got ${triplet}`);
  const [r, g, b] = parts;
  assert.ok(parts.every((n) => Number.isFinite(n)), `non-numeric rgb ${triplet}`);
  return 0.299 * r + 0.587 * g + 0.114 * b;
}

function cssVarBlock(source: string, selectorPattern: RegExp): string {
  const match = source.match(selectorPattern);
  assert.ok(match, `missing CSS block for ${selectorPattern}`);
  return match[0];
}

function cssVarRgb(block: string, name: string): string {
  const match = block.match(new RegExp(`${name}:\\s*([0-9]+\\s+[0-9]+\\s+[0-9]+)`));
  assert.ok(match, `missing ${name} rgb triplet in block`);
  return match[1];
}

test("web and desktop Tailwind configs have no darkMode", () => {
  const webConfig = readRepo("apps/web/tailwind.config.ts");
  const desktopConfig = readRepo("apps/desktop/tailwind.config.ts");
  assert.doesNotMatch(webConfig, /darkMode/);
  assert.doesNotMatch(desktopConfig, /darkMode/);
  assert.doesNotMatch(webConfig, /desktopSystemDarkMode/);
  assert.doesNotMatch(desktopConfig, /desktopSystemDarkMode/);
});

test("design tokens expose surface and muted as CSS variables", () => {
  const tokens = read("theme/tokens.ts");
  assert.match(colors.ink, /var\(--fp-ink\)/);
  assert.match(colors.mist, /var\(--fp-mist\)/);
  assert.match(colors.line, /var\(--fp-line\)/);
  assert.match(colors.surface, /var\(--fp-surface\)/);
  assert.match(colors.muted, /var\(--fp-muted\)/);
  assert.match(tokens, /surface:\s*"rgb\(var\(--fp-surface\)/);
  assert.match(tokens, /muted:\s*"rgb\(var\(--fp-muted\)/);
  assert.equal(colorHex.leaf, "#2f6f5e");
  assert.equal(colorHex.coral, "#bf5b45");
  assert.equal(colorHex.gold, "#a77721");
});

test("browser globals stay light-only and do not remap .bg-white", () => {
  const globals = read("app/globals.css");
  assert.match(globals, /color-scheme:\s*light/);
  assert.doesNotMatch(globals, /\[data-shell=["']desktop["']\]/);
  assert.doesNotMatch(globals, /\.bg-white\s*\{[^}]*background/);
  const root = cssVarBlock(globals, /:root\s*\{[\s\S]*?\}/);
  const surface = rgbLuma(cssVarRgb(root, "--fp-surface"));
  const muted = rgbLuma(cssVarRgb(root, "--fp-muted"));
  assert.ok(muted < surface, "light muted text must be darker than surface");
});

test("desktop dark theme swaps surface and muted together without utility remaps", () => {
  const styles = readRepo("apps/desktop/src/styles.css");
  assert.match(styles, /prefers-color-scheme:\s*dark/);
  assert.match(styles, /\[data-shell=["']desktop["']\]/);
  assert.doesNotMatch(styles, /\.bg-white\s*\{[^}]*background/);
  const dark = cssVarBlock(
    styles,
    /@media\s*\(prefers-color-scheme:\s*dark\)\s*\{[\s\S]*?html\[data-shell=["']desktop["']\][\s\S]*?\{[\s\S]*?\}/,
  );
  const surface = rgbLuma(cssVarRgb(dark, "--fp-surface"));
  const muted = rgbLuma(cssVarRgb(dark, "--fp-muted"));
  assert.ok(muted > surface, "dark muted text must be lighter than surface");
});

test("desktop chrome uses surface/muted tokens and ink CTAs use mist not frozen white", () => {
  const shell = read("components/Shell.tsx");
  const status = read("components/StatusBar.tsx");
  assert.doesNotMatch(shell, /\bdark:/);
  assert.doesNotMatch(status, /\bdark:/);
  assert.match(status, /bg-surface/);
  assert.match(status, /text-muted/);
  assert.doesNotMatch(status, /bg-white/);
  assert.doesNotMatch(status, /text-neutral-700/);
  assert.match(shell, /bg-ink[\s\S]*text-mist/);
  assert.doesNotMatch(shell, /bg-ink[\s\S]*text-white/);
});
