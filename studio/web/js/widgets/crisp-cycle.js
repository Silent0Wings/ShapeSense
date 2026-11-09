// The CRISP-DM wheel: six clickable steps, the forward loop and the feedback arrows.
import { el } from '../ui.js';
import { s, text } from '../svg/core.js';

const W = 1040; const H = 660; const NODE_W = 212; const NODE_H = 92;

function positions(n) {
  return Array.from({ length: n }, (_, i) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    return { x: W / 2 + 400 * Math.cos(angle), y: H / 2 + 248 * Math.sin(angle) };
  });
}

// Where the straight line from a node's centre towards `to` leaves its box.
function edge(from, to) {
  const dx = to.x - from.x; const dy = to.y - from.y;
  const k = Math.min((NODE_W / 2 + 6) / Math.abs(dx || 1e-6), (NODE_H / 2 + 6) / Math.abs(dy || 1e-6));
  return { x: from.x + dx * k, y: from.y + dy * k };
}

function arrow(a, b, bend, cls, markerId) {
  const p = edge(a, b); const q = edge(b, a);
  const mx = (p.x + q.x) / 2; const my = (p.y + q.y) / 2;
  const toCenter = Math.hypot(W / 2 - mx, H / 2 - my) || 1;
  const cx = mx + ((mx - W / 2) / toCenter) * bend; const cy = my + ((my - H / 2) / toCenter) * bend;
  return s('path', { class: `arrow ${cls}`, d: `M${p.x},${p.y} Q${cx},${cy} ${q.x},${q.y}`, 'marker-end': `url(#${markerId})` });
}

function wrap(line, width = 31) {
  const out = []; let cur = '';
  for (const word of line.split(' ')) {
    if (`${cur} ${word}`.trim().length > width) { out.push(cur); cur = word; } else cur = `${cur} ${word}`.trim();
  }
  if (cur) out.push(cur);
  return out.slice(0, 3);
}

function node(phase, at, step) {
  const lines = wrap(phase.status_line);
  const group = s('a', { href: phase.page, class: 'node', 'aria-label': `${phase.name}: ${phase.status_line}` },
    s('rect', { x: at.x - NODE_W / 2, y: at.y - NODE_H / 2, width: NODE_W, height: NODE_H, rx: 12 }),
    text(at.x, at.y - 21, `${step}. ${phase.name}`, { class: 'name', 'text-anchor': 'middle' }));
  lines.forEach((line, i) => group.append(text(at.x, at.y + 1 + i * 15, line, { class: 'line', 'text-anchor': 'middle' })));
  return group;
}

const marker = (id, cls) => s('marker', { id, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' },
  s('path', { d: 'M0,0 L10,5 L0,10 z', class: cls, style: cls ? undefined : 'fill:var(--accent)' }));

export function crispCycle({ phases, verdict }) {
  const at = positions(phases.length);
  const root = s('svg', { class: 'cycle', viewBox: `0 0 ${W} ${H}`, role: 'group', 'aria-label': 'CRISP-DM cycle' },
    s('defs', {}, marker('forward', 'head'), marker('backward', '')));
  phases.forEach((_, i) => root.append(arrow(at[i], at[(i + 1) % phases.length], 26, '', 'forward')));
  root.append(arrow(at[1], at[0], -30, 'back', 'backward'));   // Data informs Business and back
  root.append(arrow(at[3], at[2], -30, 'back', 'backward'));   // iteration 1: Modeling to Data Preparation
  root.append(arrow(at[4], at[2], -44, 'back', 'backward'));   // iteration 2: Evaluation to Data Preparation
  root.append(text(W / 2, H / 2 + 92, 'iteration 2', { class: 'center', 'text-anchor': 'middle' }));
  root.append(text(W / 2, H / 2 - 22, `${verdict ? verdict.label : 'Primary'} verdict`, { class: 'center', 'text-anchor': 'middle' }));
  root.append(text(W / 2, H / 2 + 12, verdict ? verdict.verdict.toUpperCase() : 'pending', { class: 'center-big', 'text-anchor': 'middle' }));
  root.append(text(W / 2, H / 2 + 34, 'Dashed: feedback arrows, including iteration 1', { class: 'center', 'text-anchor': 'middle' }));
  phases.forEach((phase, i) => root.append(node(phase, at[i], i + 1)));
  const list = el('ol', { class: 'cycle-list' }, phases.map((phase, i) => el('li', {},
    el('a', { href: phase.page }, `${i + 1}. ${phase.name}`, el('span', { text: phase.status_line })))));
  return el('div', {}, root, list);
}
