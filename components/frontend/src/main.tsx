// Entry point (ARCHITECTURE.md §9): load runtime config.json first, enable the
// in-browser stub when configured, build the API client, then mount the app.

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@cloudscape-design/global-styles/index.css';
import { App } from './App';
import { loadConfig } from './api/config';
import { createClient } from './api/client';
import { installStub } from './mocks/handlers';

async function bootstrap() {
  const cfg = await loadConfig();
  if (cfg.useStub) {
    installStub();
  }
  const client = await createClient(cfg);

  const rootEl = document.getElementById('root');
  if (!rootEl) throw new Error('Root element #root not found');

  createRoot(rootEl).render(
    <StrictMode>
      <App client={client} />
    </StrictMode>,
  );
}

void bootstrap();
