import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { StatusPeriodSelector } from './StatusPeriodSelector'

describe('StatusPeriodSelector', () => {
  const today = new Date(2026, 8, 30) // 2026-09-30

  it('starts on all time', () => {
    render(<StatusPeriodSelector value="all" onChange={vi.fn()} today={today} />)
    expect(screen.getByLabelText('Period')).toHaveValue('all')
    expect(screen.queryByLabelText('Year')).not.toBeInTheDocument()
  })

  it('switching to a year picks the current year', () => {
    const onChange = vi.fn()
    render(<StatusPeriodSelector value="all" onChange={onChange} today={today} />)

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'year' } })

    expect(onChange).toHaveBeenCalledWith('2026')
  })

  it('switching to a month picks the current month', () => {
    const onChange = vi.fn()
    render(<StatusPeriodSelector value="all" onChange={onChange} today={today} />)

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'month' } })

    expect(onChange).toHaveBeenCalledWith('2026-09')
  })

  it('changes the year and the month', () => {
    const onChange = vi.fn()
    const { rerender } = render(<StatusPeriodSelector value="2026" onChange={onChange} today={today} />)

    fireEvent.change(screen.getByLabelText('Year'), { target: { value: '2025' } })
    expect(onChange).toHaveBeenLastCalledWith('2025')

    rerender(<StatusPeriodSelector value="2026-04" onChange={onChange} today={today} />)
    expect(screen.getByLabelText('Year')).toHaveValue('2026')
    fireEvent.change(screen.getByLabelText('Month'), { target: { value: '11' } })
    expect(onChange).toHaveBeenLastCalledWith('2026-11')
  })

  it('back to all time', () => {
    const onChange = vi.fn()
    render(<StatusPeriodSelector value="2026-04" onChange={onChange} today={today} />)

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'all' } })

    expect(onChange).toHaveBeenCalledWith('all')
  })
})
