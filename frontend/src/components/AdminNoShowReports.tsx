import { useCallback, useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { noShowAdapter, type NoShowReportStatus, type ReportPage, type StaffNoShowReport } from '../adapters/noShowAdapter'
import { NoShowDecisionDialog, type NoShowDecision } from './NoShowDecisionDialog'
import { StatusPagination } from './StatusPagination'

const PAGE_SIZE = 20
const STATUSES: NoShowReportStatus[] = ['pending', 'approved', 'rejected', 'withdrawn']
const BADGE: Record<NoShowReportStatus, string> = {
  pending: 'pending', approved: 'completed', rejected: 'cancelled', withdrawn: 'inactive',
}
const REFUND_STATES = ['pending', 'succeeded', 'failed', 'needs_manual'] as const

/** The staff queue of "guest did not arrive" reports. Staff and super-admin may both decide. */
export function AdminNoShowReports() {
  const { t, formatDate, formatMoney } = useI18n()
  const [status, setStatus] = useState('pending')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<ReportPage<StaffNoShowReport> | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [deciding, setDeciding] = useState<{ report: StaffNoShowReport; decision: NoShowDecision } | null>(null)

  // Doubles as the Try Again button
  const load = useCallback(async () => {
    setLoading(true)
    setLoadFailed(false)
    const result = await noShowAdapter.listReports({ status, from, to, page })
    if (result.data) setData(result.data)
    else setLoadFailed(true)
    setLoading(false)
  }, [status, from, to, page])

  useEffect(() => {
    void load()
  }, [load])

  const money = (amount: string, currency: string) => formatMoney(amount, currency, { minDecimals: 0, maxDecimals: 0 })

  const refundState = (state: string) =>
    (REFUND_STATES as readonly string[]).includes(state) ? t(`noShowAdmin.refundState.${state}` as 'noShowAdmin.refundState.pending') : state

  const reports = data?.results ?? []

  return (
    <div className="admin-no-show-reports">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('noShowAdmin.title')}</h2>
        <p className="admin-view-subtitle">{t('noShowAdmin.subtitle')}</p>
      </div>

      <div className="customers-controls">
        <div className="search-bar">
          <label htmlFor="no-show-queue-status" className="search-label">{t('noShow.filter.status')}</label>
          <select id="no-show-queue-status" className="search-input" value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
            <option value="">{t('noShow.filter.all')}</option>
            {STATUSES.map(value => <option key={value} value={value}>{t(`noShow.status.${value}`)}</option>)}
          </select>
        </div>
        <div className="search-bar">
          <label htmlFor="no-show-queue-from" className="search-label">{t('noShowAdmin.from')}</label>
          <input id="no-show-queue-from" type="date" className="search-input" value={from}
            onChange={(e) => { setFrom(e.target.value); setPage(1) }} />
        </div>
        <div className="search-bar">
          <label htmlFor="no-show-queue-to" className="search-label">{t('noShowAdmin.to')}</label>
          <input id="no-show-queue-to" type="date" className="search-input" value={to} min={from || undefined}
            onChange={(e) => { setTo(e.target.value); setPage(1) }} />
        </div>
      </div>

      {loadFailed && (
        <div className="alert alert-error" role="alert">
          <p>{t('noShowAdmin.loadError')}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && !data && !loadFailed && <p className="loading-state">{t('noShowAdmin.loading')}</p>}
      {!loading && !loadFailed && reports.length === 0 && <p className="empty-state">{t('noShowAdmin.empty')}</p>}

      {reports.length > 0 && (
        <ul className="no-show-report-list">
          {reports.map(report => (
            <li key={report.id} className="booking-card no-show-report">
              <div className="booking-card-header">
                <div className="booking-property-info">
                  <h3 className="booking-property-name">{report.property_name}</h3>
                  <p className="booking-confirmation-code">{report.booking_reference}</p>
                  <p className="no-show-report-stay">
                    {t('noShow.stay', { checkIn: formatDate(report.check_in), checkOut: formatDate(report.check_out) })}
                  </p>
                </div>
                <div className="booking-status-badges">
                  {report.hotel_flagged && <span className="status-badge status-badge--cancelled">{t('noShowAdmin.flagged')}</span>}
                  <span className={`status-badge status-badge--${BADGE[report.status]}`}>{t(`noShow.status.${report.status}`)}</span>
                </div>
              </div>
              <div className="booking-card-body">
                <div className="booking-detail">
                  <span className="detail-label">{t('noShow.yourComment')}</span>
                  <p className="detail-value">{report.comment}</p>
                </div>
                {report.decision_comment && (
                  <div className="booking-detail">
                    <span className="detail-label">{t('noShow.decisionComment')}</span>
                    <p className="detail-value">{report.decision_comment}</p>
                  </div>
                )}
                {report.refund_preview && (
                  <div className="no-show-refund-preview">
                    <p>
                      {t('noShowAdmin.ifApproved', {
                        percent: report.refund_preview.percent,
                        paid: money(report.refund_preview.paid, report.refund_preview.currency),
                        amount: money(report.refund_preview.amount, report.refund_preview.currency),
                      })}
                    </p>
                    {Number(report.refund_preview.already_refunded) > 0 && (
                      <p>{t('noShowAdmin.alreadyRefunded', { amount: money(report.refund_preview.already_refunded, report.refund_preview.currency) })}</p>
                    )}
                  </div>
                )}
                {report.refunds.map(refund => (
                  <p key={refund.id} className="no-show-refund-line">
                    {t('noShowAdmin.refund', { amount: money(refund.amount, refund.currency), state: refundState(refund.status) })}
                  </p>
                ))}
              </div>
              <div className="booking-card-footer">
                {report.status === 'pending' && (
                  <div className="promotion-actions">
                    <button type="button" className="btn btn-primary btn-sm" onClick={() => setDeciding({ report, decision: 'approve' })}>
                      {t('noShowAdmin.approve')}
                    </button>
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => setDeciding({ report, decision: 'reject' })}>
                      {t('noShowAdmin.reject')}
                    </button>
                  </div>
                )}
                {(report.status === 'approved' || report.status === 'rejected') && (
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setDeciding({ report, decision: 'reverse' })}>
                    {t('noShowAdmin.reverse')}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {data && data.count > PAGE_SIZE && (
        <StatusPagination page={page} count={data.count} pageSize={PAGE_SIZE}
          hasPrevious={page > 1} hasNext={Boolean(data.next)} onPage={setPage} />
      )}

      {deciding && (
        <NoShowDecisionDialog
          report={deciding.report}
          decision={deciding.decision}
          onClose={() => setDeciding(null)}
          onDone={() => { setDeciding(null); void load() }}
        />
      )}
    </div>
  )
}
