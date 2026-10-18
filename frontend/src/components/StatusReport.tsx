import { useI18n } from '../i18n/I18nContext'
import type {
  PeriodRange, StatusFullTotals, StatusGranularity, StatusInsights as Insights, StatusRank,
  StatusReconciliation, StatusSeriesRow,
} from '../adapters/statusAdapter'
import { periodLabel } from '../utils/statusFormat'
import { StatusStatsCards } from './StatusStatsCards'
import { StatusInsights } from './StatusInsights'
import { StatusStayedNote } from './StatusStayedNote'
import { StatusBookingStatusCounts } from './StatusBookingStatusCounts'
import { StatusSeriesSection } from './StatusSeriesSection'
import { StatusReconciliationBlock } from './StatusReconciliationBlock'

interface StatusReportProps {
  period: string
  periodRange: PeriodRange
  totals: StatusFullTotals
  insights: Insights
  /** The owner's place in the region (owner hotel screen only) */
  rank?: StatusRank | null
  series: StatusSeriesRow[]
  granularity: StatusGranularity
  onGranularityChange: (granularity: StatusGranularity) => void
  reconciliation: StatusReconciliation
  /** Extra first card, e.g. the owner's "since" date */
  lead?: { label: string; value: string }
  guestsLabel?: string
}

/** The R12a body shared by the admin hotel, owner summary and owner hotel screens */
export function StatusReport({
  period, periodRange, totals, insights, rank, series, granularity, onGranularityChange, reconciliation, lead, guestsLabel,
}: StatusReportProps) {
  const i18n = useI18n()
  return (
    <>
      <StatusStatsCards totals={totals} caption={periodLabel(period, periodRange, i18n)} lead={lead} guestsLabel={guestsLabel} />
      <StatusInsights insights={insights} rank={rank} />
      <StatusStayedNote periodRange={periodRange} />
      <StatusBookingStatusCounts counts={totals.booking_status} />
      <StatusSeriesSection series={series} granularity={granularity} onGranularityChange={onGranularityChange} />
      <StatusReconciliationBlock reconciliation={reconciliation} />
    </>
  )
}
