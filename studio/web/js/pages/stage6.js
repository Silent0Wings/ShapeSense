import { badge, card, el, fmt, note, pageHead, stat, stats, table } from '../ui.js';
import { boot } from './boot.js';

boot('stage6', (main, d) => {
  main.append(pageHead({ eyebrow: 'Stage 6 · CRISP-DM deployment', title: 'Report and export',
    lede: 'The report is built from stored results only, the best validation model is exported to ONNX, and a shipped bundle runs on its own with no project code.' }));
  main.append(card('Report', el('div', { class: 'toolbar' },
    el('a', { href: '/file/report', target: '_blank', rel: 'noopener', text: 'Open the Phase 2 report' }),
    el('a', { href: '/file/report_phase1', target: '_blank', rel: 'noopener', text: 'Open the Phase 1 report' })),
  stats(stat('Traceability findings', d.metrics.traceability_failing ?? '–', 'hand-typed numbers'), stat('Missing inputs', d.metrics.missing_inputs?.length ?? '–')),
  el('div', { class: 'toolbar' },
    ...Object.entries(d.checks).map(([k, v]) => (v ? badge('good', k.replace(/_/g, ' ')) : badge('bad', k.replace(/_/g, ' ')))))));
  main.append(el('div', { class: 'grid two' },
    card('Exported bundle', d.card ? stats(stat('Run', d.card.run_name), stat('Selected by', 'validation macro-F1', fmt(d.card.val_macro_f1, 2)), stat('Input', d.card.input.shape.slice(1).join(' × ')), stat('Classes', d.labels?.length ?? '–')) : note('No bundle yet. Run: python run_pipeline.py --stages 6'),
      note('The test split never enters the choice. A plain resize is banned in the bundle, because it would not match training.')),
    card('Models available live', table(d.live.map((arm) => ({ arm, run: d.arms[arm]?.run ?? '–', f1: d.arms[arm]?.val_macro_f1 })),
      [{ key: 'arm', label: 'Arm' }, { key: 'run', label: 'Run' }, { label: 'Val macro-F1', num: true, render: (r) => fmt(r.f1, 2) }]),
    note('Single best-validation seeds, for comparing drawings. The verdict used three-seed ensembles.'),
    el('div', { class: 'toolbar' }, el('a', { href: 'live.html', text: 'Open draw and predict' })))));
  main.append(card('How to run it', el('ol', { style: 'margin:0;padding-left:20px' },
    el('li', {}, el('code', { text: 'python run_pipeline.py --stages 6' }), ' builds the report and bundle.'),
    el('li', {}, el('code', { text: 'python -m studio.tools.export_arms' }), ' adds the A1 and B models for comparison.'),
    el('li', {}, el('code', { text: 'python -m studio' }), ' starts this dashboard at 127.0.0.1:8765.'))));
});
