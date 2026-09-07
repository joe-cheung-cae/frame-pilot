import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { invoke } from "@tauri-apps/api/core";
import { applyShellDataset } from "@/lib/shell";
import { resolveApiBase } from "@/lib/apiBase";
import { App } from "./App";
import {
  applyDesktopQaBootstrap,
  historyPush,
  parseDesktopQaBootstrap,
  spaFlagsLine,
  startDesktopQaFromWindow,
} from "./lib/desktopQaRunner";
import "./styles.css";

function writeQaLine(line: string): void {
  void invoke("qa_write_evidence", { line }).catch(() => undefined);
}

async function bootDesktopQaFlags(): Promise<boolean> {
  try {
    const boot = parseDesktopQaBootstrap(await invoke("qa_bootstrap"));
    return applyDesktopQaBootstrap(typeof window === "undefined" ? undefined : window, boot);
  } catch {
    return false;
  }
}

async function probeSidecarFetch(): Promise<void> {
  const url = `${resolveApiBase()}/api/health`;
  writeQaLine(JSON.stringify({ milestone: "spa_fetch", t: new Date().toISOString(), url }));
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(url, { signal: controller.signal });
    writeQaLine(
      JSON.stringify({
        milestone: "spa_fetch_done",
        t: new Date().toISOString(),
        status: response.status,
      }),
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    writeQaLine(
      JSON.stringify({
        milestone: "spa_fetch_fail",
        t: new Date().toISOString(),
        fail_reason: message.slice(0, 200),
      }),
    );
  } finally {
    clearTimeout(timer);
  }
}

const root = document.getElementById("root");
if (!root) {
  throw new Error("FramePilot desktop root element is missing");
}

void (async () => {
  const bootstrapped = await bootDesktopQaFlags();
  writeQaLine(JSON.stringify({ milestone: "spa_module", t: new Date().toISOString() }));
  writeQaLine(spaFlagsLine(new Date().toISOString(), window, bootstrapped));
  applyShellDataset();
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
  await probeSidecarFetch();
  void startDesktopQaFromWindow({
    push: historyPush,
  });
})();
