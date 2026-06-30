// "What it Risks" card (ARCHITECTURE.md §5.2, §7): severity-sorted list,
// flagged on revalidation_required.

import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Box from '@cloudscape-design/components/box';
import Badge from '@cloudscape-design/components/badge';
import SpaceBetween from '@cloudscape-design/components/space-between';
import type { WhatItRisks } from '../api/types';
import { SeverityBadge, severityRank } from './SeverityBadge';

export function WhatItRisksCard({ data }: { data?: WhatItRisks }) {
  const items = [...(data?.items ?? [])].sort(
    (a, b) => severityRank[b.severity] - severityRank[a.severity],
  );

  return (
    <Container header={<Header variant="h2" counter={`(${items.length})`}>What it Risks</Header>}>
      {items.length === 0 ? (
        <Box textAlign="center" color="inherit">No risks identified.</Box>
      ) : (
        <SpaceBetween size="m">
          {items.map((r, idx) => (
            <div key={idx}>
              <SpaceBetween size="xs">
                <SpaceBetween size="xs" direction="horizontal">
                  <SeverityBadge severity={r.severity} />
                  <Badge color="grey">{r.category}</Badge>
                  {r.revalidation_required ? (
                    <Badge color="red">revalidation required</Badge>
                  ) : null}
                </SpaceBetween>
                <Box variant="strong">{r.title}</Box>
                <Box variant="p">{r.detail}</Box>
              </SpaceBetween>
            </div>
          ))}
        </SpaceBetween>
      )}
    </Container>
  );
}
