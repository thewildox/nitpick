// Thin fetch layer. The Vite dev server proxies /api/* to the FastAPI backend
// on :8000 (see vite.config.js), stripping the /api prefix.

async function getJSON(path) {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`Request failed (HTTP ${res.status})`)
  return res.json()
}

export const getRuns = () => getJSON('/api/runs')

export const getRun = (id) => getJSON(`/api/runs/${id}`)

// Health returns 200 {status:"ok"} or 503 {status:"degraded"}. We want the body
// in both cases, so we read it regardless of status and only surface a thrown
// error when the API is unreachable.
export async function getHealth() {
  const res = await fetch('/api/health')
  return res.json()
}
