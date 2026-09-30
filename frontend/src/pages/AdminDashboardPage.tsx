import { useState, useEffect } from 'react'
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
            icon="🔒"
            title="Authentication required"
            message="Please sign in to access the admin dashboard."
            ctaText="Sign In"
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
            icon="🚫"
            title="Access Denied"
            message="You do not have permission to access the admin dashboard."
            ctaText="Go to Home"
            ctaLink="/"
          />
        </div>
      </div>
    )
  }

  const renderNavigation = () => (
    <nav className="admin-dashboard-nav" aria-label="Admin dashboard navigation">
      <button
        onClick={() => setCurrentView('properties')}
        className={`nav-item ${currentView === 'properties' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'properties' ? 'page' : undefined}
      >
        <span className="nav-icon">🏠</span>
        <span className="nav-label">Properties</span>
      </button>
      <button
        onClick={() => setCurrentView('amenities')}
        className={`nav-item ${currentView === 'amenities' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'amenities' ? 'page' : undefined}
      >
        <span className="nav-icon">🛎️</span>
        <span className="nav-label">Amenities</span>
      </button>
      <button
        onClick={() => setCurrentView('users')}
        className={`nav-item ${currentView === 'users' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'users' ? 'page' : undefined}
      >
        <span className="nav-icon">👥</span>
        <span className="nav-label">Users</span>
      </button>
      <button
        onClick={() => setCurrentView('customers')}
        className={`nav-item ${currentView === 'customers' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'customers' ? 'page' : undefined}
      >
        <span className="nav-icon">👤</span>
        <span className="nav-label">Customers</span>
      </button>
      <button
        onClick={() => setCurrentView('statistics')}
        className={`nav-item ${currentView === 'statistics' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'statistics' ? 'page' : undefined}
      >
        <span className="nav-icon">📊</span>
        <span className="nav-label">Statistics</span>
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
        <span className="nav-label">Status</span>
      </button>
      <button
        onClick={() => navigate('/admin/support')}
        className="nav-item"
      >
        <span className="nav-icon">🔍</span>
        <span className="nav-label">Support Lookup</span>
      </button>
      {user.is_superuser && (
        <button
          onClick={() => setShowCreateOwner(true)}
          className={`nav-item ${showCreateOwner ? 'nav-item--active' : ''}`}
          aria-current={showCreateOwner ? 'page' : undefined}
        >
          <span className="nav-icon">➕</span>
          <span className="nav-label">Create Owner</span>
        </button>
      )}
    </nav>
  )

  const renderBreadcrumb = () => {
    const breadcrumbs: Array<{ label: string; onClick: () => void; active: boolean }> = []

    if (showCreateOwner) {
      breadcrumbs.push({ label: 'Create Hotel Owner', onClick: () => {}, active: true })
    } else {
      switch (currentView) {
        case 'properties':
          breadcrumbs.push({ label: 'Property Moderation', onClick: () => {}, active: true })
          break
        case 'amenities':
          breadcrumbs.push({ label: 'Amenity Management', onClick: () => {}, active: true })
          break
        case 'users':
          breadcrumbs.push({ label: 'User Management', onClick: () => {}, active: true })
          break
        case 'customers':
          breadcrumbs.push({ label: 'Customers Directory', onClick: () => {}, active: true })
          break
        case 'statistics':
          breadcrumbs.push({ label: 'Statistics Dashboard', onClick: () => {}, active: true })
          break
        case 'status':
          breadcrumbs.push({ label: 'Status', onClick: () => {}, active: true })
          break
      }
    }

    return (
      <nav className="breadcrumb" aria-label="Breadcrumb">
        {breadcrumbs.map((crumb, index) => (
          <span key={index} className="breadcrumb-item">
            {index > 0 && <span className="breadcrumb-separator">/</span>}
            {crumb.active ? (
              <span className="breadcrumb-current">{crumb.label}</span>
            ) : (
              <button onClick={crumb.onClick} className="breadcrumb-link">
                {crumb.label}
              </button>
            )}
          </span>
        ))}
      </nav>
    )
  }

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
      <div className="container">
        <div className="dashboard-header">
          <h1 className="dashboard-title">Admin Dashboard</h1>
          <p className="dashboard-subtitle">
            Welcome, {user.first_name || user.email}
            {user.is_superuser && <span className="role-badge role-badge--super-admin">Super Admin</span>}
            {user.is_staff && !user.is_superuser && <span className="role-badge role-badge--staff">Staff</span>}
          </p>
        </div>

        {renderNavigation()}
        {renderBreadcrumb()}

        <div className="dashboard-content">
          {renderCurrentView()}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboardPage
