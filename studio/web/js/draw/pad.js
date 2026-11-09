// The drawing pad: mouse, touch and stylus input, undo and clear.
// Strokes are redrawn at a fixed 256x256 before upload, the size and 8 px black
// pen of demo/app.py, so the screen's pixel density cannot change the model's input.
import { el } from '../ui.js';

const SIDE = 256;
const PEN = 8;

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
  let active = null;

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
    active = [point(e)]; strokes.push(active); redraw();
    e.preventDefault();
  });
  canvas.addEventListener('pointermove', (e) => { if (active) { active.push(point(e)); redraw(); } });
  const end = () => { if (active) { active = null; changed(); } };
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', end);

  const clear = () => { strokes.length = 0; changed(); };
  const undo = () => { strokes.pop(); changed(); };
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
      el('button', { type: 'button', class: 'ghost', onclick: clear, text: 'Clear' })),
    png,
    strokeCount: () => strokes.length,
    strokes: () => strokes.map((stroke) => stroke.map(([x, y]) => [Math.round(x), Math.round(y)])),
  };
}
