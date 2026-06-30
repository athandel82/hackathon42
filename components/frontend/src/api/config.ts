// Runtime configuration (ARCHITECTURE.md §4). Fetched once from
// `public/config.json` at startup, before first render, so the same build can
// target a stub, a dev API, or a deployed API by editing one file — no rebuild.

export interface RuntimeConfig {
  apiBaseUrl: string;
  useStub: boolean;
}

const DEFAULTS: RuntimeConfig = {
  apiBaseUrl: '',
  useStub: false,
};

let cached: RuntimeConfig | null = null;

export async function loadConfig(): Promise<RuntimeConfig> {
  if (cached) return cached;

  let fileCfg: Partial<RuntimeConfig> = {};
  try {
    const res = await fetch('/config.json', { cache: 'no-store' });
    if (res.ok) {
      fileCfg = (await res.json()) as Partial<RuntimeConfig>;
    }
  } catch {
    // Missing/invalid config.json → fall back to defaults (live, no stub).
  }

  // Build-time VITE_API_BASE_URL may override apiBaseUrl during local dev (§4),
  // but config.json remains the source of truth for deployed builds.
  const envBase = import.meta.env?.VITE_API_BASE_URL as string | undefined;

  cached = {
    apiBaseUrl: envBase || fileCfg.apiBaseUrl || DEFAULTS.apiBaseUrl,
    useStub: fileCfg.useStub ?? DEFAULTS.useStub,
  };
  return cached;
}

/** Test helper — clears the memoized config. */
export function resetConfig(): void {
  cached = null;
}
