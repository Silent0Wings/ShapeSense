// The drawing pad: mouse, touch and stylus input, undo and clear.
// Strokes are redrawn at a fixed 256x256 before upload, the size and 8 px black
// pen of demo/app.py, so the screen's pixel density cannot change the model's input.
import { el } from '../ui.js';

const SIDE = 256;
const PEN = 8;

function paint(ctx, strokes) {
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, SIDE, SIDE);
  ctx.strokeStyle = '#000000'; ctx.fillStyle = '#000000';
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
  const canvas = el('canvas', { class: 'pad', width: SIDE, height: SIDE, role: 'img', 'aria-label': 'Drawing area' });
  const ctx = canvas.getContext('2d');
  const strokes = [];
  let active = null;

  const point = (e) => {
    const box = canvas.getBoundingClientRect();
    return [((e.clientX - box.left) / box.width) * SIDE, ((e.clientY - box.top) / box.height) * SIDE];
  };
  const redraw = () => paint(ctx, strokes);
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

  return {
    canvas,
    controls: el('div', { class: 'toolbar' },
      el('button', { type: 'button', class: 'ghost', onclick: undo, text: 'Undo' }),
      el('button', { type: 'button', class: 'ghost', onclick: clear, text: 'Clear' })),
    png: () => canvas.toDataURL('image/png'),
    strokeCount: () => strokes.length,
    strokes: () => strokes.map((stroke) => stroke.map(([x, y]) => [Math.round(x), Math.round(y)])),
  };
}
