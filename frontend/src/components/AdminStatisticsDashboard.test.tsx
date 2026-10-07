import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AdminStatisticsDashboard } from './AdminStatisticsDashboard'
import { adminAdapter } from '../adapters/adminAdapter'
import { settle } from '../test/utils'

// Mock the admin adapter
vi.mock('../adapters/adminAdapter', () => ({
  adminAdapter: {
    getRegistrationStatistics: vi.fn(),
  },
}))

describe('AdminStatisticsDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the statistics dashboard', async () => {
    render(<AdminStatisticsDashboard />)
    await settle()

    expect(screen.getByText('Statistics Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Registration trends and customer insights')).toBeInTheDocument()
  })

  it('should show rolling 12 months view by default', async () => {
    render(<AdminStatisticsDashboard />)
    await settle()

    expect(screen.getByText('Rolling 12 Months')).toBeInTheDocument()
    expect(screen.getByText('Calendar Year')).toBeInTheDocument()
  })

  it('should toggle between rolling 12 months and calendar year views', async () => {
    render(<AdminStatisticsDashboard />)

    const calendarYearButton = screen.getByText('Calendar Year')
    fireEvent.click(calendarYearButton)

    await waitFor(() => {
      expect(screen.getByText('New Registrations by Year')).toBeInTheDocument()
    })
    // Let the page finish loading inside the test
    await settle()
  })

  it('should display loading state while fetching statistics', async () => {
    ;(adminAdapter.getRegistrationStatistics as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<AdminStatisticsDashboard />)

    await waitFor(() => {
      expect(screen.getByText('Loading statistics...')).toBeInTheDocument()
    })
  })

  it('should display empty state when no data available', async () => {
    ;(adminAdapter.getRegistrationStatistics as any).mockResolvedValue({
      data: { type: 'rolling_12_months', data: [] },
      error: null,
    })

    render(<AdminStatisticsDashboard />)

    await waitFor(() => {
      expect(screen.getByText('No registration data available.')).toBeInTheDocument()
    })
  })

  it('should display statistics chart when data is available', async () => {
    const mockStatistics = {
      type: 'rolling_12_months',
      data: [
        { period: '2024-01', count: 15 },
        { period: '2024-02', count: 23 },
        { period: '2024-03', count: 18 },
      ],
    }

    ;(adminAdapter.getRegistrationStatistics as any).mockResolvedValue({
      data: mockStatistics,
      error: null,
    })

    render(<AdminStatisticsDashboard />)

    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument()
      expect(screen.getByText('23')).toBeInTheDocument()
      expect(screen.getByText('18')).toBeInTheDocument()
    })
  })

  it('should display error message when API call fails', async () => {
    ;(adminAdapter.getRegistrationStatistics as any).mockResolvedValue({
      data: null,
      error: 'Failed to load statistics',
    })

    render(<AdminStatisticsDashboard />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load statistics')).toBeInTheDocument()
    })
  })

  it('should render top bookers leaderboard section', async () => {
    render(<AdminStatisticsDashboard />)
    await settle()

    expect(screen.getByText('Top Bookers Leaderboard')).toBeInTheDocument()
  })
})
