import { useCallback, useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { noShowAdapter, type NoShowReportStatus, type OwnerNoShowReport, type ReportPage } from '../adapters/noShowAdapter'
import { noShowErrorKey } from '../utils/noShowErrors'
import { StatusPagination } from './StatusPagination'

const PAGE_SIZE = 20
const STATUSES: NoShowReportStatus[] = ['pending', 'approved', 'rejected', 'withdrawn']
const BADGE: Record<NoShowReportStatus, string> = {
  pending: 'pending', approved: 'completed', rejected: 'cancelled', withdrawn: 'inactive',
}

interface PartnerNoShowReportsProps {
  /** The owner's hotels, for the hotel filter */
  properties: Array<{ id: number; name: string }>
}

/** "My reports": what the owner told staff about guests who did not arrive, and what staff decided. */
export function PartnerNoShowReports({ properties }: PartnerNoShowReportsProps) {
  const { t, formatDate } = useI18n()
  const [status, setStatus] = useState('')
  const [property, setProperty] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<ReportPage<OwnerNoShowReport> | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [actionError, setActionError] = useState<ReturnType<typeof noShowErrorKey> | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  // Doubles as the Try Again button
  const load = useCallback(async () => {
    setLoading(true)
    setLoadFailed(false)
    const result = await noShowAdapter.listMyReports({ status, property: property ? Number(property) : undefined, page })
    if (result.data) setData(result.data)
    else setLoadFailed(true)
    setLoading(false)
  }, [status, property, page])

  useEffect(() => {
    void load()
  }, [load])

  const withdraw = async (report: OwnerNoShowReport) => {
    setBusyId(report.id)
    setActionError(null)
    const result = await noShowAdapter.withdrawReport(report.id)
    setBusyId(null)
    if (result.error) {
      setActionError(noShowErrorKey(result.code, result.fieldErrors))
      return
    }
    await load()
  }

  const reports = data?.results ?? []

  return (
    <div className="partner-no-show-reports">
      <div className="bookings-view-header">
        <h1 className="bookings-view-title">{t('noShow.myReports')}</h1>
        <p className="bookings-view-subtitle">{t('noShow.myReportsSubtitle')}</p>
      </div>

      <div className="bookings-filters">
        <div className="filter-group">
          <label htmlFor="no-show-status-filter">{t('noShow.filter.status')}</label>
          <select id="no-show-status-filter" className="filter-select" value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
            <option value="">{t('noShow.filter.all')}</option>
            {STATUSES.map(value => <option key={value} value={value}>{t(`noShow.status.${value}`)}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="no-show-hotel-filter">{t('noShow.filter.hotel')}</label>
          <select id="no-show-hotel-filter" className="filter-select" value={property}
            onChange={(e) => { setProperty(e.target.value); setPage(1) }}>
            <option value="">{t('noShow.filter.allHotels')}</option>
            {properties.map(hotel => <option key={hotel.id} value={hotel.id}>{hotel.name}</option>)}
          </select>
        </div>
      </div>

      {actionError && <p className="alert alert-error" role="alert">{t(actionError)}</p>}
      {loadFailed && (
        <div className="alert alert-error" role="alert">
          <p>{t('noShow.reports.loadError')}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && !data && !loadFailed && <p className="loading-state">{t('noShow.reports.loading')}</p>}
      {!loading && !loadFailed && reports.length === 0 && <p className="empty-state">{t('noShow.reports.empty')}</p>}

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
                <span className={`status-badge status-badge--${BADGE[report.status]}`}>{t(`noShow.status.${report.status}`)}</span>
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
              </div>
              {report.status === 'pending' && (
                <div className="booking-card-footer">
                  <button type="button" className="btn btn-secondary btn-sm" disabled={busyId === report.id}
                    onClick={() => void withdraw(report)}>
                    {t('noShow.withdraw')}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {data && data.count > PAGE_SIZE && (
        <StatusPagination page={page} count={data.count} pageSize={PAGE_SIZE}
          hasPrevious={page > 1} hasNext={Boolean(data.next)} onPage={setPage} />
      )}
    </div>
  )
}
