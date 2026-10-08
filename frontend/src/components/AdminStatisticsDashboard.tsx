import { useState, useEffect } from 'react'
import { SegmentedControl } from './SegmentedControl'
import { adminAdapter, RegistrationStatistics } from '../adapters/adminAdapter'
import { TopBookersLeaderboard } from './TopBookersLeaderboard'

type StatisticsView = 'rolling_12_months' | 'calendar_year'

export function AdminStatisticsDashboard() {
  const [currentView, setCurrentView] = useState<StatisticsView>('rolling_12_months')
  const [statistics, setStatistics] = useState<RegistrationStatistics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStatistics()
  }, [currentView])

  const loadStatistics = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await adminAdapter.getRegistrationStatistics({ type: currentView })
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setStatistics(response.data)
      }
    } catch (err) {
      setError('Failed to load statistics. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getMaxCount = () => {
    if (!statistics?.data || statistics.data.length === 0) return 0
    return Math.max(...statistics.data.map(d => d.count))
  }

  const formatPeriodLabel = (period: string) => {
    if (currentView === 'rolling_12_months') {
      const date = new Date(period)
      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
    } else {
      return period
    }
  }

  return (
    <div className="admin-statistics-dashboard">
      <div className="admin-view-header">
        <h1 className="admin-view-title">Statistics Dashboard</h1>
        <p className="admin-view-subtitle">Registration trends and customer insights</p>
      </div>

      <div className="statistics-controls">
        <SegmentedControl<StatisticsView>
          aria-label="Statistics view"
          value={currentView}
          onChange={setCurrentView}
          options={[
            { value: 'rolling_12_months', label: 'Rolling 12 Months' },
            { value: 'calendar_year', label: 'Calendar Year' },
          ]}
        />
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      <div className="statistics-content">
        <div className="statistics-section">
          <h2 className="statistics-section-title">
            {currentView === 'rolling_12_months' ? 'New Registrations (Rolling 12 Months)' : 'New Registrations by Year'}
          </h2>

          {loading ? (
            <div className="loading-state" role="status" aria-live="polite">
              Loading statistics...
            </div>
          ) : !statistics || statistics.data.length === 0 ? (
            <div className="empty-state">
              <p>No registration data available.</p>
            </div>
          ) : (
            <div className="chart-container">
              <div className="bar-chart" role="img" aria-label={`Registration chart showing ${statistics.data.length} data points`}>
                {statistics.data.map((item, index) => {
                  const maxCount = getMaxCount()
                  const barHeight = maxCount > 0 ? (item.count / maxCount) * 100 : 0
                  
                  return (
                    <div key={index} className="bar-chart-item">
                      <div className="bar-container">
                        <div 
                          className="bar" 
                          style={{ height: `${barHeight}%` }}
                          title={`${item.count} registrations`}
                        >
                          <span className="bar-label">{item.count}</span>
                        </div>
                      </div>
                      <div className="bar-period">{formatPeriodLabel(item.period)}</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        <div className="statistics-section">
          {/* TopBookersLeaderboard renders its own "Top Bookers Leaderboard" heading */}
          <TopBookersLeaderboard period="all_time" limit={10} />
        </div>
      </div>
    </div>
  )
}
