const LABELS = {
  queued: 'Queued',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
}

export default function StatusPill({ status }) {
  return (
    <span className="pill" data-status={status}>
      {LABELS[status] ?? status}
    </span>
  )
}
