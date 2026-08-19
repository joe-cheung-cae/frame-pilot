const status = document.getElementById("status");
const base = window.__FRAMEPILOT_API_BASE__ || "http://127.0.0.1:8000";
fetch(base.replace(/\/$/, "") + "/health")
  .then((response) => {
    if (!response.ok) throw new Error("health " + response.status);
    return response.json();
  })
  .then((payload) => {
    if (payload && payload.status === "ok") {
      status.textContent = "API ready";
    } else {
      status.textContent = "Unexpected health payload";
    }
  })
  .catch((error) => {
    status.textContent = String(error && error.message ? error.message : error);
  });
