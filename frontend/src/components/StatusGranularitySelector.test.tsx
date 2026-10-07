import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { StatusGranularitySelector } from './StatusGranularitySelector'

describe('StatusGranularitySelector', () => {
  it('offers day, week, month and year and reports the choice', () => {
    const onChange = vi.fn()
    render(<StatusGranularitySelector value="month" onChange={onChange} />)

    const select = screen.getByLabelText('Group by')
    expect(select).toHaveValue('month')
    expect(Array.from(select.querySelectorAll('option')).map(o => (o as HTMLOptionElement).value))
      .toEqual(['day', 'week', 'month', 'year'])

    fireEvent.change(select, { target: { value: 'week' } })
    expect(onChange).toHaveBeenCalledWith('week')
  })
})
