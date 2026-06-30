import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { Onboarding } from '../screens/Onboarding';
import { ChatDashboard } from '../screens/ChatDashboard';
import { createClient } from '../api/client';
import { resetStub } from '../mocks/handlers';

const stubCfg = { apiBaseUrl: '', useStub: true };

describe('Onboarding screen', () => {
  beforeEach(() => resetStub());

  it('ingests then polls status until READY and fires onReady', async () => {
    const client = await createClient(stubCfg);
    const onReady = vi.fn();
    const user = userEvent.setup();

    render(<Onboarding client={client} onReady={onReady} />);

    await user.type(screen.getByTestId('github-url').querySelector('input')!, 'https://github.com/owner/repo');
    await user.click(screen.getByRole('button', { name: /ingest repository/i }));

    // Eventually reaches READY (poll loop PENDING → READY) and notifies parent.
    await waitFor(() => expect(onReady).toHaveBeenCalledWith('demo'), { timeout: 10000 });
    expect(screen.getByText('Ready')).toBeInTheDocument();
  }, 15000);

  it('shows an error alert when the URL is empty', async () => {
    const client = await createClient(stubCfg);
    const user = userEvent.setup();
    render(<Onboarding client={client} onReady={vi.fn()} />);
    await user.click(screen.getByRole('button', { name: /ingest repository/i }));
    expect(await screen.findByTestId('onboarding-error')).toBeInTheDocument();
  });
});

describe('ChatDashboard screen', () => {
  beforeEach(() => resetStub());

  it('renders impact cards from a successful analyze', async () => {
    const client = await createClient(stubCfg);
    const user = userEvent.setup();
    render(<ChatDashboard client={client} repoId="demo" onReonboard={vi.fn()} />);

    await user.type(screen.getByTestId('change-request').querySelector('textarea')!, 'remove the Door component');
    await user.click(screen.getByRole('button', { name: /send/i }));

    expect(await screen.findByText('What Breaks')).toBeInTheDocument();
    expect(screen.getByText('What it Costs')).toBeInTheDocument();
    expect(screen.getByText('What it Risks')).toBeInTheDocument();
    expect(screen.getByText('DoorControl')).toBeInTheDocument();
  });

  it('appends a new set of cards per request (chat transcript)', async () => {
    const client = await createClient(stubCfg);
    const user = userEvent.setup();
    render(<ChatDashboard client={client} repoId="demo" onReonboard={vi.fn()} />);
    const textarea = () => screen.getByTestId('change-request').querySelector('textarea')!;

    await user.type(textarea(), 'remove the Door component');
    await user.click(screen.getByRole('button', { name: /send/i }));
    await screen.findByText('What Breaks');

    await user.type(textarea(), 'reroute the window-position signal');
    await user.click(screen.getByRole('button', { name: /send/i }));

    // Two turns → two "What Breaks" cards and two user bubbles.
    await waitFor(() => expect(screen.getAllByText('What Breaks')).toHaveLength(2));
    expect(screen.getAllByTestId('user-message')).toHaveLength(2);
  });

  it('blocks an off-topic / invalid request via the input guard (no analyze)', async () => {
    const client = await createClient(stubCfg);
    const user = userEvent.setup();
    render(<ChatDashboard client={client} repoId="demo" onReonboard={vi.fn()} />);

    await user.type(screen.getByTestId('change-request').querySelector('textarea')!, 'what is the weather today');
    await user.click(screen.getByRole('button', { name: /send/i }));

    expect(await screen.findByTestId('guard-blocked')).toBeInTheDocument();
    expect(screen.queryByText('What Breaks')).not.toBeInTheDocument();
  });

  it('prompts to re-run onboarding on a 409', async () => {
    const client = await createClient(stubCfg);
    const onReonboard = vi.fn();
    const user = userEvent.setup();
    render(<ChatDashboard client={client} repoId="demo" onReonboard={onReonboard} />);

    await user.type(screen.getByTestId('change-request').querySelector('textarea')!, 'remove the missing-repo module');
    await user.click(screen.getByRole('button', { name: /send/i }));

    expect(await screen.findByTestId('analyze-409')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /back to onboarding/i }));
    expect(onReonboard).toHaveBeenCalled();
  });
});
