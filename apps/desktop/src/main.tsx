import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { invoke } from "@tauri-apps/api/core";
import { applyShellDataset } from "@/lib/shell";
import { App } from "./App";
import "./styles.css";

void invoke("qa_write_evidence", {
  line: JSON.stringify({ milestone: "spa_module", t: new Date().toISOString() }),
}).catch(() => undefined);

applyShellDataset();

const root = document.getElementById("root");
if (!root) {
  throw new Error("FramePilot desktop root element is missing");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
