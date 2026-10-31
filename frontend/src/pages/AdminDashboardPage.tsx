import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { Lock, Ban, House, Bell, Users, User, ChartColumn, Search, Plus, Megaphone, MessageSquare, UserX, MapPin, Coins, Star, Percent } from 'lucide-react'
import { useNavigate } from 'react-router'
import { useAuth } from '../contexts/AuthContext'
import { AdminPropertyModeration } from '../components/AdminPropertyModeration'
import { AdminAmenityManagement } from '../components/AdminAmenityManagement'
import { AdminUserManagement } from '../components/AdminUserManagement'
import { AdminCustomersList } from '../components/AdminCustomersList'
import { AdminStatisticsDashboard } from '../components/AdminStatisticsDashboard'
import { AdminStatusSection } from '../components/AdminStatusSection'
import { AdminPromotions } from '../components/AdminPromotions'
import { AdminCommission } from '../components/AdminCommission'
import { AdminSupportChat } from '../components/AdminSupportChat'
import { useChatUnread } from '../hooks/useChatUnread'
import { AdminNoShowReports } from '../components/AdminNoShowReports'
import { AdminGeography } from '../components/AdminGeography'
import { AdminExchangeRates } from '../components/AdminExchangeRates'
import { AdminReviewModeration } from '../components/AdminReviewModeration'
import { CreateHotelOwnerAccount } from '../components/CreateHotelOwnerAccount'
import { EmptyState } from '../components/EmptyState'

type AdminView = 'properties' | 'reviews' | 'amenities' | 'users' | 'customers' | 'statistics' | 'status' | 'promotions' | 'messages' | 'no-show' | 'geography' | 'rates' | 'commission' | 'create-owner'

export function AdminDashboardPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuth()
  const waiting = useChatUnread(Boolean(user?.is_staff || user?.is_superuser), true)
  const [currentView, setCurrentView] = useState<AdminView>('properties')
  // The account form in the main area: a hotel owner, an administrator, or none
  const [creating, setCreating] = useState<'owner' | 'admin' | null>(null)

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
    setCreating(null)
    setCurrentView('users')
  }

  const handleCreateOwnerCancel = () => {
    setCreating(null)
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="admin-dashboard-page">
        <div className="container">
          <EmptyState
            headingLevel={1}
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
            headingLevel={1}
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
        onClick={() => setCurrentView('promotions')}
        className={`nav-item ${currentView === 'promotions' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'promotions' ? 'page' : undefined}
      >
        <span className="nav-icon"><Megaphone size={18} aria-hidden="true" /></span>
        <span className="nav-label">{t('promoAdmin.nav')}</span>
      </button>
      <button
        onClick={() => setCurrentView('reviews')}
        className={`nav-item ${currentView === 'reviews' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'reviews' ? 'page' : undefined}
      >
        <span className="nav-icon"><Star size={18} aria-hidden="true" /></span>
        <span className="nav-label">{t('reviewAdmin.nav')}</span>
      </button>
      <button
        onClick={() => setCurrentView('messages')}
        className={`nav-item ${currentView === 'messages' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'messages' ? 'page' : undefined}
      >
        <span className="nav-icon"><MessageSquare size={18} aria-hidden="true" /></span>
        <span className="nav-label">{t('chat.admin.nav')}</span>
        {waiting.count > 0 && <span className="chat-badge" aria-label={t('chat.admin.unreadCount', { count: waiting.count })}>{waiting.count}</span>}
      </button>
      <button
        onClick={() => setCurrentView('no-show')}
        className={`nav-item ${currentView === 'no-show' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'no-show' ? 'page' : undefined}
      >
        <span className="nav-icon"><UserX size={18} aria-hidden="true" /></span>
        <span className="nav-label">{t('noShowAdmin.nav')}</span>
      </button>
      <button
        onClick={() => setCurrentView('commission')}
        className={`nav-item ${currentView === 'commission' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'commission' ? 'page' : undefined}
      >
        <span className="nav-icon"><Percent size={18} aria-hidden="true" /></span>
        <span className="nav-label">{t('commission.nav')}</span>
      </button>
      <button
        onClick={() => setCurrentView('rates')}
        className={`nav-item ${currentView === 'rates' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'rates' ? 'page' : undefined}
      >
        <span className="nav-icon"><Coins size={18} aria-hidden="true" /></span>
        <span className="nav-label">{t('fxAdmin.nav')}</span>
      </button>
      {user.is_superuser && (
        <button
          onClick={() => setCurrentView('geography')}
          className={`nav-item ${currentView === 'geography' ? 'nav-item--active' : ''}`}
          aria-current={currentView === 'geography' ? 'page' : undefined}
        >
          <span className="nav-icon"><MapPin size={18} aria-hidden="true" /></span>
          <span className="nav-label">{t('geoAdmin.nav')}</span>
        </button>
      )}
      <button
        onClick={() => navigate('/admin/support')}
        className="nav-item"
      >
        <span className="nav-icon"><Search size={18} /></span>
        <span className="nav-label">{t('crumb.supportLookup')}</span>
      </button>
      {user.is_superuser && (['owner', 'admin'] as const).map(kind => (
        <button
          key={kind}
          onClick={() => setCreating(kind)}
          className={`nav-item ${creating === kind ? 'nav-item--active' : ''}`}
          aria-current={creating === kind ? 'page' : undefined}
        >
          <span className="nav-icon"><Plus size={18} /></span>
          <span className="nav-label">{t(kind === 'owner' ? 'admin.createOwner' : 'admin.createAdmin')}</span>
        </button>
      ))}
    </nav>
  )

  const renderCurrentView = () => {
    if (creating) {
      return (
        <div className="admin-create-owner-view">
          <CreateHotelOwnerAccount
            kind={creating}
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
      case 'no-show':
        return <AdminNoShowReports />
      case 'geography':
        return user.is_superuser ? <AdminGeography /> : <AdminPropertyModeration />
      case 'reviews':
        return <AdminReviewModeration />
      case 'rates':
        return <AdminExchangeRates isSuperAdmin={Boolean(user.is_superuser)} />
      case 'commission':
        return <AdminCommission isSuperAdmin={Boolean(user.is_superuser)} />
      case 'promotions':
        return <AdminPromotions isSuperAdmin={Boolean(user.is_superuser)} />
      case 'messages':
        return <AdminSupportChat onSeen={waiting.refresh} />
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

        <div className="dashboard-layout">
          {renderNavigation()}

          <div className="dashboard-content">
            {renderCurrentView()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminDashboardPage
