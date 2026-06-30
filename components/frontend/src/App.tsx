import { useState } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import ContentLayout from '@cloudscape-design/components/content-layout';
import Header from '@cloudscape-design/components/header';
import type { ApiClient } from './api/client';
import { Onboarding } from './screens/Onboarding';
import { ChatDashboard } from './screens/ChatDashboard';

interface Props {
  client: ApiClient;
}

export function App({ client }: Props) {
  const [repoId, setRepoId] = useState<string | null>(null);

  return (
    <AppLayout
      navigationHide
      toolsHide
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="The reverse of the Software-Defined Vehicle: bring proven legacy automotive architectures back to market. Analyze the blast radius of changing or removing ECUs in existing AUTOSAR designs — before you touch them."
            >
              <span style={{ textDecoration: 'line-through', opacity: 0.45 }}>S</span>DV — Still
              Defined Vehicle
            </Header>
          }
        >
          {repoId === null ? (
            <Onboarding client={client} onReady={setRepoId} />
          ) : (
            <ChatDashboard
              client={client}
              repoId={repoId}
              onReonboard={() => setRepoId(null)}
            />
          )}
        </ContentLayout>
      }
    />
  );
}
