import { useI18n } from '../i18n/I18nContext'
import type { CommissionMonth, CommissionStatement as Statement, MoneyLine } from '../adapters/commissionTypes'

interface CommissionStatementProps {
  statement: Statement
  /** Staff and super admins confirm paid months; the owner only reads */
  confirmation?: {
    busyMonth: string | null
    onConfirm: (month: string) => void
    onUndo: (month: string) => void
  }
}

/** "2026-05" of the browser's today, to tell the months that can still change from the ended ones */
function thisMonthKey(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

/** The commission months (and year totals when the account is a year old) of one owner. */
export function CommissionStatement({ statement, confirmation }: CommissionStatementProps) {
  const { t, formatDate, formatMoney } = useI18n()

  const money = (lines: MoneyLine[] | null) => {
    if (lines === null) return t('commission.notSet')
    if (lines.length === 0) return '-'
    return lines.map(line => (
      <div key={line.currency}>{formatMoney(line.amount, line.currency, { minDecimals: 2, maxDecimals: 2 })}</div>
    ))
  }

  const monthName = (month: string) => {
    const [year, number] = month.split('-').map(Number)
    return formatDate(new Date(year, number - 1, 1), { month: 'long', year: 'numeric' })
  }

  const confirmable = (row: CommissionMonth) => (
    row.month < thisMonthKey() && row.paid === null && (row.commission ?? []).some(line => Number(line.amount) > 0)
  )

  return (
    <div className="commission-statement">
      <div className="commission-percent-line">
        {statement.percent === null
          ? <p className="auth-hint">{t('commission.percentNone')}</p>
          : <p><strong>{t('commission.percent')}: {statement.percent}%</strong>
            {statement.percent_since && <span className="promotion-city"> {t('commission.percentSince', { date: formatDate(statement.percent_since) })}</span>}</p>}
      </div>

      <h3 className="admin-section-title">{t('commission.months')}</h3>
      <div className="commission-table-wrap">
        <table className="commission-table">
          <thead>
            <tr>
              <th scope="col">{t('commission.col.month')}</th>
              <th scope="col">{t('commission.col.bookings')}</th>
              <th scope="col">{t('commission.col.gross')}</th>
              <th scope="col">{t('commission.col.percent')}</th>
              <th scope="col">{t('commission.col.commission')}</th>
              <th scope="col">{t('commission.col.paid')}</th>
            </tr>
          </thead>
          <tbody>
            {statement.months.map(row => (
              <tr key={row.month}>
                <th scope="row">{monthName(row.month)}</th>
                <td>{row.bookings}</td>
                <td>{money(row.gross)}</td>
                <td>{row.percent === null ? t('commission.notSet') : `${row.percent}%`}</td>
                <td>{money(row.commission)}</td>
                <td>
                  {row.paid ? (
                    <div>
                      <span className="status-badge status-badge--active">{t('commission.paid')}</span>
                      <div className="promotion-city">
                        {t('commission.confirmedBy', { name: row.paid.by, role: t(`commission.role.${row.paid.role}`) })}
                      </div>
                      <div className="promotion-city">{formatDate(row.paid.at)}</div>
                    </div>
                  ) : <span className="promotion-city">{t('commission.notPaid')}</span>}
                  {confirmation && confirmable(row) && (
                    <button type="button" className="btn btn-primary btn-sm" disabled={confirmation.busyMonth === row.month}
                      aria-label={`${t('commission.confirm')}: ${monthName(row.month)}`}
                      onClick={() => confirmation.onConfirm(row.month)}>
                      {t('commission.confirm')}
                    </button>
                  )}
                  {confirmation && row.paid && (
                    <button type="button" className="btn btn-secondary btn-sm" disabled={confirmation.busyMonth === row.month}
                      aria-label={`${t('commission.undo')}: ${monthName(row.month)}`}
                      onClick={() => confirmation.onUndo(row.month)}>
                      {t('commission.undo')}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {statement.years && statement.years.length > 0 && (
        <>
          <h3 className="admin-section-title">{t('commission.years')}</h3>
          <div className="commission-table-wrap">
            <table className="commission-table">
              <thead>
                <tr>
                  <th scope="col">{t('commission.col.year')}</th>
                  <th scope="col">{t('commission.col.bookings')}</th>
                  <th scope="col">{t('commission.col.gross')}</th>
                  <th scope="col">{t('commission.col.commission')}</th>
                </tr>
              </thead>
              <tbody>
                {statement.years.map(row => (
                  <tr key={row.year}>
                    <th scope="row">{row.year}</th>
                    <td>{row.bookings}</td>
                    <td>{money(row.gross)}</td>
                    <td>{money(row.commission)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
