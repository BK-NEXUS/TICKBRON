import { useCallback, useMemo, useState } from 'react'
import type { StatusGranularity, StatusPeriodParams } from '../adapters/statusAdapter'
import type { DateRange } from '../utils/statusPeriod'

interface Options {
  period?: string
  granularity?: StatusGranularity
}

/** Period, custom range and series granularity of a Status screen, with the params the adapter takes */
export function useStatusPeriod({ period: initialPeriod = 'all', granularity: initialGranularity = 'month' }: Options = {}) {
  const [period, setPeriod] = useState(initialPeriod)
  const [range, setRangeState] = useState<DateRange | null>(null)
  const [granularity, setGranularity] = useState<StatusGranularity>(initialGranularity)

  const setRange = useCallback((next: DateRange) => {
    setRangeState(next)
    setPeriod('custom')
  }, [])

  const params = useMemo<StatusPeriodParams>(
    () => (period === 'custom' && range ? { period, from: range.from, to: range.to, granularity } : { period, granularity }),
    [period, range, granularity],
  )

  return { params, period, range, granularity, setPeriod, setRange, setGranularity }
}
