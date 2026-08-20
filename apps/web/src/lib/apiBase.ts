const DEFAULT_API_BASE = "http://127.0.0.1:8000";

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function nonemptyBase(value: unknown): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed || undefined;
}

function readWindowApiBase(): string | undefined {
  const win = (globalThis as { window?: Window }).window;
  return nonemptyBase(win?.__FRAMEPILOT_API_BASE__);
}

function readEnvApiBase(): string | undefined {
  return nonemptyBase(process.env.NEXT_PUBLIC_API_BASE_URL);
}

export function resolveApiBase(): string {
  const fromWindow = readWindowApiBase();
  if (fromWindow) {
    return trimTrailingSlash(fromWindow);
  }
  const fromEnv = readEnvApiBase();
  if (fromEnv) {
    return trimTrailingSlash(fromEnv);
  }
  return DEFAULT_API_BASE;
}
