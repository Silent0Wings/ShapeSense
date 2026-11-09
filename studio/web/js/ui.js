// Small DOM helpers shared by every page. No model logic lives here.

export function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === 'class') node.className = value;
    else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (key === 'text') node.textContent = value;
    else node.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

export const fmt = (value, digits = 2) =>
  (value === null || value === undefined || Number.isNaN(Number(value))) ? '–' : Number(value).toFixed(digits);

export const signed = (value, digits = 2) => `${value > 0 ? '+' : ''}${fmt(value, digits)}`;

export function pixImg(b64, { alt = '', size = 96, tip } = {}) {
  return el('img', { class: 'pix', src: `data:image/png;base64,${b64}`, alt, width: size, height: size, 'data-tip': tip });
}

export function card(title, ...children) {
  return el('section', { class: 'card' }, title ? el('h2', { text: title }) : null, ...children);
}

export function note(text) { return el('p', { class: 'note', text }); }

export function stat(label, value, sub) {
  return el('div', { class: 'stat' }, el('span', { class: 'stat-label', text: label }),
    el('span', { class: 'stat-value', text: value }), sub ? el('span', { class: 'stat-sub', text: sub }) : null);
}

export function stats(...tiles) { return el('div', { class: 'stats' }, tiles); }

export function badge(state, text) {
  const icons = { pass: '✓', good: '✓', fail: '✕', bad: '✕', warn: '!', info: 'i' };
  return el('span', { class: `badge badge-${state}` },
    el('span', { 'aria-hidden': 'true', text: icons[state] || 'i' }), text);
}

export function table(rows, columns) {
  const head = el('tr', {}, columns.map((c) => el('th', { class: c.num ? 'num' : '', text: c.label })));
  const body = rows.map((row) => el('tr', {}, columns.map((c) => {
    const value = c.render ? c.render(row) : row[c.key];
    return el('td', { class: c.num ? 'num' : '' }, value instanceof Node ? value : String(value ?? '–'));
  })));
  return el('div', { class: 'table-wrap' }, el('table', {}, el('thead', {}, head), el('tbody', {}, body)));
}

// A chart's accessible alternative: a folded table under the figure.
export function tableView(rows, columns, label = 'Show the data as a table') {
  return el('details', { class: 'table-view' }, el('summary', { text: label }), table(rows, columns));
}

export function pageHead({ eyebrow, title, lede, chips = [] }) {
  return el('header', { class: 'page-head' },
    el('p', { class: 'eyebrow', text: eyebrow }), el('h1', { text: title }),
    el('p', { class: 'lede', text: lede }),
    chips.length ? el('div', { class: 'chips' }, chips.map((c) => el('span', { class: 'chip', text: c }))) : null);
}

export function debounce(fn, ms = 150) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// Runs now if idle; otherwise once more when the running call ends, with the newest
// state. Previews keep updating during a drag and requests can never pile up.
export function singleFlight(task) {
  let running = false; let again = false;
  return async function pump() {
    if (running) { again = true; return; }
    running = true;
    try { do { again = false; await task(); } while (again); } finally { running = false; }
  };
}

// Keep only the newest of overlapping async calls.
export function latestOnly(fn) {
  let current = 0;
  return async (...args) => {
    const id = ++current;
    const result = await fn(...args);
    return id === current ? result : undefined;
  };
}

export function errorBox(error) {
  return el('div', { class: 'error', role: 'alert' }, el('strong', { text: 'Could not load this. ' }),
    error?.message || String(error));
}
