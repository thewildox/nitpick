import { useAsync } from '../useAsync'
import { getRuns } from '../api'
import { shortSha, formatWhen } from '../format'
import StatusPill from './StatusPill'

export default function RunsList() {
  const { status, data: runs, error } = useAsync(getRuns, [])

  return (
    <section>
      <div className="page-head">
        <p className="eyebrow">Analysis</p>
        <h1 className="page-title">Runs</h1>
        <p className="page-sub">Every commit Nitpick has reviewed, newest first.</p>
      </div>

      {status === 'loading' && (
        <div className="runs" aria-hidden="true">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="skeleton" />
          ))}
        </div>
      )}

      {status === 'error' && (
        <div className="notice">
          <h2>Couldn’t load runs</h2>
          <p>The dashboard can’t reach the API. Is it running on :8000?</p>
          <p><code>{error}</code></p>
        </div>
      )}

      {status === 'done' && runs.length === 0 && (
        <div className="notice">
          <h2>No runs yet</h2>
          <p>
            Open a pull request on a connected repo and Nitpick’s review will
            show up here.
          </p>
        </div>
      )}

      {status === 'done' && runs.length > 0 && (
        <ol className="runs">
          {runs.map((run) => (
            <li key={run.id}>
              <a className="run" href={`#/runs/${run.id}`}>
                <span className="run__id">#{run.id}</span>
                <StatusPill status={run.status} />
                <code className="run__sha">{shortSha(run.commit_sha)}</code>
                <span className="run__pr">pr:{run.pull_request_id}</span>
                <span className="run__time">{formatWhen(run.created_at)}</span>
                <span className="run__chev" aria-hidden="true">→</span>
              </a>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
