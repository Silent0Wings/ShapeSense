// The CRISP-DM wheel: six clickable steps, the forward loop and the feedback arrows.
import { headline, nameArms } from '../plain.js';
import { el, fmt, signed } from '../ui.js';
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

function curve(a, b, bend) {
  const p = edge(a, b); const q = edge(b, a);
  const mx = (p.x + q.x) / 2; const my = (p.y + q.y) / 2;
  const toCenter = Math.hypot(W / 2 - mx, H / 2 - my) || 1;
  return { p, q, cx: mx + ((mx - W / 2) / toCenter) * bend, cy: my + ((my - H / 2) / toCenter) * bend };
}

function arrow(a, b, bend, cls, markerId) {
  const { p, q, cx, cy } = curve(a, b, bend);
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

function node(phase, at, step, active) {
  const lines = wrap(phase.status_line);
  const group = s('a', { href: phase.page, class: active ? 'node active' : 'node', 'aria-label': `${phase.name}: ${phase.status_line}` },
    s('rect', { x: at.x - NODE_W / 2, y: at.y - NODE_H / 2, width: NODE_W, height: NODE_H, rx: 12 }),
    text(at.x, at.y - 21, `${step}. ${phase.name}`, { class: 'name', 'text-anchor': 'middle' }));
  lines.forEach((line, i) => group.append(text(at.x, at.y + 1 + i * 15, line, { class: 'line', 'text-anchor': 'middle' })));
  return group;
}

const marker = (id, cls) => s('marker', { id, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' },
  s('path', { d: 'M0,0 L10,5 L0,10 z', class: cls, style: cls ? undefined : 'fill:var(--accent)' }));

// `active` highlights one step; `focus` replaces the verdict in the centre.
export function crispCycle({ phases, verdict, active, focus }) {
  const centre = focus ?? { over: verdict ? nameArms(verdict.label) : 'Latest result', big: verdict ? headline(verdict) : 'Pending', under: 'Dashed: feedback arrows, including iteration 1' };
  const at = positions(phases.length);
  const root = s('svg', { class: 'cycle', viewBox: `0 0 ${W} ${H}`, role: 'group', 'aria-label': 'CRISP-DM cycle' },
    s('defs', {}, marker('forward', 'head'), marker('backward', '')));
  phases.forEach((_, i) => root.append(arrow(at[i], at[(i + 1) % phases.length], 26, '', 'forward')));
  root.append(arrow(at[1], at[0], -30, 'back', 'backward'));   // Data informs Business and back
  root.append(arrow(at[3], at[2], -30, 'back', 'backward'));   // iteration 1: Modeling to Data Preparation
  root.append(arrow(at[4], at[2], -44, 'back', 'backward'));   // iteration 2: Evaluation to Data Preparation
  root.append(text(W / 2, H / 2 + 92, 'iteration 2', { class: 'center', 'text-anchor': 'middle' }));
  root.append(text(W / 2, H / 2 - 22, centre.over, { class: 'center', 'text-anchor': 'middle' }));
  root.append(text(W / 2, H / 2 + 12, centre.big, { class: 'center-big', 'text-anchor': 'middle' }));
  root.append(text(W / 2, H / 2 + 34, centre.under, { class: 'center', 'text-anchor': 'middle' }));
  phases.forEach((phase, i) => root.append(node(phase, at[i], i + 1, phase.id === active)));
  const list = el('ol', { class: 'cycle-list' }, phases.map((phase, i) => el('li', {},
    el('a', { href: phase.page, 'aria-current': phase.id === active ? 'step' : null }, `${i + 1}. ${phase.name}`, el('span', { text: phase.status_line })))));
  return el('div', {}, root, list);
}

// What each trip did at each step, short enough for a box. Results come from stored records.
const CAPTIONS = {
  1: { data: 'Most Quick, Draw! diamonds were not rhombi.', prep: 'Removed them by rule and re-froze the split.', model: 'Augmented models rejected those drawings.' },
  2: { business: 'Does this augmentation suit these classes at all?', data: 'Orientation carries class information in some sources.', prep: 'Fixed two transform defects and tuned the ranges.',
    model: 'Added Full mix and tuned every arm.', deploy: 'Exported the new model and served all four arms live.' },
  3: { business: 'From clean accuracy to surviving damage.', data: 'Built a second, never-read holdout.', prep: 'Measured what each transform costs.',
    model: 'Added synthetic pretraining and ran the experiments.', deploy: 'Exported five arms and added the All models vote.' },
};

const resultLine = (r) => `${nameArms(r.label)}: ${signed(r.delta)} points, CI [${fmt(r.ci[0])}, ${fmt(r.ci[1])}].`;

// The cycle one iteration at a time: a slider walks the trips, and a step opens its finding.
export function crispProgress({ phases, iterations, results = {} }) {
  const at = positions(phases.length);
  const last = iterations.length;
  let stop = last; let selected = null;
  const host = el('div', {}); const detail = el('div', { class: 'progress-detail' });
  const choose = (id) => (event) => {
    event.preventDefault();
    selected = selected === id ? null : id;
    draw();
    host.querySelector(`[data-step="${id}"]`)?.focus();
  };
  const caption = (it, id) => {
    if (!it.findings[id]) return 'No finding recorded in this iteration.';
    return (id === 'eval' && results[it.id] ? resultLine(results[it.id]) : CAPTIONS[it.id]?.[id]) ?? it.findings[id];
  };

  function wheel(it, n) {
    const r = results[it.id];
    const root = s('svg', { class: 'cycle', viewBox: `0 0 ${W} ${H}`, role: 'group', 'aria-label': `CRISP-DM cycle, iteration ${it.id}` },
      s('defs', {}, marker('forward', 'head'), marker('backward', '')));
    phases.forEach((_, i) => root.append(arrow(at[i], at[(i + 1) % phases.length], 26, '', 'forward')));
    root.append(arrow(at[1], at[0], -30, 'back past', 'backward'));
    iterations.slice(0, n).forEach((trip, k) => {
      const [from, to] = trip.route.split(' → ').map((name) => phases.findIndex((p) => p.name === name));
      const bend = Math.abs(from - to) === 1 ? -30 : -44;
      root.append(arrow(at[from], at[to], bend, k === n - 1 ? 'back now' : 'back past', 'backward'));
      const { p, q, cx, cy } = curve(at[from], at[to], bend);
      const mx = (p.x + 2 * cx + q.x) / 4; const my = (p.y + 2 * cy + q.y) / 4;
      const toCenter = Math.hypot(W / 2 - mx, H / 2 - my) || 1;
      root.append(text(mx + ((W / 2 - mx) / toCenter) * 16, my + ((H / 2 - my) / toCenter) * 16 + 4, `iteration ${trip.id}`,
        { class: k === n - 1 ? 'center now' : 'center', 'text-anchor': 'middle' }));
    });
    root.append(text(W / 2, H / 2 - 22, `Iteration ${it.id}: ${it.title}`, { class: 'center', 'text-anchor': 'middle' }));
    root.append(text(W / 2, H / 2 + 12, r ? headline(r) : 'No result', { class: 'center-big', 'text-anchor': 'middle' }));
    if (r) root.append(text(W / 2, H / 2 + 34, `${nameArms(r.label)}: ${signed(r.delta)} points`, { class: 'center', 'text-anchor': 'middle' }));
    phases.forEach((phase, i) => {
      const group = node({ ...phase, status_line: caption(it, phase.id) }, at[i], i + 1, false);
      group.setAttribute('data-step', phase.id);
      if (!it.findings[phase.id]) group.classList.add('dim');
      if (phase.id === selected) group.classList.add('selected');
      group.addEventListener('click', choose(phase.id));
      root.append(group);
    });
    return root;
  }

  const slider = el('input', { class: 'progress-slider', type: 'range', min: 1, max: last, step: 1, value: last, 'aria-label': 'Iteration',
    oninput: () => { stop = Number(slider.value); draw(); } });
  const ticks = iterations.map((it, i) => el('button', { class: 'progress-tick', type: 'button', onclick: () => { stop = i + 1; slider.value = stop; draw(); } },
    `Iteration ${it.id}`, results[it.id] ? ` · ${results[it.id].verdict}` : ''));

  function draw() {
    const it = iterations[stop - 1];
    const phase = phases.find((p) => p.id === selected);
    slider.setAttribute('aria-valuetext', `Iteration ${it.id}: ${it.title}`);
    ticks.forEach((tick, i) => tick.classList.toggle('on', i === stop - 1));
    const list = el('ol', { class: 'cycle-list' }, phases.map((p, i) => el('li', {},
      el('a', { href: p.page, 'data-step': p.id, 'aria-current': p.id === selected ? 'step' : null, onclick: choose(p.id) }, `${i + 1}. ${p.name}`, el('span', { text: caption(it, p.id) })))));
    host.replaceChildren(wheel(it, stop), list);
    detail.replaceChildren(
      el('h3', { text: `Iteration ${it.id}: ${it.title}` }),
      el('p', { class: 'note', text: `${it.route}. ${it.trigger}` }),
      ...(phase
        ? [el('p', {}, el('strong', { text: `${phase.name}: ` }), it.findings[phase.id] ?? 'No finding recorded at this step in this iteration.'),
          el('p', {}, el('a', { href: phase.page, text: `Open ${phase.name}` }))]
        : [el('p', {}, el('strong', { text: 'Decision: ' }), it.decision)]));
  }
  draw();
  return el('div', {}, el('div', { class: 'progress-control' }, slider, el('div', { class: 'progress-ticks' }, ticks)), host, detail);
}
