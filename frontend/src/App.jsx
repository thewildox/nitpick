import { useState, useEffect } from 'react'

function App() {
  // ---- STATE: three things this component remembers ----
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // ---- EFFECT: runs once when the component mounts ----
  useEffect(() => {
    fetch('/api/runs')                          // Vite proxies this to :8000/runs
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => setRuns(data))            // success → store runs in state
      .catch((err) => setError(err.message))    // failure → store the error
      .finally(() => setLoading(false))         // either way → done loading
  }, [])                                        // [] = run once, not every render

  // ---- RENDER: UI as a function of state ----
  if (loading) return <p>Loading runs…</p>
  if (error) return <p>Error: {error}</p>

  return (
    <div>
      <h1>Nitpick — Analysis Runs</h1>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Status</th>
            <th>Commit</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            // key: React needs a stable unique id per row
            <tr key={run.id}>
              <td>{run.id}</td>
              <td>{run.status}</td>
              <td>{run.commit_sha.slice(0, 7)}</td>
              <td>{new Date(run.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App