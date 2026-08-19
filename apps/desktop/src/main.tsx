import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function App() {
  return (
    <main className="min-h-screen bg-mist text-ink">
      <h1 className="border-b border-line bg-white px-5 py-4 font-semibold text-leaf">FramePilot</h1>
      <p className="px-5 py-4 text-coral">Desktop shell is loading.</p>
    </main>
  );
}

const root = document.getElementById("root");
if (!root) {
  throw new Error("FramePilot desktop root element is missing");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
