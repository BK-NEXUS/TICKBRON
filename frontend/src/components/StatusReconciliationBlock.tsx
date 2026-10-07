import type { ReconciliationWindow, StatusReconciliation } from '../adapters/statusAdapter'
import { formatCount } from '../utils/statusFormat'
import { StatusStayedNote } from './StatusStayedNote'

interface StatusReconciliationBlockProps {
  reconciliation: StatusReconciliation
  /** For tests; defaults to now */
  today?: Date
}

const TEXT = {
  title: 'Reconciliation',
  hint: 'By check-in date, not limited by the selected period.',
  headers: ['Window', 'Dates', 'Counted bookings', 'Counted guests', 'Stayed bookings', 'Stayed guests'],
  rows: [
    ['today', 'Today'],
    ['this_week', 'This week'],
    ['this_month', 'This month'],
    ['this_year', 'This year'],
    ['all_time', 'All time'],
  ] as [keyof StatusReconciliation, string][],
}

const datesOf = ({ from, to }: ReconciliationWindow) => (from && to ? `${from} – ${to}` : '—')

/** Fixed windows next to the period numbers, so an owner can check them against their own books */
export function StatusReconciliationBlock({ reconciliation, today }: StatusReconciliationBlockProps) {
  return (
    <section className="status-reconciliation">
      <h3 className="status-chart-title">{TEXT.title}</h3>
      <p className="status-card-caption">{TEXT.hint}</p>
      <div className="customers-table-container">
        <table className="customers-table status-table" aria-label={TEXT.title}>
          <thead>
            <tr>
              {TEXT.headers.map((header, index) => (
                <th key={header} scope="col" className={index > 1 ? 'status-cell--numeric' : undefined}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {TEXT.rows.map(([key, label]) => {
              const window = reconciliation[key]
              return (
                <tr key={key}>
                  <td>{label}</td>
                  <td>{datesOf(window)}</td>
                  <td className="status-cell--numeric">{formatCount(window.counted.bookings)}</td>
                  <td className="status-cell--numeric">{formatCount(window.counted.guests)}</td>
                  <td className="status-cell--numeric">{formatCount(window.stayed.bookings)}</td>
                  <td className="status-cell--numeric">{formatCount(window.stayed.guests)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <StatusStayedNote today={today} />
    </section>
  )
}
