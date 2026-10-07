import type {
  PeriodRange, StatusFullTotals, StatusGranularity, StatusReconciliation, StatusSeriesRow,
} from '../adapters/statusAdapter'
import { periodLabel } from '../utils/statusFormat'
import { StatusStatsCards } from './StatusStatsCards'
import { StatusStayedNote } from './StatusStayedNote'
import { StatusBookingStatusCounts } from './StatusBookingStatusCounts'
import { StatusSeriesSection } from './StatusSeriesSection'
import { StatusReconciliationBlock } from './StatusReconciliationBlock'

interface StatusReportProps {
  period: string
  periodRange: PeriodRange
  totals: StatusFullTotals
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
  period, periodRange, totals, series, granularity, onGranularityChange, reconciliation, lead, guestsLabel,
}: StatusReportProps) {
  return (
    <>
      <StatusStatsCards totals={totals} caption={periodLabel(period, periodRange)} lead={lead} guestsLabel={guestsLabel} />
      <StatusStayedNote periodRange={periodRange} />
      <StatusBookingStatusCounts counts={totals.booking_status} />
      <StatusSeriesSection series={series} granularity={granularity} onGranularityChange={onGranularityChange} />
      <StatusReconciliationBlock reconciliation={reconciliation} />
    </>
  )
}
