export const SEVERITIES = ['error', 'warning', 'info']

export function shortSha(sha) {
  return typeof sha === 'string' ? sha.slice(0, 7) : sha
}

export function formatWhen(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function plural(n, word) {
  return `${word}${n === 1 ? '' : 's'}`
}

export function countBySeverity(findings) {
  const counts = { error: 0, warning: 0, info: 0 }
  for (const f of findings) {
    if (f.severity in counts) counts[f.severity] += 1
  }
  return counts
}

// Group findings by file, preserving the backend's ordering (file, then line).
export function groupByFile(findings) {
  const groups = []
  const index = new Map()
  for (const f of findings) {
    if (!index.has(f.file_path)) {
      index.set(f.file_path, groups.length)
      groups.push({ file: f.file_path, items: [] })
    }
    groups[index.get(f.file_path)].items.push(f)
  }
  return groups
}
