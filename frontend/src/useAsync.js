import { useEffect, useState } from 'react'

// Runs an async function on mount (and whenever deps change), tracking
// loading / done / error as a single state object. Guards against setting
// state after unmount or a superseded request: the cleanup flips `alive`, so
// a stale in-flight promise can't overwrite fresher state.
export function useAsync(fn, deps) {
  const [state, setState] = useState({ status: 'loading', data: null, error: null })

  useEffect(() => {
    let alive = true
    fn().then(
      (data) => alive && setState({ status: 'done', data, error: null }),
      (err) => alive && setState({ status: 'error', data: null, error: err.message }),
    )
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return state
}
