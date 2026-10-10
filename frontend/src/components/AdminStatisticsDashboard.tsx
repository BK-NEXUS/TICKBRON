import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { SegmentedControl } from './SegmentedControl'
import { adminAdapter, RegistrationStatistics } from '../adapters/adminAdapter'
import { TopBookersLeaderboard } from './TopBookersLeaderboard'

type StatisticsView = 'rolling_12_months' | 'calendar_year'

export function AdminStatisticsDashboard() {
  const { t, tp } = useI18n()
  const [currentView, setCurrentView] = useState<StatisticsView>('rolling_12_months')
  const [statistics, setStatistics] = useState<RegistrationStatistics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStatistics()
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setError(t('admin.failedToLoadStatistics'))
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
        <h2 className="admin-view-title">{t('admin.statisticsDashboard')}</h2>
        <p className="admin-view-subtitle">{t('admin.registrationTrendsAndCustomer')}</p>
      </div>

      <div className="statistics-controls">
        <SegmentedControl<StatisticsView>
          aria-label={t('admin.statisticsView')}
          value={currentView}
          onChange={setCurrentView}
          options={[
            { value: 'rolling_12_months', label: t('admin.rolling12') },
            { value: 'calendar_year', label: t('admin.calendarYear') },
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
            {currentView === 'rolling_12_months' ? t('admin.newRegsRolling') : t('admin.newRegsByYear')}
          </h2>

          {loading ? (
            <div className="loading-state" role="status" aria-live="polite">
              {t('admin.loadingStatistics')}
            </div>
          ) : !statistics || statistics.data.length === 0 ? (
            <div className="empty-state">
              <p>{t('admin.noRegistrationDataAvailable')}</p>
            </div>
          ) : (
            <div className="chart-container">
              <div className="bar-chart" role="img" aria-label={t('admin.chartLabel', { count: statistics.data.length })}>
                {statistics.data.map((item, index) => {
                  const maxCount = getMaxCount()
                  const barHeight = maxCount > 0 ? (item.count / maxCount) * 100 : 0
                  
                  return (
                    <div key={index} className="bar-chart-item">
                      <div className="bar-container">
                        <div 
                          className="bar" 
                          style={{ height: `${barHeight}%` }}
                          title={tp('admin.registrationsCount', item.count)}
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
