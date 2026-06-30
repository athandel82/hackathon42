import Badge from '@cloudscape-design/components/badge';
import type { Severity } from '../api/types';

const COLOR: Record<Severity, 'red' | 'blue' | 'grey'> = {
  high: 'red',
  medium: 'blue',
  low: 'grey',
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <Badge color={COLOR[severity]}>{severity}</Badge>;
}

/** Numeric rank so lists can be sorted high → low. */
export const severityRank: Record<Severity, number> = {
  high: 3,
  medium: 2,
  low: 1,
};
