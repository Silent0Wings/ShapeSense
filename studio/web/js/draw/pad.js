// The drawing pad: mouse, touch and stylus input, undo, clear, rotate and scale.
// Strokes are redrawn at a fixed 256x256 before upload, the size and 8 px black
// pen of demo/app.py, so the screen's pixel density cannot change the model's input.
import { s } from '../svg/core.js';
import { el } from '../ui.js';

const SIDE = 256;
const PEN = 8;
const ROTATE_DEG = 15;
const SCALE_STEP = 1.1;
const MIN_SIZE = 16;
const ICONS = {
  left: ['M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8', 'M3 3v5h5'],
  right: ['M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8', 'M21 3v5h-5'],
  smaller: ['M21 21l-4.3-4.3', 'M8 11h6', 'M19 11a8 8 0 1 1-16 0 8 8 0 0 1 16 0z'],
  larger: ['M21 21l-4.3-4.3', 'M8 11h6', 'M11 8v6', 'M19 11a8 8 0 1 1-16 0 8 8 0 0 1 16 0z'],
};

function icon(name) {
  return s('svg', { class: 'icon', viewBox: '0 0 24 24', 'aria-hidden': 'true' }, ...ICONS[name].map((d) => s('path', { d })));
}

function paint(ctx, strokes, paper, ink) {
  ctx.fillStyle = paper;
  ctx.fillRect(0, 0, SIDE, SIDE);
  ctx.strokeStyle = ink; ctx.fillStyle = ink;
  ctx.lineWidth = PEN; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const stroke of strokes) {
    ctx.beginPath();
    ctx.moveTo(stroke[0][0], stroke[0][1]);
    if (stroke.length === 1) ctx.lineTo(stroke[0][0] + .01, stroke[0][1]);
    for (const [x, y] of stroke.slice(1)) ctx.lineTo(x, y);
    ctx.stroke();
  }
}

export function createPad({ onChange }) {
  const canvas = el('canvas', { class: 'pad', width: SIDE, height: SIDE, role: 'img', 'aria-label': 'Drawing area', 'data-tip': 'Draw one shape here with a mouse, finger or stylus.' });
  const ctx = canvas.getContext('2d');
  const strokes = [];
  const history = [];   // earlier states, for undo
  let active = null;
  const snapshot = () => strokes.map((stroke) => stroke.map((p) => [...p]));
  const restore = (state) => { strokes.length = 0; strokes.push(...state); };

  const point = (e) => {
    const box = canvas.getBoundingClientRect();
    return [((e.clientX - box.left) / box.width) * SIDE, ((e.clientY - box.top) / box.height) * SIDE];
  };
  // The screen follows the theme; the upload below is always black on white.
  const redraw = () => {
    const style = getComputedStyle(document.documentElement);
    paint(ctx, strokes, style.getPropertyValue('--pad-paper').trim(), style.getPropertyValue('--pad-ink').trim());
  };
  const changed = () => { redraw(); onChange(strokes.length); };

  canvas.addEventListener('pointerdown', (e) => {
    canvas.setPointerCapture(e.pointerId);
    history.push(snapshot());
    active = [point(e)]; strokes.push(active); redraw();
    e.preventDefault();
  });
  canvas.addEventListener('pointermove', (e) => { if (active) { active.push(point(e)); redraw(); } });
  const end = () => { if (active) { active = null; changed(); } };
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', end);

  const clear = () => { strokes.length = 0; history.length = 0; changed(); };
  const undo = () => { if (history.length) { restore(history.pop()); changed(); } };

  const bounds = (state) => {
    const points = state.flat(); const xs = points.map((p) => p[0]); const ys = points.map((p) => p[1]);
    return { x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) };
  };
  // Moves every point around the drawing's centre. A change that would leave the
  // canvas, or shrink the drawing to almost nothing, is ignored.
  const transform = (move) => {
    if (active || !strokes.length) return;
    const was = bounds(strokes);
    const cx = (was.x0 + was.x1) / 2; const cy = (was.y0 + was.y1) / 2;
    const next = strokes.map((stroke) => stroke.map(([x, y]) => move(x - cx, y - cy)));
    const box = bounds(next);
    const size = Math.max(box.x1 - box.x0, box.y1 - box.y0);
    if (size > SIDE - PEN || size < MIN_SIZE) return;
    const low = PEN / 2; const high = SIDE - PEN / 2;
    const fit = (value, lo, hi) => (lo + value < low ? low - lo : hi + value > high ? high - hi : value);
    const dx = fit(cx, box.x0, box.x1); const dy = fit(cy, box.y0, box.y1);
    history.push(snapshot());
    restore(next.map((stroke) => stroke.map(([x, y]) => [x + dx, y + dy])));
    changed();
  };
  const rotate = (deg) => {
    const c = Math.cos((deg * Math.PI) / 180); const n = Math.sin((deg * Math.PI) / 180);
    transform((x, y) => [x * c - y * n, x * n + y * c]);
  };
  const scale = (k) => transform((x, y) => [x * k, y * k]);
  const tool = (name, label, tip, onclick) => el('button', { type: 'button', class: 'ghost icon-button', onclick, 'aria-label': label, 'data-tip': tip }, icon(name));
  const refit = 'Every drawing is re-framed to the same size before the model sees it, so this mostly changes how thick the line looks.';
  redraw();
  new MutationObserver(redraw).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', redraw);

  function png() {
    const copy = el('canvas', { width: SIDE, height: SIDE });
    paint(copy.getContext('2d'), strokes, '#ffffff', '#000000');
    return copy.toDataURL('image/png');
  }

  return {
    canvas,
    controls: el('div', { class: 'toolbar' },
      el('button', { type: 'button', class: 'ghost', onclick: undo, text: 'Undo' }),
      el('button', { type: 'button', class: 'ghost', onclick: clear, text: 'Clear' }),
      tool('left', 'Rotate left', `Turn the drawing ${ROTATE_DEG}° to the left.`, () => rotate(-ROTATE_DEG)),
      tool('right', 'Rotate right', `Turn the drawing ${ROTATE_DEG}° to the right.`, () => rotate(ROTATE_DEG)),
      tool('smaller', 'Scale down', `Make the drawing smaller. ${refit}`, () => scale(1 / SCALE_STEP)),
      tool('larger', 'Scale up', `Make the drawing larger, up to the canvas edge. ${refit}`, () => scale(SCALE_STEP))),
    png,
    strokeCount: () => strokes.length,
    strokes: () => strokes.map((stroke) => stroke.map(([x, y]) => [Math.round(x), Math.round(y)])),
  };
}
