// SVG helpers and the single hover tooltip used by every chart.
const NS = 'http://www.w3.org/2000/svg';

export function s(tag, attrs = {}, ...children) {
  const node = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  for (const child of children.flat()) if (child) node.append(child instanceof Node ? child : String(child));
  return node;
}

export const svgRoot = (width, height, label) =>
  s('svg', { class: 'chart', viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': label });

export function text(x, y, value, attrs = {}) { return s('text', { x, y, ...attrs }, String(value)); }

let tipNode;
function tipEl() {
  if (!tipNode) { tipNode = document.createElement('div'); tipNode.className = 'tip'; tipNode.hidden = true; document.body.append(tipNode); }
  return tipNode;
}

export function hover(node, content) {
  const place = (e) => {
    const tip = tipEl();
    tip.hidden = false; tip.innerHTML = '';
    tip.append(typeof content === 'function' ? content() : content);
    const box = tip.getBoundingClientRect();
    tip.style.left = `${Math.min(e.clientX + 14, innerWidth - box.width - 8)}px`;
    tip.style.top = `${Math.max(8, e.clientY - box.height - 12)}px`;
  };
  node.addEventListener('pointermove', place);
  node.addEventListener('pointerleave', () => { tipEl().hidden = true; });
}

export const linear = ([d0, d1], [r0, r1]) => (v) => r0 + ((v - d0) / ((d1 - d0) || 1)) * (r1 - r0);

export function ticks(lo, hi, count = 4) {
  const raw = (hi - lo) / count;
  const mag = 10 ** Math.floor(Math.log10(raw || 1));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((c) => c >= raw) || raw;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-6; v += step) out.push(Number(v.toFixed(6)));
  return out;
}

// One-hue ramp between the theme's low and high steps; `t` is 0..1.
export function seqColor(t) {
  const style = getComputedStyle(document.documentElement);
  const hex = (name) => style.getPropertyValue(name).trim().slice(1).match(/../g).map((h) => parseInt(h, 16));
  const low = hex('--seq-low'); const high = hex('--seq-high');
  return `rgb(${low.map((c, i) => Math.round(c + (high[i] - c) * Math.min(1, Math.max(0, t)))).join(',')})`;
}

export function legend(items) {
  const root = document.createElement('div'); root.className = 'legend';
  for (const { label, color } of items) {
    const span = document.createElement('span');
    const dot = document.createElement('i'); dot.style.background = color;
    span.append(dot, label); root.append(span);
  }
  return root;
}
