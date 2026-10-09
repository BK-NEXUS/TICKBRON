import { textKeys, useTexts } from '../i18n/I18nContext'
import type { ReconciliationWindow, StatusReconciliation } from '../adapters/statusAdapter'
import { formatCount } from '../utils/statusFormat'
import { StatusStayedNote } from './StatusStayedNote'

interface StatusReconciliationBlockProps {
  reconciliation: StatusReconciliation
  /** For tests; defaults to now */
  today?: Date
}

const TEXT_KEYS = textKeys({
  title: 'status.title4',
  hint: 'status.hint',
  window: 'status.window',
  dates: 'status.dates',
  countedBookings: 'status.countedBookings',
  countedGuests: 'status.countedGuests',
  stayedBookings: 'status.stayedBookings',
  stayedGuests: 'status.stayedGuests',
  today: 'status.today',
  thisWeek: 'status.thisWeek',
  thisMonth: 'status.thisMonth',
  thisYear: 'status.thisYear',
  allTime: 'status.all',
})

const ROW_KEYS: [keyof StatusReconciliation, keyof typeof TEXT_KEYS][] = [
  ['today', 'today'],
  ['this_week', 'thisWeek'],
  ['this_month', 'thisMonth'],
  ['this_year', 'thisYear'],
  ['all_time', 'allTime'],
]

const datesOf = ({ from, to }: ReconciliationWindow) => (from && to ? `${from} – ${to}` : '—')

/** Fixed windows next to the period numbers, so an owner can check them against their own books */
export function StatusReconciliationBlock({ reconciliation, today }: StatusReconciliationBlockProps) {
  const TEXT = useTexts(TEXT_KEYS)
  return (
    <section className="status-reconciliation">
      <h3 className="status-chart-title">{TEXT.title}</h3>
      <p className="status-card-caption">{TEXT.hint}</p>
      <div className="customers-table-container">
        <table className="customers-table status-table" aria-label={TEXT.title}>
          <thead>
            <tr>
              {[TEXT.window, TEXT.dates, TEXT.countedBookings, TEXT.countedGuests, TEXT.stayedBookings, TEXT.stayedGuests].map((header, index) => (
                <th key={header} scope="col" className={index > 1 ? 'status-cell--numeric' : undefined}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROW_KEYS.map(([key, labelKey]) => {
              const label = TEXT[labelKey]
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
