// Thin HTTP client (ARCHITECTURE.md §6, §9). Browser-native `fetch` only — no
// AWS SDK, no credentials. When `useStub` is true, calls are served in-browser
// by the stub handler (§8.1); otherwise they go to `apiBaseUrl`.

import { loadConfig, type RuntimeConfig } from './config';
import { resolveStub } from '../mocks/handlers';
import type {
  AnalyzeRequest,
  IngestResponse,
  ResultEnvelope,
  StatusResponse,
} from './types';

/** Raised for non-2xx responses so screens can branch on status (e.g. 409). */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  cfg: RuntimeConfig,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = cfg.useStub ? path : `${cfg.apiBaseUrl}${path}`;

  let res: Response | null = null;
  if (cfg.useStub) {
    res = await resolveStub(url, init);
  }
  if (!res) {
    res = await fetch(url, init);
  }

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = undefined;
    }
    throw new ApiError(res.status, `Request to ${path} failed (${res.status})`, body);
  }

  return (await res.json()) as T;
}

const jsonInit = (method: string, payload: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
});

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// `/analyze` runs the model synchronously, but API Gateway caps the integration
// at 30s. A heavier change request can exceed that and return 503/504 — yet the
// Lambda keeps running and CACHES its ResultEnvelope (keyed by repo_id +
// change_request). So we transparently retry the same request: once the
// background run finishes, a retry is a fast cache hit. This turns a gateway
// timeout into a slightly longer, seamless wait instead of an error.
//
// Only gateway/transport failures are retried; deterministic outcomes (e.g. 409
// not-ready, 4xx) propagate immediately.
const ANALYZE_RETRYABLE_STATUS = new Set([502, 503, 504]);
const ANALYZE_MAX_ATTEMPTS = 6;
const ANALYZE_RETRY_DELAY_MS = 2500;

async function analyzeWithRetry(
  cfg: RuntimeConfig,
  req: AnalyzeRequest,
): Promise<ResultEnvelope> {
  let lastErr: unknown;
  for (let attempt = 1; attempt <= ANALYZE_MAX_ATTEMPTS; attempt++) {
    try {
      return await request<ResultEnvelope>(cfg, '/analyze', jsonInit('POST', req));
    } catch (e) {
      lastErr = e;
      const retryable =
        e instanceof ApiError ? ANALYZE_RETRYABLE_STATUS.has(e.status) : true; // network/transport error
      if (!retryable || attempt === ANALYZE_MAX_ATTEMPTS) throw e;
      await sleep(ANALYZE_RETRY_DELAY_MS);
    }
  }
  throw lastErr;
}

export interface ApiClient {
  ingest(githubUrl: string): Promise<IngestResponse>;
  status(repoId: string): Promise<StatusResponse>;
  analyze(req: AnalyzeRequest): Promise<ResultEnvelope>;
}

export async function createClient(cfg?: RuntimeConfig): Promise<ApiClient> {
  const resolved = cfg ?? (await loadConfig());
  return {
    ingest: (githubUrl) =>
      request<IngestResponse>(resolved, '/ingest', jsonInit('POST', { github_url: githubUrl })),
    status: (repoId) =>
      request<StatusResponse>(
        resolved,
        `/status?repo_id=${encodeURIComponent(repoId)}`,
        { method: 'GET' },
      ),
    analyze: (req) => analyzeWithRetry(resolved, req),
  };
}
