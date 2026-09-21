import { useAuth } from '../contexts/AuthContext'
import { EmptyState } from '../components/EmptyState'
import { Link } from 'react-router-dom'

export function ProfilePage() {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated || !user) {
    return (
      <div className="profile-page">
        <div className="container">
          <EmptyState
            icon="🔒"
            title="Sign in required"
            message="Please sign in to view your profile."
            ctaText="Sign In"
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="profile-page">
      <div className="container">
        <div className="profile-content">
          <div className="profile-header">
            <div className="profile-avatar">
              {user.first_name ? (
                <span className="profile-avatar-initials">
                  {user.first_name.charAt(0)}{user.last_name ? user.last_name.charAt(0) : ''}
                </span>
              ) : (
                <span className="profile-avatar-initials">U</span>
              )}
            </div>
            <div className="profile-info">
              <h1 className="profile-name">{user.full_name || user.email}</h1>
              <p className="profile-email">{user.email}</p>
              <div className="profile-status">
                <span className={`profile-status-badge ${user.is_active ? 'profile-status-badge--active' : 'profile-status-badge--inactive'}`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
                {user.email_verified && (
                  <span className="profile-status-badge profile-status-badge--verified">
                    Verified
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="profile-details">
            <div className="profile-section">
              <h2 className="profile-section-title">Personal Information</h2>
              <div className="profile-field">
                <label className="profile-field-label">First Name</label>
                <p className="profile-field-value">{user.first_name || 'Not provided'}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">Last Name</label>
                <p className="profile-field-value">{user.last_name || 'Not provided'}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">Email</label>
                <p className="profile-field-value">{user.email}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">Phone Number</label>
                <p className="profile-field-value">{user.phone_number || 'Not provided'}</p>
              </div>
            </div>

            <div className="profile-section">
              <h2 className="profile-section-title">Account Information</h2>
              <div className="profile-field">
                <label className="profile-field-label">Member Since</label>
                <p className="profile-field-value">
                  {user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'Unknown'}
                </p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">Last Login</label>
                <p className="profile-field-value">
                  {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                </p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">Two-Factor Authentication</label>
                <p className="profile-field-value">
                  {user.two_factor_enabled ? 'Enabled' : 'Disabled'}
                </p>
              </div>
            </div>

            <div className="profile-section">
              <h2 className="profile-section-title">Quick Links</h2>
              <div className="profile-links">
                <Link to="/bookings" className="profile-link">
                  <span className="profile-link-icon">📅</span>
                  <span className="profile-link-text">My Bookings</span>
                </Link>
                <Link to="/favorites" className="profile-link">
                  <span className="profile-link-icon">❤️</span>
                  <span className="profile-link-text">My Favorites</span>
                </Link>
                <Link to="/partner" className="profile-link">
                  <span className="profile-link-icon">🏠</span>
                  <span className="profile-link-text">Partner Dashboard</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
