// Plain-language wording for new readers. Every number comes from stored results.
import { ciChart } from './svg/charts.js';
import { fmt } from './ui.js';

export const ARM_NAMES = { A0: 'Real only', A1: 'Real + augmented', B: 'Real + synthetic', A2: 'Full mix', P: 'Synthetic pretraining' };

export const armName = (key) => ARM_NAMES[key] ?? key;

// For comparison labels such as "A2 vs A0".
export const nameArms = (label) => String(label).replace(/\b(A0|A1|A2|B|P)\b/g, (key) => ARM_NAMES[key]);

const spansZero = (ci) => ci[0] <= 0 && ci[1] >= 0;

export function headline(verdict) {
  if (verdict.verdict === 'pass') return 'Clear gain';
  return spansZero(verdict.ci) ? 'No clear gain' : 'Target not met';
}

export function finding(verdict) {
  const [candidate, reference] = String(verdict.label).split(' vs ');
  const direction = verdict.delta >= 0 ? 'higher' : 'lower';
  const uncertainty = spansZero(verdict.ci) ? ' The uncertainty range includes no difference at all.' : '';
  const rule = verdict.verdict === 'pass' ? ' It met the success rule set in advance.' : ' It did not meet the success rule set in advance.';
  return `${armName(candidate)} scored ${fmt(Math.abs(verdict.delta))} points ${direction} than ${armName(reference)}.${uncertainty}${rule}`;
}

export function verdictPicture(verdict, required) {
  return ciChart({ label: `${nameArms(verdict.label)}: result, uncertainty range and target`, required,
    rows: [{ label: 'Result', delta: verdict.delta, ci: verdict.ci }] });
}
