import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { EmptyState } from '../components/EmptyState'
import { Link } from 'react-router-dom'

export function ProfilePage() {
  const { user, isAuthenticated, updateProfile } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone_number: user?.phone_number || '',
    whatsapp: user?.whatsapp || '',
    telegram: user?.telegram || '',
    preferred_contact_method: user?.preferred_contact_method || 'email',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleEdit = () => {
    setEditForm({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone_number: user?.phone_number || '',
      whatsapp: user?.whatsapp || '',
      telegram: user?.telegram || '',
      preferred_contact_method: user?.preferred_contact_method || 'email',
    })
    setIsEditing(true)
    setError(null)
    setSuccess(false)
  }

  const handleCancel = () => {
    setIsEditing(false)
    setError(null)
    setSuccess(false)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setEditForm(prev => ({ ...prev, [name]: value }))
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(false)

    try {
      const response = await updateProfile(editForm)
      if (response.success) {
        setSuccess(true)
        setIsEditing(false)
        setTimeout(() => setSuccess(false), 3000)
      } else {
        setError(response.error || 'Failed to update profile')
      }
    } catch (err) {
      setError('An error occurred while updating your profile')
    } finally {
      setSaving(false)
    }
  }

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
            {!isEditing && (
              <button
                className="btn btn-secondary profile-edit-button"
                onClick={handleEdit}
                aria-label="Edit profile"
              >
                Edit Profile
              </button>
            )}
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
              <div className="profile-field">
                <label className="profile-field-label">WhatsApp</label>
                <p className="profile-field-value">{user.whatsapp || 'Not provided'}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">Telegram</label>
                <p className="profile-field-value">{user.telegram || 'Not provided'}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">Preferred Contact Method</label>
                <p className="profile-field-value">
                  {user.preferred_contact_method ? user.preferred_contact_method.charAt(0).toUpperCase() + user.preferred_contact_method.slice(1) : 'Email'}
                </p>
              </div>
            </div>

            {isEditing && (
              <div className="profile-section">
                <h2 className="profile-section-title">Edit Profile</h2>
                <form onSubmit={handleSave} className="profile-edit-form">
                  {error && (
                    <div className="profile-form-error" role="alert" aria-live="assertive">
                      {error}
                    </div>
                  )}
                  {success && (
                    <div className="profile-form-success" role="status" aria-live="polite">
                      Profile updated successfully!
                    </div>
                  )}
                  <div className="profile-form-row">
                    <div className="profile-form-field">
                      <label htmlFor="first_name" className="profile-form-label">First Name</label>
                      <input
                        type="text"
                        id="first_name"
                        name="first_name"
                        value={editForm.first_name}
                        onChange={handleInputChange}
                        className="profile-form-input"
                      />
                    </div>
                    <div className="profile-form-field">
                      <label htmlFor="last_name" className="profile-form-label">Last Name</label>
                      <input
                        type="text"
                        id="last_name"
                        name="last_name"
                        value={editForm.last_name}
                        onChange={handleInputChange}
                        className="profile-form-input"
                      />
                    </div>
                  </div>
                  <div className="profile-form-field">
                    <label htmlFor="phone_number" className="profile-form-label">Phone Number</label>
                    <input
                      type="tel"
                      id="phone_number"
                      name="phone_number"
                      value={editForm.phone_number}
                      onChange={handleInputChange}
                      className="profile-form-input"
                    />
                  </div>
                  <div className="profile-form-field">
                    <label htmlFor="whatsapp" className="profile-form-label">WhatsApp</label>
                    <input
                      type="tel"
                      id="whatsapp"
                      name="whatsapp"
                      value={editForm.whatsapp}
                      onChange={handleInputChange}
                      className="profile-form-input"
                      placeholder="Optional"
                    />
                  </div>
                  <div className="profile-form-field">
                    <label htmlFor="telegram" className="profile-form-label">Telegram</label>
                    <input
                      type="text"
                      id="telegram"
                      name="telegram"
                      value={editForm.telegram}
                      onChange={handleInputChange}
                      className="profile-form-input"
                      placeholder="@username (optional)"
                    />
                  </div>
                  <div className="profile-form-field">
                    <label htmlFor="preferred_contact_method" className="profile-form-label">Preferred Contact Method</label>
                    <select
                      id="preferred_contact_method"
                      name="preferred_contact_method"
                      value={editForm.preferred_contact_method}
                      onChange={handleInputChange}
                      className="profile-form-select"
                    >
                      <option value="email">Email</option>
                      <option value="phone">Phone</option>
                      <option value="whatsapp">WhatsApp</option>
                      <option value="telegram">Telegram</option>
                    </select>
                  </div>
                  <div className="profile-form-actions">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={handleCancel}
                      disabled={saving}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

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
