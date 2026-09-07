export {};

declare global {
  interface Window {
    __FRAMEPILOT_API_BASE__?: string;
    __FRAMEPILOT_DESKTOP__?: boolean;
    __FRAMEPILOT_WINDOW__?: "main" | "preview";
    __FRAMEPILOT_DESKTOP_QA__?: {
      photos: string;
      project: string;
      evidence?: string;
    };
  }
}
