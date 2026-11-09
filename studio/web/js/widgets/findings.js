// The CRISP-DM record: what each trip round the cycle found, step by step.
import { badge, card, el, table } from '../ui.js';

export const STEP_NAME = { business: 'Business Understanding', data: 'Data Understanding', prep: 'Data Preparation',
  model: 'Modeling', eval: 'Evaluation', deploy: 'Deployment' };
const PAGE_STEPS = { business: ['business'], stage1: ['data', 'prep'], stage2: ['prep'], stage3: ['prep'],
  stage4: ['model'], stage5: ['eval'], stage6: ['deploy'], live: ['deploy'] };

const statusBadge = (it) => (it.status === 'closed' ? badge('good', 'Closed') : badge('warn', 'In progress'));

export function iterationLog(iterations = []) {
  return card('What each trip round the cycle found', iterations.map((it) => el('div', { style: 'margin-bottom:18px' },
    el('h3', {}, `Iteration ${it.id}: ${it.title} `, statusBadge(it)),
    el('p', { class: 'note', text: `${it.route}. ${it.trigger}` }),
    table(Object.entries(it.findings).map(([step, finding]) => ({ step: STEP_NAME[step], finding })),
      [{ key: 'step', label: 'Step' }, { key: 'finding', label: 'Finding' }]),
    el('p', { style: 'margin-top:8px' }, el('strong', { text: 'Decision: ' }), it.decision))));
}

export const STATE_TONE = { Overcome: 'good', Partly: 'warn', 'Still open': 'bad', 'Verdict stands': 'warn' };

const STAGE_TITLE = ['Infrastructure', 'Data freeze', 'Augmentation', 'Synthetic generator', 'Training', 'Evaluation', 'Report and export'];

// Links to the pipeline stages a failure belongs to.
export function stageLinks(stages) {
  return el('span', {}, stages.flatMap((n, i) => [i ? ', ' : '', el('a', { href: `stage${n}.html`, text: `${n} · ${STAGE_TITLE[n]}` })]));
}

export const failureHref = (id) => `failure.html?id=${id}`;

// Every failure in the order it happened, each row opening its own page.
export function failureLog(failures = [], phases = []) {
  const phaseOf = (f) => phases.find((p) => p.id === f.step);
  const groups = [...new Set(failures.map((f) => f.group))];
  return card('Failures and how we handled them', groups.map((group) => el('div', { style: 'margin-bottom:18px' },
    el('h3', { text: group }),
    table(failures.filter((f) => f.group === group), [
      { key: 'id', label: 'No.' },
      { label: 'What failed', render: (f) => el('a', { href: failureHref(f.id), text: f.failure }) },
      { label: 'CRISP-DM step', render: (f) => el('a', { href: phaseOf(f).page, text: STEP_NAME[f.step] }) },
      { label: 'Pipeline stage', render: (f) => stageLinks(f.pipeline_stages) },
      { label: 'State', render: (f) => badge(STATE_TONE[f.state], f.state) }]))));
}

// The findings recorded for the step or steps this page belongs to.
export function pageFindings(page, iterations = []) {
  const steps = PAGE_STEPS[page];
  if (!steps) return null;
  const rows = iterations.flatMap((it) => steps.filter((step) => it.findings[step]).map((step) => ({ it, step })));
  if (!rows.length) return null;
  return card('Findings recorded at this step', table(rows, [
    { label: 'Iteration', render: ({ it }) => el('span', {}, `${it.id} `, statusBadge(it)) },
    { label: 'Step', render: ({ step }) => STEP_NAME[step] },
    { label: 'Finding', render: ({ it, step }) => it.findings[step] }]));
}
