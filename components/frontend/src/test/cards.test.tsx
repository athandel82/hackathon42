import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import analyzeFixture from '../mocks/fixtures/analyze.json';
import type { ResultEnvelope } from '../api/types';
import { WhatBreaksCard } from '../cards/WhatBreaks';
import { WhatItCostsCard } from '../cards/WhatItCosts';
import { WhatItRisksCard } from '../cards/WhatItRisks';

const fixture = analyzeFixture as unknown as ResultEnvelope;

describe('WhatBreaksCard', () => {
  it('renders the summary and every impacted element from the fixture', () => {
    render(<WhatBreaksCard data={fixture.what_breaks} />);
    expect(screen.getByText('What Breaks')).toBeInTheDocument();
    // Sample case: DoorControl + EDC + the 4 CombinedStatus chains.
    expect(screen.getByText('DoorControl')).toBeInTheDocument();
    expect(screen.getByText('EDC')).toBeInTheDocument();
    expect(screen.getByText('CombinedStatusLockedLeftIPdu')).toBeInTheDocument();
    expect(screen.getByText('CombinedStatusOpenLeftIPdu')).toBeInTheDocument();
    expect(screen.getByText('CombinedStatusLockedRightIPdu')).toBeInTheDocument();
    expect(screen.getByText('CombinedStatusOpenRightIPdu')).toBeInTheDocument();
  });

  it('shows an empty state when there are no impacted elements (missing section)', () => {
    render(<WhatBreaksCard data={undefined} />);
    expect(screen.getByText('No impacted elements.')).toBeInTheDocument();
  });
});

describe('WhatItCostsCard', () => {
  it('renders ranges, net assessment and line items', () => {
    render(<WhatItCostsCard data={fixture.what_it_costs} />);
    expect(screen.getByText('What it Costs')).toBeInTheDocument();
    expect(screen.getByText('favorable')).toBeInTheDocument();
    expect(screen.getByText(/USD 12–22/)).toBeInTheDocument();
    expect(screen.getByText(/80–200 engineer-hours/)).toBeInTheDocument();
    expect(screen.getByText('Re-map CombinedStatus signals')).toBeInTheDocument();
  });

  it('shows an empty state when the cost section is missing', () => {
    render(<WhatItCostsCard data={undefined} />);
    expect(screen.getByText('No cost estimate available.')).toBeInTheDocument();
  });
});

describe('WhatItRisksCard', () => {
  it('renders risk items sorted by severity (high first)', () => {
    render(<WhatItRisksCard data={fixture.what_it_risks} />);
    expect(screen.getByText('What it Risks')).toBeInTheDocument();

    const titles = screen
      .getAllByText(/Body CAN loses 4 CombinedStatus signals|Door-ajar \/ lock indication unavailable|Stale DTCs for removed door module/)
      .map((el) => el.textContent);
    expect(titles[0]).toContain('Body CAN loses 4 CombinedStatus signals'); // high first

    // revalidation flag rendered for items that require it
    expect(screen.getAllByText('revalidation required').length).toBeGreaterThan(0);
  });

  it('shows an empty state when there are no risks', () => {
    render(<WhatItRisksCard data={{ items: [] }} />);
    expect(screen.getByText('No risks identified.')).toBeInTheDocument();
  });
});

describe('fixture integrity', () => {
  it('has all six top-level ResultEnvelope fields (parent §7)', () => {
    for (const key of [
      'change_request',
      'target_nodes',
      'what_breaks',
      'what_it_costs',
      'what_it_risks',
      'confidence',
    ]) {
      expect(fixture).toHaveProperty(key);
    }
  });

  it('matches the documented remove-Door blast radius', () => {
    const ids = fixture.what_breaks.impacted.map((i) => i.id);
    expect(ids).toContain('DoorControl');
    expect(ids).toContain('EDC');
    const chains = ids.filter((id) => id.startsWith('CombinedStatus'));
    expect(chains).toHaveLength(4);
  });
});
