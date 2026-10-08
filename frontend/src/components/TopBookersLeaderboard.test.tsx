import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { TopBookersLeaderboard } from './TopBookersLeaderboard'
import { adminAdapter } from '../adapters/adminAdapter'
import { settle } from '../test/utils'

// Mock the admin adapter
vi.mock('../adapters/adminAdapter', () => ({
  adminAdapter: {
    getTopBookers: vi.fn(),
  },
}))

describe('TopBookersLeaderboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the leaderboard', async () => {
    render(<TopBookersLeaderboard />)
    await settle()

    expect(screen.getByText('Top Bookers Leaderboard')).toBeInTheDocument()
    expect(screen.getByText('All Time')).toBeInTheDocument()
  })

  it('should display loading state while fetching data', async () => {
    ;(adminAdapter.getTopBookers as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<TopBookersLeaderboard />)

    await waitFor(() => {
      expect(screen.getByText('Loading leaderboard...')).toBeInTheDocument()
    })
  })

  it('should display empty state when no data available', async () => {
    ;(adminAdapter.getTopBookers as any).mockResolvedValue({
      data: [],
      error: null,
    })

    render(<TopBookersLeaderboard />)

    await waitFor(() => {
      expect(screen.getByText('No booking data available for this period.')).toBeInTheDocument()
    })
  })

  it('should display top bookers when data is available', async () => {
    const mockTopBookers = [
      {
        rank: 1,
        customer_id: 1,
        customer_name: 'John Doe',
        completed_booking_count: 15,
      },
      {
        rank: 2,
        customer_id: 2,
        customer_name: 'Jane Smith',
        completed_booking_count: 12,
      },
    ]

    ;(adminAdapter.getTopBookers as any).mockResolvedValue({
      data: mockTopBookers,
      error: null,
    })

    render(<TopBookersLeaderboard />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
      expect(screen.getByText('15')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
    })
  })

  it('should display medal emojis for top 3 positions', async () => {
    const mockTopBookers = [
      {
        rank: 1,
        customer_id: 1,
        customer_name: 'John Doe',
        completed_booking_count: 15,
      },
      {
        rank: 2,
        customer_id: 2,
        customer_name: 'Jane Smith',
        completed_booking_count: 12,
      },
      {
        rank: 3,
        customer_id: 3,
        customer_name: 'Bob Johnson',
        completed_booking_count: 10,
      },
    ]

    ;(adminAdapter.getTopBookers as any).mockResolvedValue({
      data: mockTopBookers,
      error: null,
    })

    render(<TopBookersLeaderboard />)

    await waitFor(() => {
      expect(screen.getByRole('img', { name: 'Rank 1' })).toBeInTheDocument()
      expect(screen.getByRole('img', { name: 'Rank 2' })).toBeInTheDocument()
      expect(screen.getByRole('img', { name: 'Rank 3' })).toBeInTheDocument()
    })
  })

  it('should display rank number for positions beyond 3', async () => {
    const mockTopBookers = [
      {
        rank: 4,
        customer_id: 4,
        customer_name: 'Alice Brown',
        completed_booking_count: 8,
      },
    ]

    ;(adminAdapter.getTopBookers as any).mockResolvedValue({
      data: mockTopBookers,
      error: null,
    })

    render(<TopBookersLeaderboard />)

    await waitFor(() => {
      expect(screen.getByText('#4')).toBeInTheDocument()
    })
  })

  it('should display error message when API call fails', async () => {
    ;(adminAdapter.getTopBookers as any).mockResolvedValue({
      data: null,
      error: 'Failed to load top bookers',
    })

    render(<TopBookersLeaderboard />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load top bookers')).toBeInTheDocument()
    })
  })

  it('should display correct period label for this_month', async () => {
    render(<TopBookersLeaderboard period="this_month" />)
    await settle()

    expect(screen.getByText('This Month')).toBeInTheDocument()
  })

  it('should display correct period label for this_year', async () => {
    render(<TopBookersLeaderboard period="this_year" />)
    await settle()

    expect(screen.getByText('This Year')).toBeInTheDocument()
  })
})
