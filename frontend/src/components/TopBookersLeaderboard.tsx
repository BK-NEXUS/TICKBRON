import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { Medal } from 'lucide-react'
import { adminAdapter, TopBooker } from '../adapters/adminAdapter'

interface TopBookersLeaderboardProps {
  period?: 'this_month' | 'this_year' | 'all_time'
  limit?: number
}

export function TopBookersLeaderboard({ period = 'all_time', limit = 10 }: TopBookersLeaderboardProps) {
  const { t } = useI18n()
  const [topBookers, setTopBookers] = useState<TopBooker[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTopBookers()
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setError(t('admin.failedToLoadTop'))
    } finally {
      setLoading(false)
    }
  }

  const getPeriodLabel = () => {
    switch (period) {
      case 'this_month':
        return t('admin.periodThisMonth')
      case 'this_year':
        return t('admin.periodThisYear')
      case 'all_time':
      default:
        return t('admin.periodAllTime')
    }
  }

  const getRankBadge = (rank: number) => {
    if (rank > 3) return `#${rank}`
    return <Medal size={20} className={`rank-medal rank-medal--${rank}`} aria-label={t('admin.rankLabel', { rank })} role="img" />
  }

  return (
    <div className="top-bookers-leaderboard">
      <div className="leaderboard-header">
        <h2 className="leaderboard-title">{t('admin.topBookersLeaderboard')}</h2>
        <span className="leaderboard-period">{getPeriodLabel()}</span>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          {t('admin.loadingLeaderboard')}
        </div>
      ) : topBookers.length === 0 ? (
        <div className="empty-state">
          <p>{t('admin.noBookingDataAvailable')}</p>
        </div>
      ) : (
        <div className="leaderboard-table-container">
          <table className="leaderboard-table" role="table">
            <thead>
              <tr>
                <th scope="col">{t('admin.rank')}</th>
                <th scope="col">{t('crumb.customer')}</th>
                <th scope="col">{t('admin.completedBookings')}</th>
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
