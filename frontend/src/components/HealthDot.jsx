import { useAsync } from '../useAsync'
import { getHealth } from '../api'

export default function HealthDot() {
  const { status, data } = useAsync(getHealth, [])

  let state = 'checking'
  let label = 'Checking…'
  if (status === 'error') {
    state = 'down'
    label = 'API unreachable'
  } else if (status === 'done') {
    state = data.status === 'ok' ? 'ok' : 'degraded'
    label = data.status === 'ok' ? 'All systems go' : 'Degraded'
  }

  const title =
    status === 'done'
      ? `Postgres ${data.postgres ? 'up' : 'down'} · Redis ${data.redis ? 'up' : 'down'}`
      : label

  return (
    <span className="health" data-state={state} title={title}>
      <span className="health__dot" aria-hidden="true" />
      <span className="health__label">{label}</span>
    </span>
  )
}
