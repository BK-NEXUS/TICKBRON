import { useEffect, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { statusAdapter } from '../adapters/statusAdapter'
import type { PartnerStatus } from '../adapters/statusAdapter'
import { useStatusPeriod } from '../hooks/useStatusPeriod'
import { formatDate } from '../utils/statusFormat'
import { SegmentedControl } from './SegmentedControl'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { StatusReport } from './StatusReport'
import { StatusCsvButton } from './StatusCsvButton'
import { PartnerArrivals } from './PartnerArrivals'
import { PartnerHotelStatus } from './PartnerHotelStatus'
import { PartnerStatusOverview } from './PartnerStatusOverview'
import { PartnerRoomsStatus } from './PartnerRoomsStatus'

type StatusView = 'overview' | 'rooms' | 'arrivals' | 'reports'

const VIEWS: readonly StatusView[] = ['overview', 'rooms', 'arrivals', 'reports']

/**
 * Partner panel > Status in four tabs: overview (this month, key numbers, charts, hotels), rooms (which room
 * types are booked most), arrivals (who comes soon) and reports (the full numbers, reconciliation, export).
 */
export function PartnerStatusTab() {
  const i18n = useI18n()
  const { t } = i18n
  const id = useId()
  const { params, period, range, granularity, setPeriod, setRange, setGranularity } = useStatusPeriod()
  const [view, setView] = useState<StatusView>('overview')
  const [year, setYear] = useState<number | undefined>(undefined)
  const [hotelId, setHotelId] = useState<number | null>(null)
  const [data, setData] = useState<PartnerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getPartnerStatus(year === undefined ? params : { ...params, year }).then(response => {
      if (cancelled) return
      if (response.data) setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [params, year, attempt])

  if (hotelId !== null) return <PartnerHotelStatus hotelId={hotelId} onBack={() => setHotelId(null)} />

  const header = (
    <div className="admin-view-header">
      <h2 className="admin-view-title">{t('partner.status')}</h2>
      <p className="admin-view-subtitle">{t('status.subtitle2')}</p>
    </div>
  )

  if (!data && !error) {
    return (
      <div className="partner-status">
        {header}
        <div className="loading-state" role="status" aria-live="polite">{t('status.loading3')}</div>
      </div>
    )
  }

  const panelId = (value: StatusView) => `${id}-${value}-panel`
  const options = VIEWS.map(value => ({ value, label: t(`ownerStatus.tab.${value}`), controls: panelId(value) }))
  const needsPeriod = view !== 'arrivals'

  return (
    <div className="partner-status" aria-busy={loading}>
      {header}

      <SegmentedControl<StatusView> mode="tabs" options={options} value={view} onChange={setView} aria-label={t('ownerStatus.tabsLabel')} />

      {needsPeriod && (
        <div className="status-controls">
          <StatusPeriodSelector value={period} range={range} onChange={setPeriod} onRangeChange={setRange} />
          {view === 'reports' && <StatusCsvButton onExport={format => statusAdapter.exportPartnerReconciliation(params, format)} />}
        </div>
      )}

      <div role="tabpanel" id={panelId(view)}>
        {error ? (
          <div className="alert alert-error" role="alert">
            <p>{error}</p>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setAttempt(n => n + 1)}>{t('common.tryAgain')}</button>
          </div>
        ) : data && view === 'overview' ? (
          <PartnerStatusOverview data={data} onYearChange={setYear} onOpenHotel={setHotelId} />
        ) : data && view === 'rooms' ? (
          <PartnerRoomsStatus params={params} hotels={data.properties.map(({ id: hotel, name }) => ({ id: hotel, name }))} />
        ) : view === 'arrivals' ? (
          <PartnerArrivals />
        ) : data && (
          <StatusReport
            period={data.period} periodRange={data.period_range} totals={data.totals} insights={data.insights} series={data.series}
            granularity={granularity} onGranularityChange={setGranularity} reconciliation={data.reconciliation}
            lead={{ label: t('status.since'), value: formatDate(data.since, i18n) }} guestsLabel={t('status.guestsLabel')}
          />
        )}
      </div>
    </div>
  )
}
