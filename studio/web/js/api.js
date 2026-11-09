// Calls to the local server. Nothing else talks to the network.

async function unpack(response) {
  if (response.ok) return response.json();
  let detail = `${response.status} ${response.statusText}`;
  try { const body = await response.json(); if (body.detail) detail = String(body.detail); } catch { /* keep status text */ }
  throw new Error(detail);
}

export const get = (url) => fetch(url).then(unpack);

export const post = (url, body) => fetch(url, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
}).then(unpack);

export const page = (name) => get(`/api/page/${name}`);
