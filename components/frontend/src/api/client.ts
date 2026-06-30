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
    analyze: (req) => request<ResultEnvelope>(resolved, '/analyze', jsonInit('POST', req)),
  };
}
