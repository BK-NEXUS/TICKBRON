import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { StatusReconciliationBlock } from './StatusReconciliationBlock'
import { StatusStayedNote } from './StatusStayedNote'
import { RECONCILIATION } from '../test/statusFixtures'

describe('StatusReconciliationBlock', () => {
  it('lists today, week, month, year and all time with counted and stayed guests and bookings', () => {
    render(<StatusReconciliationBlock reconciliation={RECONCILIATION} today={new Date(2026, 9, 7)} />)

    const table = screen.getByRole('table', { name: 'Reconciliation' })
    const rows = within(table).getAllByRole('row')
    expect(rows).toHaveLength(6)
    expect(within(rows[1]).getByText('Today')).toBeInTheDocument()
    expect(within(rows[2]).getByText('This week')).toBeInTheDocument()
    expect(within(rows[3]).getByText('This month')).toBeInTheDocument()
    expect(within(rows[4]).getByText('This year')).toBeInTheDocument()
    expect(within(rows[5]).getByText('All time')).toBeInTheDocument()

    const cells = within(rows[2]).getAllByRole('cell').map(cell => cell.textContent)
    expect(cells).toEqual(['This week', '2026-10-05 – 2026-10-11', '20', '41', '12', '25'])
    expect(within(rows[5]).getAllByRole('cell')[1]).toHaveTextContent('—')
  })

  it('has labelled headers for counted and stayed', () => {
    render(<StatusReconciliationBlock reconciliation={RECONCILIATION} today={new Date(2026, 9, 7)} />)
    const headers = screen.getAllByRole('columnheader').map(header => header.textContent)
    expect(headers).toEqual(['Window', 'Dates', 'Counted bookings', 'Counted guests', 'Stayed bookings', 'Stayed guests'])
  })

  it('always carries the "may still change" note', () => {
    render(<StatusReconciliationBlock reconciliation={RECONCILIATION} today={new Date(2026, 9, 7)} />)
    expect(screen.getByRole('note')).toHaveTextContent('can still change')
  })
})

describe('StatusStayedNote', () => {
  const today = new Date(2026, 9, 7)

  it('names the window from the contract', () => {
    render(<StatusStayedNote today={today} />)
    expect(screen.getByRole('note')).toHaveTextContent(
      'The "stayed" numbers of the last 7 days can still change: hotels may report no-shows for 7 days after check-out.')
  })

  it('shows for all time and for periods that reach the last 7 days', () => {
    const { rerender } = render(<StatusStayedNote periodRange={{ from: null, to: null }} today={today} />)
    expect(screen.getByRole('note')).toBeInTheDocument()

    rerender(<StatusStayedNote periodRange={{ from: '2026-10-01', to: '2026-10-07' }} today={today} />)
    expect(screen.getByRole('note')).toBeInTheDocument()

    rerender(<StatusStayedNote periodRange={{ from: '2026-09-01', to: '2026-09-30' }} today={today} />)
    expect(screen.getByRole('note')).toBeInTheDocument()
  })

  it('is hidden for a period that ended before the window', () => {
    render(<StatusStayedNote periodRange={{ from: '2026-01-01', to: '2026-09-29' }} today={today} />)
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })
})
