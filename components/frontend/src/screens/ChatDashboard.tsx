// Chat + Dashboard screen (ARCHITECTURE.md §5.2), chat-style: the user enters a
// change request; an in-app input guard validates it (simulating a Bedrock
// Guardrail); valid requests go to POST /analyze and the ResultEnvelope is
// appended to the conversation as a new set of impact cards. Each turn renders
// in the same format. Loading, generic errors (retry), the 409 not-READY path,
// and guard blocks are all surfaced per turn.

import { useCallback, useRef, useState } from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Form from '@cloudscape-design/components/form';
import FormField from '@cloudscape-design/components/form-field';
import Textarea from '@cloudscape-design/components/textarea';
import Button from '@cloudscape-design/components/button';
import Alert from '@cloudscape-design/components/alert';
import Badge from '@cloudscape-design/components/badge';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import ColumnLayout from '@cloudscape-design/components/column-layout';
import type { ApiClient } from '../api/client';
import { ApiError } from '../api/client';
import type { ResultEnvelope } from '../api/types';
import { evaluateInputGuard } from '../guard';
import { WhatBreaksCard } from '../cards/WhatBreaks';
import { WhatItCostsCard } from '../cards/WhatItCosts';
import { WhatItRisksCard } from '../cards/WhatItRisks';

interface Props {
  client: ApiClient;
  repoId: string;
  onReonboard: () => void;
}

type Turn =
  | { id: number; request: string; kind: 'result'; result: ResultEnvelope }
  | { id: number; request: string; kind: 'blocked'; message: string; categories?: string[] }
  | { id: number; request: string; kind: 'not_ready' }
  | { id: number; request: string; kind: 'error'; message: string };

// Distribute Omit across the union so variant-specific fields are preserved.
type DistributiveOmit<T, K extends keyof T> = T extends unknown ? Omit<T, K> : never;
type NewTurn = DistributiveOmit<Turn, 'id'>;

export function ChatDashboard({ client, repoId, onReonboard }: Props) {
  const [input, setInput] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const nextId = useRef(1);

  const append = (turn: NewTurn) =>
    setTurns((prev) => [{ ...turn, id: nextId.current++ } as Turn, ...prev]);

  const submit = useCallback(async () => {
    const request = input.trim();

    // Input guard runs before any /analyze call (simulated Bedrock Guardrail).
    const verdict = evaluateInputGuard(input);
    if (!verdict.allowed) {
      append({
        request: request || '(empty)',
        kind: 'blocked',
        message: verdict.reason ?? 'Request was blocked.',
        categories: verdict.categories,
      });
      setInput('');
      return;
    }

    setBusy(true);
    try {
      const result = await client.analyze({ repo_id: repoId, change_request: request });
      append({ request, kind: 'result', result });
      setInput('');
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        append({ request, kind: 'not_ready' });
      } else {
        append({
          request,
          kind: 'error',
          message:
            e instanceof ApiError
              ? `Analysis failed (${e.status}). Try again.`
              : 'Network error during analysis. Try again.',
        });
      }
    } finally {
      setBusy(false);
    }
  }, [input, client, repoId]);

  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header variant="h2" description={`Repository: ${repoId}`}>
            Change Impact Analysis
          </Header>
        }
      >
        <Form
          actions={
            <Button variant="primary" onClick={() => void submit()} loading={busy}>
              Send
            </Button>
          }
        >
          <FormField
            label="Ask about a change"
            description="Describe a change in plain English; each request adds a new analysis below."
          >
            <Textarea
              value={input}
              onChange={({ detail }) => setInput(detail.value)}
              placeholder="e.g. remove the Door component"
              disabled={busy}
              data-testid="change-request"
            />
          </FormField>
        </Form>
      </Container>

      {turns.length === 0 ? (
        <Box textAlign="center" color="text-status-inactive" data-testid="chat-empty">
          No requests yet. Ask something to see its impact analysis.
        </Box>
      ) : (
        <SpaceBetween size="l">
          {turns.map((turn) => (
            <ConversationTurn key={turn.id} turn={turn} onReonboard={onReonboard} />
          ))}
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
}

function UserBubble({ request }: { request: string }) {
  return (
    <Box data-testid="user-message">
      <SpaceBetween size="xxs">
        <Badge color="blue">You</Badge>
        <Box variant="p" fontWeight="bold">
          {request}
        </Box>
      </SpaceBetween>
    </Box>
  );
}

function ConversationTurn({ turn, onReonboard }: { turn: Turn; onReonboard: () => void }) {
  return (
    <SpaceBetween size="s">
      <UserBubble request={turn.request} />

      {turn.kind === 'result' ? <ResultReport result={turn.result} /> : null}

      {turn.kind === 'blocked' ? (
        <Alert type="warning" header="Request blocked by input guard" data-testid="guard-blocked">
          <SpaceBetween size="xs">
            <span>{turn.message}</span>
            {turn.categories?.length ? (
              <SpaceBetween size="xs" direction="horizontal">
                {turn.categories.map((c) => (
                  <Badge key={c} color="grey">
                    {c}
                  </Badge>
                ))}
              </SpaceBetween>
            ) : null}
          </SpaceBetween>
        </Alert>
      ) : null}

      {turn.kind === 'not_ready' ? (
        <Alert
          type="warning"
          header="Repository not ready"
          data-testid="analyze-409"
          action={<Button onClick={onReonboard}>Back to onboarding</Button>}
        >
          This repository is missing or not READY. Run onboarding first.
        </Alert>
      ) : null}

      {turn.kind === 'error' ? (
        <Alert type="error" header="Analysis error" data-testid="analyze-error">
          {turn.message}
        </Alert>
      ) : null}
    </SpaceBetween>
  );
}

function ResultReport({ result }: { result: ResultEnvelope }) {
  const targets = result.target_nodes ?? [];
  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header
            variant="h2"
            description="Analysis"
            actions={<Badge color="blue">confidence: {result.confidence?.level ?? 'n/a'}</Badge>}
          >
            {result.change_request}
          </Header>
        }
      >
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Target nodes</Box>
          {targets.length === 0 ? (
            <Box color="text-status-inactive">No targets resolved.</Box>
          ) : (
            <SpaceBetween size="xs" direction="horizontal">
              {targets.map((t) => (
                <Badge key={t.id} color="grey">
                  {t.label} ({t.type})
                </Badge>
              ))}
            </SpaceBetween>
          )}
        </SpaceBetween>
      </Container>

      <WhatBreaksCard data={result.what_breaks} />
      <ColumnLayout columns={2}>
        <WhatItCostsCard data={result.what_it_costs} />
        <WhatItRisksCard data={result.what_it_risks} />
      </ColumnLayout>
    </SpaceBetween>
  );
}
