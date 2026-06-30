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

// Relative column widths as PERCENTAGES (coefficient ÷ total), so the table
// stays responsive: with table-layout:auto + a full-width table, percentage
// column widths rescale as the window resizes while preserving the requested
// ratios. wrapLines keeps long text inside its column instead of scrolling.
// Coefficients: Element 1, Type 1, Domain 1, Hops 1, Severity 1, Via 3, Explanation 4.
const COL_TOTAL = 12;
const pct = (coef: number) => `${((coef / COL_TOTAL) * 100).toFixed(2)}%`;

export function WhatBreaksCard({ data }: { data?: WhatBreaks }) {
  const impacted = data?.impacted ?? [];
  const edges = data?.graph?.edges ?? [];

  return (
    <Container header={<Header variant="h2" counter={`(${impacted.length})`}>What Breaks</Header>}>
      <SpaceBetween size="m">
        {data?.summary ? <Box variant="p">{data.summary}</Box> : null}

        <Table
          variant="embedded"
          wrapLines
          items={impacted}
          empty={<Box textAlign="center" color="inherit">No impacted elements.</Box>}
          columnDefinitions={[
            {
              id: 'id',
              header: 'Element',
              cell: (i) => i.id,
              isRowHeader: true,
              width: pct(1),
            },
            { id: 'type', header: 'Type', cell: (i) => i.type, width: pct(1) },
            { id: 'domain', header: 'Domain', cell: (i) => i.domain, width: pct(1) },
            { id: 'hops', header: 'Hops', cell: (i) => i.hops, width: pct(1) },
            {
              id: 'severity',
              header: 'Severity',
              cell: (i) => <SeverityBadge severity={i.severity} />,
              width: pct(1),
            },
            {
              id: 'via',
              header: 'Via',
              cell: (i) => (i.via?.length ? i.via.join(' → ') : '—'),
              width: pct(3),
            },
            {
              id: 'explanation',
              header: 'Explanation',
              cell: (i) => i.explanation,
              width: pct(4),
            },
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
