import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { applyShellDataset } from "@/lib/shell";
import { App } from "./App";
import "./styles.css";

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
