import { badge, card, el, note, pageHead, stat, stats, table } from '../ui.js';
import { select } from '../widgets/controls.js';
import { boot } from './boot.js';

const STATE = {
  match: () => badge('pass', 'Matches'),
  changed: () => badge('fail', 'Changed'),
  recorded: () => badge('info', 'Recorded only'),
};

boot('stage0', (main, d) => {
  main.append(pageHead({
    eyebrow: 'Stage 0 · foundations for every CRISP-DM step', title: 'Infrastructure',
    lede: 'Rules that keep the experiment honest: a test split only one stage can read, import boundaries, and a cache that reruns a stage only when one of its inputs changed.',
    chips: ['run_pipeline.py', 'status.json per stage', 'import contracts'],
  }));
  main.append(card('Status of each stage', el('div', { class: 'lights' }, d.lights.map((l) => el('a', { class: 'light', href: l.page },
    `${l.stage} · ${l.title}`, l.status === 'passed' ? badge('pass', 'Passed') : badge('fail', l.status))))));
  main.append(el('div', { class: 'grid two' },
    card('Guards', stats(
      stat('Import boundaries', d.guards?.import_linter ? 'Passing' : 'Failing'),
      stat('Contract tests', d.guards?.contract_tests ? 'Passing' : 'Failing'),
      stat('Test-split reads', d.access.total, Object.keys(d.access.callers).join(', ') || 'none'))),
    card('Code migration check', stats(
      stat('Rebuild equals original', d.migration?.equal ? 'Yes' : 'No'),
      stat('Items compared', d.migration?.compared?.length ?? '–'),
      stat('Differences', Object.keys(d.migration?.differences ?? {}).length)),
    note('Phase 1 scripts moved into src/ and rebuilt the dataset, then had to reproduce it exactly.'))));

  let stage = 'all'; let state = 'all';
  // A stage opens by default when it has a changed row; the reader's own open and close choices are kept across filters.
  const openStages = new Set(d.hashes.filter((r) => r.state === 'changed').map((r) => r.stage));
  const holder = el('div', {});
  const draw = () => {
    const rows = d.hashes.filter((r) => (stage === 'all' || String(r.stage) === stage) && (state === 'all' || r.state === state));
    const groups = [...new Set(rows.map((r) => r.stage))].sort((a, b) => a - b).map((n) => {
      const group = rows.filter((r) => r.stage === n);
      const count = (key) => group.filter((r) => r.state === key).length;
      const details = el('details', { class: 'stage-group', open: openStages.has(n) },
        el('summary', {}, el('strong', { text: `Stage ${n}` }), el('span', { class: 'note', text: `${group.length} rows` }),
          badge('pass', `${count('match')} match`), badge(count('changed') ? 'fail' : 'info', `${count('changed')} changed`), badge('info', `${count('recorded')} recorded only`)),
        table(group, [
          { label: 'Input', key: 'input' },
          { label: 'Recorded hash', render: (r) => el('span', { class: 'mono', text: r.recorded }) },
          { label: 'Now', render: (r) => STATE[r.state]() },
        ]));
      details.addEventListener('toggle', () => { if (details.open) openStages.add(n); else openStages.delete(n); });
      return details;
    });
    holder.replaceChildren(...(groups.length ? groups : [note('No rows match these filters.')]));
  };
  const counts = { match: 0, changed: 0, recorded: 0 };
  d.hashes.forEach((r) => { counts[r.state] += 1; });
  draw();
  main.append(card('Hash cache explorer',
    stats(stat('Match on disk', counts.match), stat('Changed', counts.changed), stat('Recorded only', counts.recorded)),
    el('div', { class: 'toolbar' },
      select([{ value: 'all', label: 'All stages' }, ...[0, 1, 2, 3, 4, 5, 6].map((n) => ({ value: String(n), label: `Stage ${n}` }))], 'all', (v) => { stage = v; draw(); }, 'Stage'),
      select([{ value: 'all', label: 'Any state' }, { value: 'match', label: 'Matches' }, { value: 'changed', label: 'Changed' }, { value: 'recorded', label: 'Recorded only' }], 'all', (v) => { state = v; draw(); }, 'State')),
    holder,
    note('Only code, config and the train and val manifests are recomputed. The other inputs, which include the test manifest and whole image folders, are shown as recorded and are not reopened.')));
});
