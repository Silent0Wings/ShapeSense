// Directed lines from one source element to every tile that came from it.
import { s } from '../svg/core.js';

export function fanLines() {
  const lines = s('g', {});
  const root = s('svg', { class: 'fan-lines', 'aria-hidden': 'true' },
    s('defs', {}, s('marker', { id: 'fan-head', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto' },
      s('path', { d: 'M0,0 L10,5 L0,10 z', fill: 'var(--accent)' }))), lines);
  let source = null; let tiles = []; let observed = false;

  function paint() {
    const host = root.parentElement;
    if (!host || !source || !tiles.length) { lines.replaceChildren(); return; }
    if (!observed) { new ResizeObserver(paint).observe(host); observed = true; }
    const box = host.getBoundingClientRect();
    root.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
    const from = source.getBoundingClientRect();
    const rects = tiles.map((tile) => tile.getBoundingClientRect());
    if (Math.min(...rects.map((r) => r.left)) < from.right) { lines.replaceChildren(); return; }   // stacked on a phone
    const x0 = from.right - box.left; const y0 = from.top + from.height / 2 - box.top;
    const trunk = x0 + 30;
    const tops = [...new Set(rects.map((r) => Math.round(r.top)))].sort((a, b) => a - b);
    const buses = tops.map((top) => top - 16 - box.top);
    const path = (d, extra = {}) => s('path', { d, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 1.6, ...extra });
    const parts = [path(`M${x0},${y0} H${trunk}`), path(`M${trunk},${Math.min(y0, ...buses)} V${Math.max(y0, ...buses)}`)];
    tops.forEach((top, row) => {
      const inRow = rects.filter((r) => Math.round(r.top) === top);
      const end = Math.max(...inRow.map((r) => r.left + r.width / 2)) - box.left;
      parts.push(path(`M${trunk},${buses[row]} H${end}`));
      inRow.forEach((r) => parts.push(path(`M${r.left + r.width / 2 - box.left},${buses[row]} V${r.top - box.top - 2}`, { 'marker-end': 'url(#fan-head)' })));
    });
    lines.replaceChildren(...parts);
  }

  return { root, draw(sourceEl, tileEls) { source = sourceEl; tiles = tileEls; paint(); } };
}
