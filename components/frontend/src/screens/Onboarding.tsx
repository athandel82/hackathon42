// Onboarding screen (ARCHITECTURE.md §5.1): submit a GitHub repo URL, POST
// /ingest, then poll GET /status every ~2s until READY or FAILED.

import { useCallback, useEffect, useRef, useState } from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Form from '@cloudscape-design/components/form';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import Button from '@cloudscape-design/components/button';
import Alert from '@cloudscape-design/components/alert';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Spinner from '@cloudscape-design/components/spinner';
import ProgressBar from '@cloudscape-design/components/progress-bar';
import type { ApiClient } from '../api/client';
import { ApiError } from '../api/client';
import type { RepoStatus } from '../api/types';
import { INGEST_JOKES, nextRandomJokeIndex } from '../jokes';

const POLL_INTERVAL_MS = 2000;
const JOKE_INTERVAL_MS = 3000;
const PROGRESS_TICK_MS = 700;
const PROGRESS_CEILING = 93; // creep toward this while PENDING; snap to 100 on READY

interface Props {
  client: ApiClient;
  onReady: (repoId: string) => void;
}

export function Onboarding({ client, onReady }: Props) {
  const [githubUrl, setGithubUrl] = useState('');
  const [repoId, setRepoId] = useState<string | null>(null);
  const [status, setStatus] = useState<RepoStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jokeIndex, setJokeIndex] = useState(() =>
    Math.floor(Math.random() * INGEST_JOKES.length),
  );
  const [progress, setProgress] = useState(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimer = () => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  };

  useEffect(() => clearTimer, []);

  const pending = busy && status === 'PENDING';

  // Rotate to a RANDOM joke while we wait on ingestion (never repeats back-to-back).
  useEffect(() => {
    if (!pending) return;
    const id = setInterval(
      () => setJokeIndex((i) => nextRandomJokeIndex(i)),
      JOKE_INTERVAL_MS,
    );
    return () => clearInterval(id);
  }, [pending]);

  // Simulated progress: ease toward a ceiling while PENDING; snap to 100 on READY.
  // The real signal is the /status poll — this just makes the wait feel alive.
  useEffect(() => {
    if (!pending) return;
    const id = setInterval(() => {
      setProgress((p) =>
        p >= PROGRESS_CEILING ? PROGRESS_CEILING : p + Math.max(0.5, (PROGRESS_CEILING - p) * 0.06),
      );
    }, PROGRESS_TICK_MS);
    return () => clearInterval(id);
  }, [pending]);

  const poll = useCallback(
    async (id: string) => {
      try {
        const { status: s } = await client.status(id);
        setStatus(s);
        if (s === 'READY') {
          setProgress(100);
          setBusy(false);
          onReady(id);
          return;
        }
        if (s === 'FAILED') {
          setBusy(false);
          setError('Ingestion failed for this repository. Check the URL and retry.');
          return;
        }
        timer.current = setTimeout(() => void poll(id), POLL_INTERVAL_MS);
      } catch (e) {
        setBusy(false);
        setError(
          e instanceof ApiError
            ? `Status check failed (${e.status}). Retry.`
            : 'Network error while checking status. Retry.',
        );
      }
    },
    [client, onReady],
  );

  const start = useCallback(async () => {
    if (!githubUrl.trim()) {
      setError('Enter a GitHub repository URL.');
      return;
    }
    clearTimer();
    setError(null);
    setStatus(null);
    setJokeIndex(Math.floor(Math.random() * INGEST_JOKES.length));
    setProgress(0);
    setBusy(true);
    try {
      const { repo_id } = await client.ingest(githubUrl.trim());
      setRepoId(repo_id);
      setStatus('PENDING');
      void poll(repo_id);
    } catch (e) {
      setBusy(false);
      setError(
        e instanceof ApiError
          ? `Failed to start ingestion (${e.status}). Retry.`
          : 'Network error while starting ingestion. Retry.',
      );
    }
  }, [githubUrl, client, poll]);

  return (
    <Container header={<Header variant="h1" description="Paste a GitHub repository URL to ingest its AUTOSAR ARXML.">Onboarding</Header>}>
      <SpaceBetween size="l">
        <Form
          actions={
            <Button variant="primary" onClick={() => void start()} loading={busy}>
              {error ? 'Retry' : 'Ingest repository'}
            </Button>
          }
        >
          <FormField label="GitHub repository URL">
            <Input
              value={githubUrl}
              onChange={({ detail }) => setGithubUrl(detail.value)}
              placeholder="https://github.com/owner/repo"
              disabled={busy}
              data-testid="github-url"
            />
          </FormField>
        </Form>

        {error ? (
          <Alert type="error" header="Onboarding error" data-testid="onboarding-error">
            {error}
          </Alert>
        ) : null}

        {busy && status === 'PENDING' ? (
          <Box data-testid="onboarding-pending">
            <SpaceBetween size="s">
              <ProgressBar
                value={Math.round(progress)}
                label="Building the knowledge base"
                description={repoId ? `Ingesting ${repoId}` : 'Ingesting repository'}
                additionalInfo="Parsing ARXML, resolving ports, and mapping signal chains…"
              />
              <Box
                data-testid="onboarding-pending-joke"
                padding={{ vertical: 'xs', horizontal: 's' }}
              >
                <SpaceBetween size="xs" direction="horizontal">
                  <Spinner />
                  <span data-testid="onboarding-pending-message" style={{ fontStyle: 'italic' }}>
                    {INGEST_JOKES[jokeIndex]}
                  </span>
                </SpaceBetween>
              </Box>
            </SpaceBetween>
          </Box>
        ) : null}

        {status === 'READY' ? (
          <Alert type="success" header="Ready">
            Repository <strong>{repoId}</strong> is ready for analysis.
          </Alert>
        ) : null}
      </SpaceBetween>
    </Container>
  );
}
