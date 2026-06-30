import { describe, it, expect } from 'vitest';
import { INGEST_JOKES, nextRandomJokeIndex } from '../jokes';

describe('ingestion jokes', () => {
  it('provides 100 distinct jokes', () => {
    expect(INGEST_JOKES).toHaveLength(100);
    expect(new Set(INGEST_JOKES).size).toBe(100); // all unique
  });

  it('nextRandomJokeIndex never repeats the current index and stays in range', () => {
    for (let current = 0; current < INGEST_JOKES.length; current++) {
      for (let trial = 0; trial < 20; trial++) {
        const next = nextRandomJokeIndex(current);
        expect(next).not.toBe(current);
        expect(next).toBeGreaterThanOrEqual(0);
        expect(next).toBeLessThan(INGEST_JOKES.length);
      }
    }
  });
});
