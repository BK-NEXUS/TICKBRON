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
  /** Iyeniń regiondaǵı orni (tek iye mehmanxana ekranı) */
  rank?: StatusRank | null
  series: StatusSeriesRow[]
  granularity: StatusGranularity
  onGranularityChange: (granularity: StatusGranularity) => void
  reconciliation: StatusReconciliation
  /** Qosımsha birinshi karta, mısalı iyeniń "beri" sanası */
  lead?: { label: string; value: string }
  guestsLabel?: string
}

/** Admin mehmanxana, iye qısqasha mazmunı hám iye mehmanxana ekranları ortaq paydalanatuǵın R12a deneti */
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
