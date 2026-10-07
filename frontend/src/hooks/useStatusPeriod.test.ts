import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useStatusPeriod } from './useStatusPeriod'

describe('useStatusPeriod', () => {
  it('starts on all time by month', () => {
    const { result } = renderHook(() => useStatusPeriod())
    expect(result.current.params).toEqual({ period: 'all', granularity: 'month' })
  })

  it('a custom range becomes period custom with from and to', () => {
    const { result } = renderHook(() => useStatusPeriod())

    act(() => result.current.setRange({ from: '2026-01-01', to: '2026-03-01' }))

    expect(result.current.params).toEqual({ period: 'custom', from: '2026-01-01', to: '2026-03-01', granularity: 'month' })
    expect(result.current.range).toEqual({ from: '2026-01-01', to: '2026-03-01' })
  })

  it('leaving custom drops the range from the params', () => {
    const { result } = renderHook(() => useStatusPeriod())
    act(() => result.current.setRange({ from: '2026-01-01', to: '2026-03-01' }))

    act(() => result.current.setPeriod('last_7_days'))

    expect(result.current.params).toEqual({ period: 'last_7_days', granularity: 'month' })
  })

  it('changes the granularity', () => {
    const { result } = renderHook(() => useStatusPeriod({ granularity: 'day' }))
    expect(result.current.params.granularity).toBe('day')

    act(() => result.current.setGranularity('year'))

    expect(result.current.params.granularity).toBe('year')
  })
})
