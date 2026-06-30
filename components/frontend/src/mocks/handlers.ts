// In-browser stub (ARCHITECTURE.md §8.1). A simple `fetch` shim — one handler
// file plus the fixtures in ./fixtures — so the SPA is fully developable and
// testable without the backend or AWS.

import ingest from './fixtures/ingest.json';
import statusReady from './fixtures/status.json';
import analyze from './fixtures/analyze.json';
import analyze409 from './fixtures/analyze-409.json';

const json = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

// Status poll loop: report PENDING a few times, then READY (§5.1, §8.1).
const PENDING_POLLS = 2;
const pollCounts = new Map<string, number>();

function handleStatus(url: URL): Response {
  const repoId = url.searchParams.get('repo_id') ?? 'demo';
  const seen = pollCounts.get(repoId) ?? 0;
  pollCounts.set(repoId, seen + 1);
  if (seen < PENDING_POLLS) {
    return json({ status: 'PENDING' });
  }
  return json(statusReady);
}

/**
 * Resolve a single stubbed request to a Response, or `null` if the path is not
 * handled (callers may then fall through to the real network).
 */
export async function resolveStub(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response | null> {
  const rawUrl = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
  const method = (init?.method ?? (input instanceof Request ? input.method : 'GET')).toUpperCase();
  // Tolerate relative URLs (same-origin calls) by giving them a dummy base.
  const url = new URL(rawUrl, 'http://stub.local');
  const path = url.pathname;

  // Simulate a little latency so loading states are exercisable.
  await new Promise((r) => setTimeout(r, 0));

  if (path.endsWith('/ingest') && method === 'POST') {
    return json(ingest, 202);
  }
  if (path.endsWith('/status') && method === 'GET') {
    return handleStatus(url);
  }
  if (path.endsWith('/analyze') && method === 'POST') {
    // A change request mentioning "missing" / "unknown" exercises the 409 path.
    let body: { change_request?: string } = {};
    try {
      body = init?.body ? JSON.parse(String(init.body)) : {};
    } catch {
      body = {};
    }
    const cr = (body.change_request ?? '').toLowerCase();
    if (cr.includes('missing-repo') || cr.includes('not-ready')) {
      return json(analyze409, 409);
    }
    return json(analyze, 200);
  }

  return null;
}

/** Reset internal stub state (used by tests). */
export function resetStub(): void {
  pollCounts.clear();
}

let installed = false;

/** Patch global `fetch` to serve stubbed routes; real fetch handles the rest. */
export function installStub(): void {
  if (installed) return;
  installed = true;
  const realFetch = globalThis.fetch.bind(globalThis);
  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const stubbed = await resolveStub(input, init);
    return stubbed ?? realFetch(input, init);
  };
}
