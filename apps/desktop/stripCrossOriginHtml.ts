/** Vite emits `crossorigin` on script/link tags. Tauri custom-protocol CORS then blocks the SPA. */

export function stripCrossOriginHtml(html: string): string {
  return html.replace(/\s+crossorigin(?:="[^"]*")?/gi, "");
}
