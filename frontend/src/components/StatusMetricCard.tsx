interface StatusMetricCardProps {
  label: string
  value: string
  caption: string
  /** Colours the caption for a change against last month */
  tone?: 'up' | 'down' | 'same' | 'none'
}

/** One number of a Status page: label, value and a small caption (a hint, or the change against last month). */
export function StatusMetricCard({ label, value, caption, tone }: StatusMetricCardProps) {
  return (
    <div className="status-card">
      <span className="status-card-label">{label}</span>
      <span className="status-card-value">{value}</span>
      <span className={`status-card-caption${tone ? ` status-change--${tone}` : ''}`}>{caption}</span>
    </div>
  )
}
