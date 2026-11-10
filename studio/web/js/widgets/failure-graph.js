// Every failure in the order it happened, one lane per CRISP-DM step, so the path shows.
import { hover, s, svgRoot, text } from '../svg/core.js';
import { el } from '../ui.js';
import { STEP_NAME, failureHref } from './findings.js';

const STATES = ['Overcome', 'Partly', 'Still open', 'Verdict stands'];
const COLOR = { Overcome: 'var(--good)', Partly: 'var(--warn)', 'Still open': 'var(--bad)', 'Verdict stands': 'var(--text-muted)' };

function mark(state, x, y, r) {
  const fill = COLOR[state];
  if (state === 'Overcome') return s('circle', { cx: x, cy: y, r, fill });
  if (state === 'Partly') return s('path', { d: `M${x},${y - r - 1} L${x + r + 1},${y} L${x},${y + r + 1} L${x - r - 1},${y} z`, fill });
  if (state === 'Still open') return s('path', { d: `M${x},${y - r - 1} L${x + r + 1},${y + r} L${x - r - 1},${y + r} z`, fill });
  return s('rect', { x: x - r, y: y - r, width: 2 * r, height: 2 * r, rx: 2, fill });
}

export function failureGraph(failures, phases) {
  const before = (f) => f.iteration.startsWith('Before');
  const ordered = [...failures.filter(before), ...failures.filter((f) => !before(f))];
  const lanes = phases.filter((p) => ordered.some((f) => f.step === p.id));
  const left = 156; const col = 27; const gap = 18; const top = 40; const laneH = 46;
  const bottom = top + lanes.length * laneH;
  const bands = [...new Set(ordered.map((f) => f.iteration))];
  const xOf = new Map(); const spans = [];
  let x = left;
  for (const band of bands) {
    const inBand = ordered.filter((f) => f.iteration === band);
    spans.push({ band, from: x, to: x + inBand.length * col });
    inBand.forEach((f, i) => xOf.set(f.id, x + (i + .5) * col));
    x += inBand.length * col + gap;
  }
  const width = x - gap + 14;
  const yOf = (f) => top + lanes.findIndex((p) => p.id === f.step) * laneH + laneH / 2 - 5;
  const root = svgRoot(width, bottom + 6, 'Every failure in order, by CRISP-DM step and how it ended');
  root.style.minWidth = '760px';
  for (const { band, from, to } of spans) {
    root.append(s('rect', { x: from, y: top - 6, width: to - from, height: bottom - top + 10, rx: 6, fill: 'var(--surface-2)' }),
      text((from + to) / 2, 22, band.startsWith('Before') ? 'Before' : band, { 'text-anchor': 'middle', class: 'title' }));
  }
  lanes.forEach((phase, i) => {
    const y = top + i * laneH + laneH / 2 - 5;
    root.append(s('line', { class: 'grid-line', x1: left, x2: width - 14, y1: y, y2: y }),
      text(left - 12, y + 4, STEP_NAME[phase.id], { 'text-anchor': 'end', style: 'font-size:13px;fill:var(--text-primary)' }));
  });
  root.append(s('path', { d: ordered.map((f, i) => `${i ? 'L' : 'M'}${xOf.get(f.id)},${yOf(f)}`).join(''), fill: 'none', stroke: 'var(--text-muted)', 'stroke-width': 1.2, opacity: .55 }));
  for (const f of ordered) {
    const cx = xOf.get(f.id); const cy = yOf(f);
    const link = s('a', { href: failureHref(f.id), 'aria-label': `${f.id}, ${f.state}: ${f.failure}` },
      s('rect', { x: cx - col / 2, y: cy - 14, width: col, height: 40, fill: 'transparent' }), mark(f.state, cx, cy, 7), text(cx, cy + 20, f.id.slice(1).replace(/^0/, ''), { 'text-anchor': 'middle', style: 'font-size:10px' }));
    hover(link, `${f.id} · ${f.state}: ${f.failure}`);
    root.append(link);
  }
  const key = (state) => el('span', { style: 'display:inline-flex;align-items:center;gap:5px;margin-right:14px' },
    s('svg', { width: 18, height: 18, viewBox: '0 0 18 18', 'aria-hidden': 'true' }, mark(state, 9, 9, 6)), state);
  return el('div', {}, el('div', { style: 'font-size:13px;margin-bottom:6px' }, STATES.map(key)), el('div', { style: 'overflow-x:auto' }, root));
}
