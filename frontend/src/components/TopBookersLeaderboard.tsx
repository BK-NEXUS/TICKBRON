import { useState, useEffect } from 'react'
import { Medal } from 'lucide-react'
import { adminAdapter, TopBooker } from '../adapters/adminAdapter'

interface TopBookersLeaderboardProps {
  period?: 'this_month' | 'this_year' | 'all_time'
  limit?: number
}

export function TopBookersLeaderboard({ period = 'all_time', limit = 10 }: TopBookersLeaderboardProps) {
  const [topBookers, setTopBookers] = useState<TopBooker[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTopBookers()
  }, [period, limit])

  const loadTopBookers = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await adminAdapter.getTopBookers({ period, limit })
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setTopBookers(response.data)
      }
    } catch (err) {
      setError('Failed to load top bookers. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getPeriodLabel = () => {
    switch (period) {
      case 'this_month':
        return 'This Month'
      case 'this_year':
        return 'This Year'
      case 'all_time':
      default:
        return 'All Time'
    }
  }

  const getRankBadge = (rank: number) => {
    if (rank > 3) return `#${rank}`
    return <Medal size={20} className={`rank-medal rank-medal--${rank}`} aria-label={`Rank ${rank}`} role="img" />
  }

  return (
    <div className="top-bookers-leaderboard">
      <div className="leaderboard-header">
        <h2 className="leaderboard-title">Top Bookers Leaderboard</h2>
        <span className="leaderboard-period">{getPeriodLabel()}</span>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          Loading leaderboard...
        </div>
      ) : topBookers.length === 0 ? (
        <div className="empty-state">
          <p>No booking data available for this period.</p>
        </div>
      ) : (
        <div className="leaderboard-table-container">
          <table className="leaderboard-table" role="table">
            <thead>
              <tr>
                <th scope="col">Rank</th>
                <th scope="col">Customer</th>
                <th scope="col">Completed Bookings</th>
              </tr>
            </thead>
            <tbody>
              {topBookers.map((booker) => (
                <tr key={booker.customer_id}>
                  <td className="rank-cell">
                    <span className="rank-badge">{getRankBadge(booker.rank)}</span>
                  </td>
                  <td className="customer-cell">{booker.customer_name}</td>
                  <td className="bookings-cell">{booker.completed_booking_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
