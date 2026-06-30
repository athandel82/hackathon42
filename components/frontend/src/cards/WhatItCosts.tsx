// "What it Costs" card (ARCHITECTURE.md §5.2, §7): savings-vs-rework ranges,
// net-assessment headline, and a line-item breakdown.

import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Box from '@cloudscape-design/components/box';
import Badge from '@cloudscape-design/components/badge';
import SpaceBetween from '@cloudscape-design/components/space-between';
import ColumnLayout from '@cloudscape-design/components/column-layout';
import Table from '@cloudscape-design/components/table';
import type { NetAssessment, Range, WhatItCosts } from '../api/types';

const ASSESSMENT_COLOR: Record<NetAssessment, 'green' | 'grey' | 'red'> = {
  favorable: 'green',
  neutral: 'grey',
  unfavorable: 'red',
};

function formatRange(r?: Range): string {
  if (!r) return '—';
  const prefix = r.currency ? `${r.currency} ` : '';
  const suffix = r.unit ? ` ${r.unit}` : '';
  const basis = r.basis ? ` (${r.basis})` : '';
  return `${prefix}${r.low}–${r.high}${suffix}${basis}`;
}

export function WhatItCostsCard({ data }: { data?: WhatItCosts }) {
  if (!data) {
    return (
      <Container header={<Header variant="h2">What it Costs</Header>}>
        <Box textAlign="center" color="inherit">No cost estimate available.</Box>
      </Container>
    );
  }

  const lineItems = data.line_items ?? [];

  return (
    <Container
      header={
        <Header
          variant="h2"
          actions={
            data.net_assessment ? (
              <Badge color={ASSESSMENT_COLOR[data.net_assessment]}>{data.net_assessment}</Badge>
            ) : undefined
          }
        >
          What it Costs
        </Header>
      }
    >
      <SpaceBetween size="m">
        <ColumnLayout columns={2} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">BOM saved</Box>
            <Box variant="p">{formatRange(data.bom_saved)}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Engineering rework</Box>
            <Box variant="p">{formatRange(data.eng_rework)}</Box>
          </div>
        </ColumnLayout>

        <Table
          variant="embedded"
          items={lineItems}
          empty={<Box textAlign="center" color="inherit">No line items.</Box>}
          columnDefinitions={[
            { id: 'label', header: 'Line item', cell: (i) => i.label, isRowHeader: true },
            {
              id: 'range',
              header: 'Estimate',
              cell: (i) => `${i.low}–${i.high} ${i.unit}`,
            },
          ]}
        />
      </SpaceBetween>
    </Container>
  );
}
