import { badge, card, el, note, pageHead, table } from '../ui.js';
import { STEP_NAME } from '../widgets/findings.js';
import { boot } from './boot.js';

const VERDICT_TONE = { Stands: 'warn', Partly: 'warn', 'Does not stand': 'good' };
const STATE_TONE = { 'Next iteration': 'bad', Disclosed: 'warn', 'Fixed in this record': 'good', 'No action': 'good' };

boot('changes', (main, _data, meta) => {
  main.append(pageHead({ eyebrow: 'CRISP-DM record', title: 'Changes by CRISP-DM step',
    lede: 'Every change to data, training or evaluation, filed under the step it belongs to, with what two outside code reviews found at that step.',
    chips: [`${meta.changes.length} changes`, `${meta.audit.length} review points`, 'no verdict changed'] }));
  const open = meta.audit.filter((a) => a.state === 'Next iteration').length;
  main.append(card('What stays open', note(`${open} review points are left for the next iteration. Fixing them now would change the recorded Stage 4 or Stage 5 code, forcing a retrain or replacing the one recorded evaluation, or would change an analysis the preregistration froze before the test read.`)));
  meta.phases.forEach((phase, i) => {
    const changes = meta.changes.filter((c) => c.step === phase.id);
    const audit = meta.audit.filter((a) => a.step === phase.id);
    if (!changes.length && !audit.length) return;
    main.append(card(`${i + 1}. ${STEP_NAME[phase.id]}`,
      changes.length ? el('div', { style: 'margin-bottom:14px' }, el('h3', { text: 'What changed' }), table(changes, [{ key: 'what', label: 'Change' }, { key: 'before', label: 'Before' }, { key: 'after', label: 'After' }, { key: 'why', label: 'Why' }])) : null,
      audit.length ? el('div', {}, el('h3', { text: 'Outside review' }), table(audit, [{ key: 'claim', label: 'Point raised' }, { label: 'Verdict', render: (a) => badge(VERDICT_TONE[a.verdict], a.verdict) }, { key: 'action', label: 'What was done' }, { label: 'State', render: (a) => badge(STATE_TONE[a.state], a.state) }])) : null,
      el('a', { href: phase.page, text: `Open ${STEP_NAME[phase.id]}` })));
  });
});
