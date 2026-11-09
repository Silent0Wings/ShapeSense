// The chart forms the pages use: stacked bars, heatmap, lines, dots, CI whiskers.
import { hover, legend, linear, s, seqColor, svgRoot, text, ticks } from './core.js';

const ink = (t) => (t > 0.55 ? 'var(--seq-ink-high)' : 'var(--text-primary)');

function valueAxis(root, scale, values, top, bottom, format = String) {
  for (const v of values) {
    const x = scale(v);
    root.append(s('line', { class: 'grid-line', x1: x, x2: x, y1: top, y2: bottom }),
      text(x, bottom + 14, format(v), { 'text-anchor': 'middle' }));
  }
}

export function stackedBars({ rows, series, label, valueLabel }) {
  const width = 620; const rowH = 26; const left = 80; const top = 6;
  const bottom = top + rows.length * rowH + 2;
  const max = Math.max(...rows.map((r) => series.reduce((sum, k) => sum + (r.values[k.key] || 0), 0)));
  const scale = linear([0, max], [left, width - 14]);
  const root = svgRoot(width, bottom + 28, label);
  valueAxis(root, scale, ticks(0, max, 5), top, bottom);
  rows.forEach((row, i) => {
    let at = 0; const y = top + i * rowH + 4;
    root.append(text(left - 8, y + 12, row.label, { 'text-anchor': 'end' }));
    for (const item of series) {
      const v = row.values[item.key] || 0;
      if (!v) continue;
      const x0 = scale(at); const x1 = scale(at + v);
      const rect = s('rect', { x: x0, y, width: Math.max(1, x1 - x0 - 2), height: rowH - 9, rx: 3, fill: item.color });
      hover(rect, `${row.label} · ${item.label}: ${v.toLocaleString()} ${valueLabel}`);
      root.append(rect); at += v;
    }
  });
  const wrap = document.createElement('div');
  wrap.append(legend(series), root);
  return wrap;
}

export function heatmap({ cells, xLabels, yLabels, label, cellText, tip, onClick, size = 44, marked, xTitle, yTitle }) {
  const left = 78; const top = 24;
  const width = left + xLabels.length * size + 10; const height = top + yLabels.length * size + 50;
  const root = svgRoot(width, height, label);
  xLabels.forEach((x, i) => root.append(text(left + (i + .5) * size, top - 8, x, { 'text-anchor': 'middle' })));
  yLabels.forEach((y, j) => root.append(text(left - 8, top + (j + .5) * size + 4, y, { 'text-anchor': 'end' })));
  for (const cell of cells) {
    const x = left + cell.x * size; const y = top + cell.y * size;
    const rect = s('rect', { class: `cell${onClick ? ' hit' : ''}${marked?.(cell) ? ' on' : ''}`, x, y, width: size, height: size, rx: 3, fill: seqColor(cell.t) });
    hover(rect, tip(cell));
    if (onClick) { rect.addEventListener('click', () => onClick(cell, rect)); }
    root.append(rect);
    const value = cellText(cell);
    if (value !== '') root.append(text(x + size / 2, y + size / 2 + 4, value, { 'text-anchor': 'middle', fill: ink(cell.t), style: `fill:${ink(cell.t)};pointer-events:none` }));
  }
  if (xTitle) root.append(text(left + xLabels.length * size / 2, height - 12, xTitle, { 'text-anchor': 'middle' }));
  if (yTitle) root.append(text(12, top + yLabels.length * size / 2, yTitle, { 'text-anchor': 'middle', transform: `rotate(-90 12 ${top + yLabels.length * size / 2})` }));
  return root;
}

export function lines({ series, xs, label, yLabel, marker, xLabels, xTitle = 'epoch' }) {
  const width = 560; const height = 220; const left = 42; const right = 12; const top = 10; const bottom = 186;
  const all = series.flatMap((d) => d.values);
  const lo = Math.min(...all); const hi = Math.max(...all);
  const pad = (hi - lo || 1) * .08;
  const x = linear([xs[0], xs[xs.length - 1]], [left, width - right]);
  const y = linear([lo - pad, hi + pad], [bottom, top]);
  const root = svgRoot(width, height, label);
  for (const v of ticks(lo - pad, hi + pad, 4)) {
    root.append(s('line', { class: 'grid-line', x1: left, x2: width - right, y1: y(v), y2: y(v) }),
      text(left - 6, y(v) + 4, v, { 'text-anchor': 'end' }));
  }
  if (xLabels) xs.forEach((v, i) => root.append(text(x(v), bottom + 15, xLabels[i], { 'text-anchor': 'middle', style: 'font-size:10.5px' })));
  else for (const v of ticks(xs[0], xs[xs.length - 1], 6)) root.append(text(x(v), bottom + 15, v, { 'text-anchor': 'middle' }));
  root.append(text((left + width - right) / 2, height - 4, xTitle, { 'text-anchor': 'middle' }));
  root.append(text(12, (top + bottom) / 2, yLabel, { 'text-anchor': 'middle', transform: `rotate(-90 12 ${(top + bottom) / 2})` }));
  for (const d of series) {
    root.append(s('path', { d: d.values.map((v, i) => `${i ? 'L' : 'M'}${x(xs[i])},${y(v)}`).join(''), fill: 'none', stroke: d.color, 'stroke-width': 2 }));
  }
  if (marker !== undefined) {
    const i = xs.indexOf(marker);
    root.append(s('line', { class: 'axis-line', x1: x(marker), x2: x(marker), y1: top, y2: bottom }));
    for (const d of series) root.append(s('circle', { cx: x(marker), cy: y(d.values[i]), r: 4.5, fill: d.color, stroke: 'var(--surface-1)', 'stroke-width': 2 }));
  }
  if (marker !== undefined) {
    const band = s('rect', { x: left, y: top, width: width - left - right, height: bottom - top, fill: 'transparent' });
    hover(band, () => document.createTextNode(series.map((d) => `${d.label}: ${d.values[xs.indexOf(marker)].toFixed(3)}`).join('  ·  ')));
    root.append(band);
  }
  if (xLabels) {
    for (const d of series) {
      d.values.forEach((v, i) => {
        const dot = s('circle', { cx: x(xs[i]), cy: y(v), r: 4, fill: d.color, stroke: 'var(--surface-1)', 'stroke-width': 1.5 });
        hover(dot, `${d.label}, ${xLabels[i]}: ${v.toFixed(1)}`);
        root.append(dot);
      });
    }
  }
  const wrap = document.createElement('div');
  if (series.length > 1) wrap.append(legend(series));
  wrap.append(root);
  return wrap;
}

export function dots({ rows, series, label, domain }) {
  const width = 620; const rowH = 26; const left = 90; const top = 6;
  const bottom = top + rows.length * rowH;
  const lo = domain[0]; const hi = domain[1];
  const scale = linear([lo, hi], [left, width - 16]);
  const root = svgRoot(width, bottom + 28, label);
  valueAxis(root, scale, ticks(lo, hi, 6), top, bottom);
  rows.forEach((row, i) => {
    const y = top + i * rowH + rowH / 2;
    root.append(text(left - 8, y + 4, row.label, { 'text-anchor': 'end' }));
    for (const item of series) {
      const dot = s('circle', { cx: scale(row.values[item.key]), cy: y, r: 6, fill: item.color, stroke: 'var(--surface-1)', 'stroke-width': 2 });
      hover(dot, `${row.label} · ${item.label}: ${row.values[item.key].toFixed(1)}`);
      root.append(dot);
    }
  });
  const wrap = document.createElement('div');
  wrap.append(legend(series), root);
  return wrap;
}

// One row per item: dots joined by a range bar, with each exact value in its own column.
export function scoreRows({ rows, series, label, domain }) {
  const width = 780; const rowH = 38; const left = 104; const plotEnd = 556; const top = 30;
  const columns = series.map((_, i) => 610 + i * (series.length > 3 ? 54 : 64));
  const bottom = top + rows.length * rowH;
  const scale = linear(domain, [left, plotEnd]);
  const root = svgRoot(width, bottom + 34, label);
  valueAxis(root, scale, ticks(domain[0], domain[1], 5), top, bottom);
  series.forEach((item, i) => {
    root.append(s('circle', { cx: columns[i] - 22, cy: 13, r: 5, fill: item.color }),
      text(columns[i], 18, item.key, { 'text-anchor': 'end', class: 'title' }));
  });
  rows.forEach((row, i) => {
    const y = top + i * rowH + rowH / 2;
    const values = series.map((item) => row.values[item.key]);
    const best = Math.max(...values);
    if (i) root.append(s('line', { class: 'grid-line', x1: 0, x2: width, y1: y - rowH / 2, y2: y - rowH / 2 }));
    root.append(text(left - 12, y + 5, row.label, { 'text-anchor': 'end', style: 'font-size:14px;fill:var(--text-primary)' }));
    root.append(s('line', { x1: scale(Math.min(...values)), x2: scale(best), y1: y, y2: y, stroke: 'var(--text-muted)', 'stroke-width': 3, 'stroke-linecap': 'round' }));
    series.forEach((item, k) => {
      root.append(s('circle', { cx: scale(values[k]), cy: y, r: 7.5, fill: item.color, stroke: 'var(--surface-1)', 'stroke-width': 2 }));
      const isBest = values[k] === best;
      root.append(text(columns[k], y + 5, values[k].toFixed(1), { 'text-anchor': 'end',
        style: `font-size:14px;font-variant-numeric:tabular-nums;${isBest ? 'font-weight:700;fill:var(--text-primary)' : ''}` }));
    });
    const band = s('rect', { x: 0, y: y - rowH / 2, width, height: rowH, fill: 'transparent' });
    hover(band, `${row.label}: ${series.map((item, k) => `${item.key} ${values[k].toFixed(1)}`).join(', ')}`);
    root.append(band);
  });
  const wrap = document.createElement('div');
  wrap.append(legend(series), root);
  return wrap;
}

// Effect estimates with confidence intervals, a zero line and a required-gain line.
export function ciChart({ rows, label, required }) {
  const width = 620; const rowH = 44; const left = 112; const top = 18;
  const bottom = top + rows.length * rowH;
  const all = rows.flatMap((r) => r.ci).concat([0, required ?? 0]);
  const lo = Math.min(...all) - .5; const hi = Math.max(...all) + .5;
  const scale = linear([lo, hi], [left, width - 16]);
  const root = svgRoot(width, bottom + 28, label);
  valueAxis(root, scale, ticks(lo, hi, 7), top, bottom, (v) => (v > 0 ? `+${v}` : v));
  root.append(s('line', { class: 'axis-line', x1: scale(0), x2: scale(0), y1: top - 4, y2: bottom }));
  root.append(text(scale(0), top - 7, '0', { 'text-anchor': 'middle' }));
  if (required !== undefined) {
    root.append(s('line', { x1: scale(required), x2: scale(required), y1: top - 4, y2: bottom, stroke: 'var(--text-muted)', 'stroke-dasharray': '4 4' }));
    root.append(text(scale(required), top - 7, `required +${required}`, { 'text-anchor': 'middle' }));
  }
  rows.forEach((row, i) => {
    const y = top + i * rowH + rowH / 2;
    root.append(text(left - 8, y + 4, row.label, { 'text-anchor': 'end' }));
    const whisk = s('line', { x1: scale(row.ci[0]), x2: scale(row.ci[1]), y1: y, y2: y, stroke: 'var(--series-1)', 'stroke-width': 2 });
    const dot = s('circle', { cx: scale(row.delta), cy: y, r: 6.5, fill: 'var(--series-1)', stroke: 'var(--surface-1)', 'stroke-width': 2 });
    const tip = `${row.label}: ${row.delta.toFixed(2)} points, CI [${row.ci[0].toFixed(2)}, ${row.ci[1].toFixed(2)}]`;
    hover(whisk, tip); hover(dot, tip);
    root.append(whisk, dot, text(scale(row.delta), y - 11, row.delta.toFixed(2), { 'text-anchor': 'middle' }));
  });
  return root;
}

// Labelled values. Bars start at zero; with a `domain` the values sit too close for
// bars to show, so each is a dot on its own line and length carries no meaning.
export function valueBars({ rows, label, unit = '', domain }) {
  const width = 680; const rowH = 36; const left = 250; const right = 590; const top = 6;
  const span = domain ?? [0, Math.max(...rows.map((r) => r.value))];
  const scale = linear(span, [left, right]);
  const bottom = top + rows.length * rowH;
  const root = svgRoot(width, bottom + (domain ? 24 : 6), label);
  if (domain) valueAxis(root, scale, ticks(span[0], span[1], 5), top, bottom);
  rows.forEach((row, i) => {
    const y = top + i * rowH + rowH / 2;
    const fill = row.mark ? 'var(--accent)' : 'var(--text-muted)';
    root.append(text(left - 12, y + 5, row.label, { 'text-anchor': 'end', style: 'font-size:13.5px;fill:var(--text-primary)' }));
    if (domain) root.append(s('circle', { cx: scale(row.value), cy: y, r: 8, fill }));
    else root.append(s('rect', { x: left, y: y - 8, width: Math.max(scale(row.value) - left, 2), height: 16, rx: 4, fill }));
    root.append(text(width - 4, y + 5, `${row.value}${unit}`, { 'text-anchor': 'end', style: 'font-size:14px;font-variant-numeric:tabular-nums;fill:var(--text-primary)' }));
    const band = s('rect', { x: 0, y: y - rowH / 2, width, height: rowH, fill: 'transparent' });
    hover(band, `${row.label}: ${row.value}${unit}`);
    root.append(band);
  });
  return root;
}
