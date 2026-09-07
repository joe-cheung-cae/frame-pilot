import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { invoke } from "@tauri-apps/api/core";
import { applyShellDataset } from "@/lib/shell";
import { App } from "./App";
import { applyDesktopQaBootstrap, parseDesktopQaBootstrap, spaFlagsLine } from "./lib/desktopQaRunner";
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
})();
