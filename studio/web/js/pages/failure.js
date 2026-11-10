import { badge, card, el, note, pageHead } from '../ui.js';
import { crispCycle } from '../widgets/crisp-cycle.js';
import { failureVisual } from '../widgets/failure-visuals.js';
import { failureHref, stageLinks, STATE_TONE, STEP_NAME } from '../widgets/findings.js';
import { boot } from './boot.js';

const line = (label, value) => el('p', {}, el('strong', { text: `${label}: ` }), value);

boot('failure', (main, _data, meta) => {
  const id = new URLSearchParams(location.search).get('id');
  const at = meta.failures.findIndex((f) => f.id === id);
  if (at < 0) {
    main.append(pageHead({ eyebrow: 'CRISP-DM record', title: 'Failure not found', lede: 'There is no failure with that number.' }),
      card('Failure timeline', el('a', { href: 'failures.html', text: 'Go to the failure timeline' })));
    return;
  }
  const f = meta.failures[at];
  const stepNumber = meta.phases.findIndex((p) => p.id === f.step) + 1;
  const phase = meta.phases[stepNumber - 1];
  document.title = `${f.id} · ShapeSense Studio`;
  main.append(pageHead({ eyebrow: `Failure ${at + 1} of ${meta.failures.length} · ${f.group}`, title: f.failure, lede: f.cause, chips: [f.iteration, STEP_NAME[f.step]] }));
  main.append(el('div', { class: 'toolbar' }, badge(STATE_TONE[f.state], f.state)));
  main.append(card('What it looks like', ...failureVisual(f.visual, meta, f.iteration)));
  main.append(el('div', { class: 'grid two' },
    card('Why it happened', el('p', { text: f.cause })),
    card('How it was handled', el('p', { text: f.handled }), note(f.state === 'Still open' ? 'This one is not solved.' : `State: ${f.state}.`))));
  main.append(card('Where this sits in the CRISP-DM cycle',
    crispCycle({ phases: meta.phases, active: f.step, focus: { over: 'This failure belongs to', big: `Step ${stepNumber}`, under: phase.name } }),
    line('CRISP-DM step', el('a', { href: phase.page, text: `${stepNumber}. ${phase.name}` })),
    line(f.pipeline_stages.length > 1 ? 'Pipeline stages' : 'Pipeline stage', stageLinks(f.pipeline_stages))));
  const before = meta.failures[at - 1]; const after = meta.failures[at + 1];
  main.append(el('div', { class: 'toolbar' },
    before ? el('a', { href: failureHref(before.id), text: `Previous: ${before.id}` }) : null,
    el('a', { href: 'failures.html', text: 'All failures' }),
    after ? el('a', { href: failureHref(after.id), text: `Next: ${after.id}` }) : null));
});
