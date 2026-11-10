// The same short explanation at the top of every pipeline stage, and links along the pipeline.
import { badge, el } from '../ui.js';

const STAGES = ['Infrastructure', 'Data freeze', 'Augmentation', 'Synthetic generator', 'Training', 'Evaluation', 'Report and export'];

// Pages write their phrases freely; every stage shows them the same way: capitalised, no closing full stop.
const tidy = (text) => { const t = String(text ?? '').trim().replace(/\.$/, ''); return t ? t[0].toUpperCase() + t.slice(1) : t; };
const step = (label, body) => el('div', { class: 'brief-step' }, el('span', { text: label }), el('strong', { text: tidy(body) }));
const checkBadge = (ok) => (ok === true ? badge('good', 'Passed') : ok === false ? badge('bad', 'Failed') : badge('info', 'Recorded'));

// `checks` are { label, ok } read from stored results: ok true, false, or null when there is nothing to pass or fail.
export function stageBrief({ job, input, process, output, finding, checks = [] }) {
  return el('section', { class: 'card stage-brief', 'aria-label': 'What this stage does' },
    el('p', { class: 'brief-job', text: job }),
    el('div', { class: 'brief-flow' }, step('Goes in', input), el('span', { class: 'brief-arrow', 'aria-hidden': 'true', text: '→' }),
      step('What it does', process), el('span', { class: 'brief-arrow', 'aria-hidden': 'true', text: '→' }), step('Comes out', output)),
    el('div', { class: 'brief-notes' },
      el('div', {}, el('h3', { text: 'Key finding' }), el('p', {}, finding)),
      el('div', {}, el('h3', { text: 'How we know it worked' }),
        el('ul', { class: 'brief-checks' }, checks.map((c) => el('li', {}, checkBadge(c.ok), ' ', tidy(c.label)))))));
}

export function stageNav(stage) {
  const link = (n, prefix) => el('a', { href: `stage${n}.html` }, `${prefix}: ${n} · ${STAGES[n]}`);
  const onward = stage === STAGES.length - 1 ? el('a', { href: 'live.html', text: 'Next: Draw and predict' }) : link(stage + 1, 'Next');
  return el('nav', { class: 'stage-nav', 'aria-label': 'Pipeline stages' }, stage > 0 ? link(stage - 1, 'Previous') : el('span', {}), onward);
}
