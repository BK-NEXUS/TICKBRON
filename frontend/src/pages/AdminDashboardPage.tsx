import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { Lock, Ban, House, Bell, Users, User, ChartColumn, Search, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { AdminPropertyModeration } from '../components/AdminPropertyModeration'
import { AdminAmenityManagement } from '../components/AdminAmenityManagement'
import { AdminUserManagement } from '../components/AdminUserManagement'
import { AdminCustomersList } from '../components/AdminCustomersList'
import { AdminStatisticsDashboard } from '../components/AdminStatisticsDashboard'
import { AdminStatusSection } from '../components/AdminStatusSection'
import { CreateHotelOwnerAccount } from '../components/CreateHotelOwnerAccount'
import { EmptyState } from '../components/EmptyState'

type AdminView = 'properties' | 'amenities' | 'users' | 'customers' | 'statistics' | 'status' | 'create-owner'

export function AdminDashboardPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuth()
  const [currentView, setCurrentView] = useState<AdminView>('properties')
  const [showCreateOwner, setShowCreateOwner] = useState(false)

  useEffect(() => {
    if (isAuthenticated && user) {
      // Check if user is super-admin or staff
      if (!user.is_staff && !user.is_superuser) {
        // Non-admin users should not access this page
        // They will be redirected by the route protection
      }
    }
  }, [isAuthenticated, user])

  const handleCreateOwnerSuccess = () => {
    setShowCreateOwner(false)
    setCurrentView('users')
  }

  const handleCreateOwnerCancel = () => {
    setShowCreateOwner(false)
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="admin-dashboard-page">
        <div className="container">
          <EmptyState
            icon={<Lock size={40} />}
            title={t('partner.authenticationRequired')}
            message={t('admin.pleaseSignInTo')}
            ctaText={t('auth.signIn')}
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  // UI permission boundaries - but never rely on frontend authorization alone
  // Backend enforces actual permissions via 403 responses
  if (!user.is_staff && !user.is_superuser) {
    return (
      <div className="admin-dashboard-page">
        <div className="container">
          <EmptyState
            icon={<Ban size={40} />}
            title={t('denied.title')}
            message={t('admin.youDoNotHave')}
            ctaText={t('admin.goToHome')}
            ctaLink="/"
          />
        </div>
      </div>
    )
  }

  const renderNavigation = () => (
    <nav className="admin-dashboard-nav" aria-label={t('admin.adminDashboardNavigation')}>
      <button
        onClick={() => setCurrentView('properties')}
        className={`nav-item ${currentView === 'properties' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'properties' ? 'page' : undefined}
      >
        <span className="nav-icon"><House size={18} /></span>
        <span className="nav-label">{t('nav.properties')}</span>
      </button>
      <button
        onClick={() => setCurrentView('amenities')}
        className={`nav-item ${currentView === 'amenities' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'amenities' ? 'page' : undefined}
      >
        <span className="nav-icon"><Bell size={18} /></span>
        <span className="nav-label">{t('filters.amenities')}</span>
      </button>
      <button
        onClick={() => setCurrentView('users')}
        className={`nav-item ${currentView === 'users' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'users' ? 'page' : undefined}
      >
        <span className="nav-icon"><Users size={18} /></span>
        <span className="nav-label">{t('status.users')}</span>
      </button>
      <button
        onClick={() => setCurrentView('customers')}
        className={`nav-item ${currentView === 'customers' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'customers' ? 'page' : undefined}
      >
        <span className="nav-icon"><User size={18} /></span>
        <span className="nav-label">{t('admin.customers')}</span>
      </button>
      <button
        onClick={() => setCurrentView('statistics')}
        className={`nav-item ${currentView === 'statistics' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'statistics' ? 'page' : undefined}
      >
        <span className="nav-icon"><ChartColumn size={18} /></span>
        <span className="nav-label">{t('status.statistics')}</span>
      </button>
      <button
        onClick={() => setCurrentView('status')}
        className={`nav-item ${currentView === 'status' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'status' ? 'page' : undefined}
      >
        <span className="nav-icon" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" focusable="false">
            <rect x="1" y="9" width="3" height="6" rx="0.5" />
            <rect x="6.5" y="5" width="3" height="10" rx="0.5" />
            <rect x="12" y="1" width="3" height="14" rx="0.5" />
          </svg>
        </span>
        <span className="nav-label">{t('partner.status')}</span>
      </button>
      <button
        onClick={() => navigate('/admin/support')}
        className="nav-item"
      >
        <span className="nav-icon"><Search size={18} /></span>
        <span className="nav-label">{t('crumb.supportLookup')}</span>
      </button>
      {user.is_superuser && (
        <button
          onClick={() => setShowCreateOwner(true)}
          className={`nav-item ${showCreateOwner ? 'nav-item--active' : ''}`}
          aria-current={showCreateOwner ? 'page' : undefined}
        >
          <span className="nav-icon"><Plus size={18} /></span>
          <span className="nav-label">{t('admin.createOwner')}</span>
        </button>
      )}
    </nav>
  )

  const renderCurrentView = () => {
    if (showCreateOwner) {
      return (
        <div className="admin-create-owner-view">
          <CreateHotelOwnerAccount
            onSuccess={handleCreateOwnerSuccess}
            onCancel={handleCreateOwnerCancel}
          />
        </div>
      )
    }

    switch (currentView) {
      case 'properties':
        return <AdminPropertyModeration />
      case 'amenities':
        return <AdminAmenityManagement />
      case 'users':
        return <AdminUserManagement />
      case 'customers':
        return <AdminCustomersList />
      case 'statistics':
        return <AdminStatisticsDashboard />
      case 'status':
        return <AdminStatusSection onExit={() => setCurrentView('properties')} />
      default:
        return <AdminPropertyModeration />
    }
  }

  return (
    <div className="admin-dashboard-page">
      <div className="container container-large-desktop">
        <div className="dashboard-header">
          <h1 className="dashboard-title">{t('header.adminDashboard')}</h1>
          <p className="dashboard-subtitle">
            {t('admin.welcome', { name: user.first_name || user.email })}
            {user.is_superuser && <span className="role-badge role-badge--super-admin">{t('admin.superAdmin')}</span>}
            {user.is_staff && !user.is_superuser && <span className="role-badge role-badge--staff">{t('admin.staff')}</span>}
          </p>
        </div>

        {renderNavigation()}

        <div className="dashboard-content">
          {renderCurrentView()}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboardPage
