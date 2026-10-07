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

  describe('presets and custom range', () => {
    it('offers the preset periods and picks one', () => {
      const onChange = vi.fn()
      render(<StatusPeriodSelector value="all" onChange={onChange} today={today} />)

      const options = Array.from(screen.getByLabelText('Period').querySelectorAll('option'))
        .map(o => (o as HTMLOptionElement).value)
      expect(options).toEqual(
        ['all', 'today', 'last_7_days', 'last_30_days', 'this_year', 'last_5_years', 'last_10_years', 'year', 'month'])

      fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'last_30_days' } })
      expect(onChange).toHaveBeenCalledWith('last_30_days')
    })

    it('a preset shows no year or month field', () => {
      render(<StatusPeriodSelector value="last_7_days" onChange={vi.fn()} today={today} />)
      expect(screen.getByLabelText('Period')).toHaveValue('last_7_days')
      expect(screen.queryByLabelText('Year')).not.toBeInTheDocument()
    })

    it('has no custom option without a range handler', () => {
      render(<StatusPeriodSelector value="all" onChange={vi.fn()} today={today} />)
      expect(screen.queryByRole('option', { name: 'Custom range' })).not.toBeInTheDocument()
    })

    it('choosing custom waits for Apply and sends a valid range', () => {
      const onChange = vi.fn()
      const onRangeChange = vi.fn()
      render(<StatusPeriodSelector value="all" onChange={onChange} onRangeChange={onRangeChange} today={today} />)

      fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'custom' } })
      expect(onChange).not.toHaveBeenCalled()
      expect(onRangeChange).not.toHaveBeenCalled()

      fireEvent.change(screen.getByLabelText('From'), { target: { value: '2026-01-01' } })
      fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-03-01' } })
      fireEvent.click(screen.getByRole('button', { name: 'Apply' }))

      expect(onRangeChange).toHaveBeenCalledWith({ from: '2026-01-01', to: '2026-03-01' })
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })

    it('refuses an invalid range and says why', () => {
      const onRangeChange = vi.fn()
      render(<StatusPeriodSelector value="all" onChange={vi.fn()} onRangeChange={onRangeChange} today={today} />)

      fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'custom' } })
      fireEvent.change(screen.getByLabelText('From'), { target: { value: '2026-03-01' } })
      fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-01-01' } })
      fireEvent.click(screen.getByRole('button', { name: 'Apply' }))

      expect(onRangeChange).not.toHaveBeenCalled()
      expect(screen.getByRole('alert')).toHaveTextContent('"From" must not be after "To".')
      expect(screen.getByLabelText('From')).toHaveAttribute('aria-invalid', 'true')
    })

    it('shows the applied range and leaves custom for a preset', () => {
      const onChange = vi.fn()
      render(
        <StatusPeriodSelector
          value="custom" range={{ from: '2026-01-01', to: '2026-03-01' }}
          onChange={onChange} onRangeChange={vi.fn()} today={today}
        />,
      )
      expect(screen.getByLabelText('Period')).toHaveValue('custom')
      expect(screen.getByLabelText('From')).toHaveValue('2026-01-01')
      expect(screen.getByLabelText('To')).toHaveValue('2026-03-01')

      fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'today' } })
      expect(onChange).toHaveBeenCalledWith('today')
    })
  })
})
