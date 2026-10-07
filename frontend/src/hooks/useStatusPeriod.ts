import { useCallback, useMemo, useState } from 'react'
import type { StatusGranularity, StatusPeriodParams } from '../adapters/statusAdapter'
import type { DateRange } from '../utils/statusPeriod'

interface Options {
  period?: string
}

export const DEFAULT_GRANULARITY: StatusGranularity = 'month'

/** Period, custom range and series granularity of a Status screen, with the params the adapter takes */
export function useStatusPeriod({ period: initialPeriod = 'all' }: Options = {}) {
  const [period, setPeriod] = useState(initialPeriod)
  const [range, setRangeState] = useState<DateRange | null>(null)
  // Sent only after the user picks one; until then the backend default (month) applies
  const [chosenGranularity, setGranularity] = useState<StatusGranularity | undefined>(undefined)

  const setRange = useCallback((next: DateRange) => {
    setRangeState(next)
    setPeriod('custom')
  }, [])

  const params = useMemo<StatusPeriodParams>(() => {
    const base: StatusPeriodParams = period === 'custom' && range ? { period, from: range.from, to: range.to } : { period }
    return chosenGranularity ? { ...base, granularity: chosenGranularity } : base
  }, [period, range, chosenGranularity])

  return {
    params, period, range, granularity: chosenGranularity ?? DEFAULT_GRANULARITY, setPeriod, setRange, setGranularity,
  }
}
