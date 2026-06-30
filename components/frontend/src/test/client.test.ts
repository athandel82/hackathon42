import { describe, it, expect, beforeEach } from 'vitest';
import { createClient, ApiError } from '../api/client';
import { resetStub } from '../mocks/handlers';

const stubCfg = { apiBaseUrl: '', useStub: true };

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
