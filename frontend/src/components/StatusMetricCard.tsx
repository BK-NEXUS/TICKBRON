import { statusCardClass } from '../utils/statusFormat'

interface StatusMetricCardProps {
  label: string
  value: string
  caption: string
  /** Aldınǵı ayǵa qarata ózgeris ushın jazıwdı reńleydi */
  tone?: 'up' | 'down' | 'same' | 'none'
}

/** Status betiniń bir sanı: belgi, mánis hám kishi jazıw (eskertpe, yamasa aldınǵı ayǵa qarata ózgeris). */
export function StatusMetricCard({ label, value, caption, tone }: StatusMetricCardProps) {
  return (
    <div className={statusCardClass(value)}>
      <span className="status-card-label">{label}</span>
      <span className="status-card-value">{value}</span>
      <span className={`status-card-caption${tone ? ` status-change--${tone}` : ''}`}>{caption}</span>
    </div>
  )
}
