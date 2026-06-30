// "What Breaks" card (ARCHITECTURE.md §5.2, §7): dependency tree/graph from
// what_breaks.graph and the per-element impacted[] list.

import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Box from '@cloudscape-design/components/box';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Table from '@cloudscape-design/components/table';
import ExpandableSection from '@cloudscape-design/components/expandable-section';
import type { WhatBreaks } from '../api/types';
import { SeverityBadge } from './SeverityBadge';

export function WhatBreaksCard({ data }: { data?: WhatBreaks }) {
  const impacted = data?.impacted ?? [];
  const edges = data?.graph?.edges ?? [];

  return (
    <Container header={<Header variant="h2" counter={`(${impacted.length})`}>What Breaks</Header>}>
      <SpaceBetween size="m">
        {data?.summary ? <Box variant="p">{data.summary}</Box> : null}

        <Table
          variant="embedded"
          items={impacted}
          empty={<Box textAlign="center" color="inherit">No impacted elements.</Box>}
          columnDefinitions={[
            {
              id: 'id',
              header: 'Element',
              cell: (i) => i.id,
              isRowHeader: true,
            },
            { id: 'type', header: 'Type', cell: (i) => i.type },
            { id: 'domain', header: 'Domain', cell: (i) => i.domain },
            { id: 'hops', header: 'Hops', cell: (i) => i.hops },
            {
              id: 'severity',
              header: 'Severity',
              cell: (i) => <SeverityBadge severity={i.severity} />,
            },
            {
              id: 'via',
              header: 'Via',
              cell: (i) => (i.via?.length ? i.via.join(' → ') : '—'),
            },
            { id: 'explanation', header: 'Explanation', cell: (i) => i.explanation },
          ]}
        />

        <ExpandableSection headerText={`Dependency graph (${edges.length} edges)`}>
          {edges.length === 0 ? (
            <Box color="text-status-inactive">No graph data.</Box>
          ) : (
            <ul>
              {edges.map((e, idx) => (
                <li key={idx}>
                  {e.from} → {e.to}
                  {e.label ? ` (${e.label})` : ''}
                </li>
              ))}
            </ul>
          )}
        </ExpandableSection>
      </SpaceBetween>
    </Container>
  );
}
