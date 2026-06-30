import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createClient, ApiError } from '../api/client';
import { resetStub } from '../mocks/handlers';

const stubCfg = { apiBaseUrl: '', useStub: true };

const liveCfg = { apiBaseUrl: 'https://api.test', useStub: false };

const jsonResponse = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const sampleEnvelope = {
  change_request: 'c',
  target_nodes: [],
  what_breaks: { summary: '', impacted: [], graph: { nodes: [], edges: [] } },
  what_it_costs: { bom_saved: { low: 0, high: 0 }, eng_rework: { low: 0, high: 0 }, net_assessment: 'neutral', line_items: [] },
  what_it_risks: { items: [] },
  confidence: { level: 'low' },
};

describe('API client (stub mode)', () => {
  beforeEach(() => resetStub());

  it('POST /ingest returns a repo_id', async () => {
    const client = await createClient(stubCfg);
    const res = await client.ingest('https://github.com/owner/repo');
    expect(res.repo_id).toBe('demo');
  });

  it('GET /status cycles PENDING then READY (poll loop)', async () => {
    const client = await createClient(stubCfg);
    const seen: string[] = [];
    for (let i = 0; i < 4; i++) {
      const { status } = await client.status('demo');
      seen.push(status);
    }
    expect(seen[0]).toBe('PENDING');
    expect(seen).toContain('READY');
    // Once READY is reached it stays READY.
    expect(seen[seen.length - 1]).toBe('READY');
  });

  it('POST /analyze returns the full ResultEnvelope', async () => {
    const client = await createClient(stubCfg);
    const res = await client.analyze({ repo_id: 'demo', change_request: 'remove the Door component' });
    expect(res.change_request).toBeTruthy();
    expect(res.what_breaks.impacted.length).toBeGreaterThan(0);
    expect(res.confidence.level).toBeTruthy();
  });

  it('POST /analyze surfaces a 409 as ApiError for a missing/not-READY repo', async () => {
    const client = await createClient(stubCfg);
    await expect(
      client.analyze({ repo_id: 'demo', change_request: 'analyze missing-repo' }),
    ).rejects.toMatchObject({ status: 409 });
    await expect(
      client.analyze({ repo_id: 'demo', change_request: 'analyze missing-repo' }),
    ).rejects.toBeInstanceOf(ApiError);
  });
});

describe('API client analyze retry (live mode)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('retries on a 503 gateway timeout and returns the (now-cached) result', async () => {
    let calls = 0;
    const fetchMock = vi.fn(async () => {
      calls += 1;
      return calls === 1
        ? jsonResponse({ message: 'Service Unavailable' }, 503) // first attempt times out at the gateway
        : jsonResponse(sampleEnvelope, 200); // background run cached -> retry hits it
    });
    vi.stubGlobal('fetch', fetchMock);
    vi.useFakeTimers();

    const client = await createClient(liveCfg);
    const p = client.analyze({ repo_id: 'r', change_request: 'c' });
    await vi.advanceTimersByTimeAsync(5000); // skip the retry backoff
    const res = await p;

    expect(calls).toBe(2);
    expect(res.confidence.level).toBe('low');
  });

  it('does NOT retry deterministic outcomes (e.g. 409 not-ready)', async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ error: 'not ready' }, 409));
    vi.stubGlobal('fetch', fetchMock);

    const client = await createClient(liveCfg);
    await expect(
      client.analyze({ repo_id: 'r', change_request: 'c' }),
    ).rejects.toMatchObject({ status: 409 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
