import { useAsync } from '../useAsync'
import { getRun } from '../api'
import {
  SEVERITIES,
  shortSha,
  formatWhen,
  plural,
  countBySeverity,
  groupByFile,
} from '../format'
import StatusPill from './StatusPill'

export default function RunDetail({ runId }) {
  const { status, data: run, error } = useAsync(() => getRun(runId), [runId])

  if (status === 'loading') {
    return (
      <section>
        <a className="back" href="#/">← All runs</a>
        <p className="state">Loading run #{runId}…</p>
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section>
        <a className="back" href="#/">← All runs</a>
        <div className="notice">
          <h2>Couldn’t load run #{runId}</h2>
          <p><code>{error}</code></p>
        </div>
      </section>
    )
  }

  const findings = run.findings ?? []
  const counts = countBySeverity(findings)
  const groups = groupByFile(findings)

  return (
    <section>
      <a className="back" href="#/">← All runs</a>

      <div className="page-head">
        <p className="eyebrow">Run #{run.id}</p>
        <h1 className="page-title">
          <code>{shortSha(run.commit_sha)}</code>
        </h1>
        <div className="run-meta">
          <StatusPill status={run.status} />
          <span>reviewed {formatWhen(run.created_at)}</span>
        </div>
      </div>

      <div className="tally">
        {SEVERITIES.map((sev) => (
          <span
            key={sev}
            className="tally__chip"
            data-sev={sev}
            data-empty={counts[sev] === 0}
          >
            <b>{counts[sev]}</b> {plural(counts[sev], sev)}
          </span>
        ))}
      </div>

      {findings.length === 0 ? (
        <div className="notice notice--clean">
          <span className="notice__mark" aria-hidden="true">✓</span>
          <h2>Nothing to nitpick</h2>
          <p>This commit came back clean — no findings on the changed lines.</p>
        </div>
      ) : (
        groups.map(({ file, items }) => (
          <div className="file" key={file}>
            <div className="file__head">
              <code>{file}</code>
              <span className="file__count">
                {items.length} {plural(items.length, 'finding')}
              </span>
            </div>
            <ul className="findings">
              {items.map((f) => (
                <li className="finding" data-sev={f.severity} key={f.id}>
                  <span className="finding__line">{f.line_number}</span>
                  <div className="finding__body">
                    <div className="finding__meta">
                      <span className="finding__source">{f.source}</span>
                      {f.rule_id && <code className="finding__rule">{f.rule_id}</code>}
                      <span className="finding__sev">{f.severity}</span>
                    </div>
                    <p className="finding__msg">{f.message}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </section>
  )
}
