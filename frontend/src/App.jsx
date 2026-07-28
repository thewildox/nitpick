import { useEffect, useState } from 'react'
import RunsList from './components/RunsList'
import RunDetail from './components/RunDetail'
import HealthDot from './components/HealthDot'

// Minimal hash router — no dependency, and the browser back button just works.
//   #/            → runs list
//   #/runs/:id    → run detail
function parseHash() {
  const path = window.location.hash.replace(/^#/, '') || '/'
  const match = path.match(/^\/runs\/(\d+)$/)
  if (match) return { name: 'detail', runId: Number(match[1]) }
  return { name: 'list' }
}

function useHashRoute() {
  const [route, setRoute] = useState(parseHash)
  useEffect(() => {
    const onChange = () => setRoute(parseHash())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

export default function App() {
  const route = useHashRoute()

  return (
    <div className="app">
      <header className="topbar">
        <a className="wordmark" href="#/">
          <span className="wordmark__dots" aria-hidden="true">
            <i /><i /><i />
          </span>
          nitpick
        </a>
        <HealthDot />
      </header>

      <main className="main">
        {route.name === 'detail' ? (
          <RunDetail key={route.runId} runId={route.runId} />
        ) : (
          <RunsList />
        )}
      </main>
    </div>
  )
}
