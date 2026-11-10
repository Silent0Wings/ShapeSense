import { post } from '../api.js';
import { finding, otherArmsNote, verdictPicture } from '../plain.js';
import { badge, card, debounce, el, errorBox, fmt, latestOnly, note, pageHead, signed, table } from '../ui.js';
import { boot } from './boot.js';

function numberField(label, value, step, onInput) {
  const input = el('input', { type: 'number', step, value, oninput: onInput, 'aria-label': label });
  return { root: el('label', { style: 'display:grid;gap:3px;font-size:13.5px' }, label, input), get: () => Number(input.value) };
}

boot('business', (main, data, meta) => {
  const c = data.criterion;
  const statusOf = (id) => (meta.iterations.find((it) => it.id === id)?.status === 'closed' ? badge('good', 'Closed') : badge('warn', 'In progress'));
  main.append(pageHead({
    eyebrow: 'CRISP-DM step 1', title: 'Business understanding',
    lede: 'The current question, from iteration 3, is which training mix still works when images are damaged. Iterations 1 and 2 asked earlier questions, both on clean images.',
  }));
  main.append(card('The question in each iteration', table([
    { iteration: 'Iteration 1', status: statusOf(1), question: 'Does synthetic data beat augmentation alone?', test: 'Real + synthetic (B) against Real + augmented (A1)', images: 'Clean' },
    { iteration: 'Iteration 2', status: statusOf(2), question: 'Does the full mix beat real images alone?', test: 'Full mix (A2) against Real only (A0)', images: 'Clean' },
    { iteration: 'Iteration 3 (current)', status: statusOf(3), question: 'Which training mix survives damage?', test: 'Full mix (A2) against Real only (A0)', images: 'Damaged, with clean shown for context' },
  ], [{ key: 'iteration', label: 'Iteration' }, { key: 'status', label: 'Status' }, { key: 'question', label: 'Question' },
    { key: 'test', label: 'Comparison' }, { key: 'images', label: 'Images' }]),
  el('p', { class: 'note' }, 'Their results are on ', el('a', { href: 'iteration1.html', text: 'iteration 1' }), ' and ', el('a', { href: 'iteration2.html', text: 'iteration 2' }), ', and the iteration 3 experiments are on ', el('a', { href: 'experiments.html', text: 'experiments' }), '.')));
  main.append(el('div', { class: 'grid two' },
    card('The arms and what each one tests', table([
      { arm: 'Real only (A0)', data: 'Real images only', role: 'Control' },
      { arm: 'Real + augmented (A1)', data: 'Real images plus class-safe augmentation', role: 'Isolates augmentation' },
      { arm: 'Real + synthetic (B)', data: 'A1 plus synthetic images in every batch', role: 'Iteration 1 test: B against A1' },
      { arm: 'Synthetic pretraining (P)', data: 'Generated shapes first, then real images', role: 'Iteration 3, reported descriptively' },
      { arm: 'Full mix (A2)', data: 'Clean real, augmented real and synthetic images in each batch', role: 'Iteration 2 test: A2 against A0. Iteration 3 primary test on damaged images: A2 against A0' },
    ], [{ key: 'arm', label: 'Arm' }, { key: 'data', label: 'Training data' }, { key: 'role', label: 'Purpose' }])),
    card('The locked success rule', table([
      { rule: 'Macro-F1 gain of A2 over A0 (iterations 2 and 3)', value: `at least ${c.macro_f1_min_gain_points} point` },
      { rule: 'Paired bootstrap confidence level', value: `${c.ci_level * 100}%, interval must exclude 0` },
      { rule: 'Largest allowed class drop', value: `${c.max_class_f1_drop_points} points, or the noise band if wider` },
    ], [{ key: 'rule', label: 'Rule' }, { key: 'value', label: 'Value' }]),
    note('These values were frozen before the first test read and are never edited here.'))));

  if (!data.verdict) { main.append(card('Iteration 3 result', note('Stage 5 has not run yet.'))); return; }
  const v = data.verdict;
  main.append(card('Iteration 3 result: damaged images (current question)', el('div', { class: 'hero' },
    el('span', { class: 'big', text: signed(v.delta) }),
    v.verdict === 'pass' ? badge('pass', 'Criterion met') : badge('fail', 'Criterion not met'),
    el('span', { text: `points of macro-F1 on damaged images, 95% CI [${fmt(v.ci[0])}, ${fmt(v.ci[1])}]` })),
    el('p', { class: 'finding', text: finding(v, { damaged: true }) }), verdictPicture(v, c.macro_f1_min_gain_points),
    v.others?.length ? note(otherArmsNote) : null,
    el('p', { class: 'note', text: v.reasons.join('. ') })));

  const gain = numberField('Minimum gain (points)', c.macro_f1_min_gain_points, 0.1, () => refresh());
  const drop = numberField('Largest allowed class drop (points)', c.max_class_f1_drop_points, 0.1, () => refresh());
  const requireCi = el('input', { type: 'checkbox', checked: true, onchange: () => refresh() });
  const out = el('div', {});
  const send = latestOnly((body) => post('/api/whatif', body));
  const refresh = debounce(async () => {
    try {
      const r = await send({ min_gain: gain.get(), max_class_drop: drop.get(), require_ci: requireCi.checked });
      if (!r) return;
      out.replaceChildren(el('div', { class: 'toolbar' },
        r.verdict === 'pass' ? badge('pass', 'Would pass') : badge('fail', 'Would fail')),
      el('p', { text: r.reasons.length ? r.reasons.join('. ') : 'Every what-if condition is met.' }),
      r.harmful_classes.length ? note(`Harmful classes: ${r.harmful_classes.join(', ')}`) : note('No class would count as harmed.'));
    } catch (error) { out.replaceChildren(errorBox(error)); }
  }, 120);
  main.append(card('Iteration 3: what if the rule had been different?',
    el('div', { class: 'grid two', style: 'margin-bottom:6px' }, gain.root, drop.root),
    el('label', {}, requireCi, ' The confidence interval must exclude 0'),
    out,
    note(`A what-if only. It re-applies the rule to the stored iteration 3 results and changes nothing: the real verdict stays "${v.verdict}". The confidence level is fixed at ${c.ci_level * 100}%, because changing it would need a new computation on test predictions. Per-class drops come from a table rounded to 0.1, so values right at a threshold can differ slightly from the exact rule.`)));
  refresh();
});
