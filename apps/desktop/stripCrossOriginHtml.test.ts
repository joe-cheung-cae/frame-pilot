import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { stripCrossOriginHtml } from "./stripCrossOriginHtml.ts";

test("stripCrossOriginHtml removes Vite module and stylesheet crossorigin", () => {
  const html = `<!doctype html>
<html lang="en" data-shell="desktop">
  <head>
    <script type="module" crossorigin src="/assets/index-BsVPiZtg.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-DJVhb-Ah.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
`;
  const out = stripCrossOriginHtml(html);
  assert.equal(out.includes("crossorigin"), false);
  assert.equal(out.includes('src="/assets/index-BsVPiZtg.js"'), true);
  assert.equal(out.includes('href="/assets/index-DJVhb-Ah.css"'), true);
});

test("vite.config uses relative base and the shipped strip helper", () => {
  const config = readFileSync(new URL("./vite.config.ts", import.meta.url), "utf8");
  assert.match(config, /base:\s*["']\.\/["']/);
  assert.match(config, /stripCrossOriginHtml/);
  assert.match(config, /transformIndexHtml/);
});
