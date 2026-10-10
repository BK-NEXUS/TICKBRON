import { useI18n } from '../i18n/I18nContext'
import { useState } from 'react'
import { Lock, Calendar, Heart, House } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { EmptyState } from '../components/EmptyState'
import { Link } from 'react-router-dom'
import { canUsePartnerPanel } from '../utils/roles'
import { PhoneInput } from '../components/PhoneInput'
import { isValidPhone, phoneExample } from '../utils/phone'
import { PhoneVerifyDialog } from '../components/PhoneVerifyDialog'

export function ProfilePage() {
  const { t, formatDate } = useI18n()
  const { user, isAuthenticated, updateProfile, refreshUser } = useAuth()
  const [verifyingPhone, setVerifyingPhone] = useState(false)
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
    setError(null)
    setSuccess(false)

    // Checked only when changed: a number saved before validation existed is sent back as it is
    const phoneChanged = editForm.phone_number !== (user?.phone_number || '')
    if (phoneChanged && editForm.phone_number && !isValidPhone(editForm.phone_number)) {
      setError(t('phone.invalid', { example: phoneExample() }))
      return
    }

    setSaving(true)
    try {
      const response = await updateProfile(editForm)
      if (response.success) {
        setSuccess(true)
        setIsEditing(false)
        setTimeout(() => setSuccess(false), 3000)
      } else {
        setError(response.error || t('profile.errorUpdate'))
      }
    } catch (err) {
      setError(t('profile.errorUpdateGeneric'))
    } finally {
      setSaving(false)
    }
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="profile-page">
        <div className="container">
          <EmptyState
            icon={<Lock size={40} />}
            title={t('common.signInRequired')}
            message={t('profile.signInText')}
            ctaText={t('auth.signIn')}
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
                  {user.is_active ? t('profile.active') : t('profile.inactive')}
                </span>
                {user.email_verified && (
                  <span className="profile-status-badge profile-status-badge--verified">
                    {t('profile.verified')}
                  </span>
                )}
              </div>
            </div>
            {!isEditing && (
              <button
                className="btn btn-secondary profile-edit-button"
                onClick={handleEdit}
                aria-label={t('profile.edit')}
              >
                {t('profile.edit')}
              </button>
            )}
          </div>

          <div className="profile-details">
            <div className="profile-section">
              <h2 className="profile-section-title">{t('profile.personal')}</h2>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.firstName')}</label>
                <p className="profile-field-value">{user.first_name || t('profile.notProvided')}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.lastName')}</label>
                <p className="profile-field-value">{user.last_name || t('profile.notProvided')}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.email')}</label>
                <p className="profile-field-value">{user.email}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.phone')}</label>
                <p className="profile-field-value">{user.phone_number || t('profile.notProvided')}</p>
                {user.phone_number && (
                  <p className="profile-phone-status">
                    <span className={`profile-phone-badge ${user.phone_verified ? 'profile-phone-badge--ok' : 'profile-phone-badge--warn'}`}>
                      {user.phone_verified ? t('profile.phoneVerified') : t('profile.phoneNotVerified')}
                    </span>
                    {!user.phone_verified && (
                      <>
                        <button type="button" className="btn btn-secondary btn-small" onClick={() => setVerifyingPhone(true)}>
                          {t('profile.verifyPhone')}
                        </button>
                        <small className="form-hint">{t('profile.verifyPhoneHint')}</small>
                      </>
                    )}
                  </p>
                )}
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.whatsapp')}</label>
                <p className="profile-field-value">{user.whatsapp || t('profile.notProvided')}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.telegram')}</label>
                <p className="profile-field-value">{user.telegram || t('profile.notProvided')}</p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.contactMethod')}</label>
                <p className="profile-field-value">
                  {t(`profile.contact.${user.preferred_contact_method || 'email'}`)}
                </p>
              </div>
            </div>

            {isEditing && (
              <div className="profile-section">
                <h2 className="profile-section-title">{t('profile.edit')}</h2>
                <form onSubmit={handleSave} className="profile-edit-form">
                  {error && (
                    <div className="profile-form-error" role="alert" aria-live="assertive">
                      {error}
                    </div>
                  )}
                  {success && (
                    <div className="profile-form-success" role="status" aria-live="polite">
                      {t('profile.saved')}
                    </div>
                  )}
                  <div className="profile-form-row">
                    <div className="profile-form-field">
                      <label htmlFor="first_name" className="profile-form-label">{t('profile.firstName')}</label>
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
                      <label htmlFor="last_name" className="profile-form-label">{t('profile.lastName')}</label>
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
                    <label htmlFor="phone_number" className="profile-form-label">{t('profile.phone')}</label>
                    <PhoneInput
                      id="phone_number"
                      name="phone_number"
                      value={editForm.phone_number}
                      onChange={(phone_number) => setEditForm(prev => ({ ...prev, phone_number }))}
                      className="profile-form-input"
                    />
                  </div>
                  <div className="profile-form-field">
                    <label htmlFor="whatsapp" className="profile-form-label">{t('profile.whatsapp')}</label>
                    <input
                      type="tel"
                      id="whatsapp"
                      name="whatsapp"
                      value={editForm.whatsapp}
                      onChange={handleInputChange}
                      className="profile-form-input"
                      placeholder={t('profile.optional')}
                    />
                  </div>
                  <div className="profile-form-field">
                    <label htmlFor="telegram" className="profile-form-label">{t('profile.telegram')}</label>
                    <input
                      type="text"
                      id="telegram"
                      name="telegram"
                      value={editForm.telegram}
                      onChange={handleInputChange}
                      className="profile-form-input"
                      placeholder={t('profile.telegramPlaceholder')}
                    />
                  </div>
                  <div className="profile-form-field">
                    <label htmlFor="preferred_contact_method" className="profile-form-label">{t('profile.contactMethod')}</label>
                    <select
                      id="preferred_contact_method"
                      name="preferred_contact_method"
                      value={editForm.preferred_contact_method}
                      onChange={handleInputChange}
                      className="profile-form-select"
                    >
                      <option value="email">{t('profile.contact.email')}</option>
                      <option value="phone">{t('profile.contact.phone')}</option>
                      <option value="whatsapp">{t('profile.contact.whatsapp')}</option>
                      <option value="telegram">{t('profile.contact.telegram')}</option>
                    </select>
                  </div>
                  <div className="profile-form-actions">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={saving}
                    >
                      {saving ? t('profile.saving') : t('profile.save')}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={handleCancel}
                      disabled={saving}
                    >
                      {t('common.cancel')}
                    </button>
                  </div>
                </form>
              </div>
            )}

            <div className="profile-section">
              <h2 className="profile-section-title">{t('profile.account')}</h2>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.memberSince')}</label>
                <p className="profile-field-value">
                  {user.date_joined ? formatDate(user.date_joined) : t('profile.unknown')}
                </p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.lastLogin')}</label>
                <p className="profile-field-value">
                  {user.last_login ? formatDate(user.last_login, { dateStyle: 'medium', timeStyle: 'short' }) : t('profile.never')}
                </p>
              </div>
              <div className="profile-field">
                <label className="profile-field-label">{t('profile.twoFactor')}</label>
                <p className="profile-field-value">
                  {user.two_factor_enabled ? t('profile.enabled') : t('profile.disabled')}
                </p>
              </div>
            </div>

            <div className="profile-section">
              <h2 className="profile-section-title">{t('profile.quickLinks')}</h2>
              <div className="profile-links">
                <Link to="/bookings" className="profile-link">
                  <span className="profile-link-icon"><Calendar size={18} /></span>
                  <span className="profile-link-text">{t('header.myBookings')}</span>
                </Link>
                <Link to="/favorites" className="profile-link">
                  <span className="profile-link-icon"><Heart size={18} /></span>
                  <span className="profile-link-text">{t('crumb.myFavorites')}</span>
                </Link>
                {canUsePartnerPanel(user) && (
                  <Link to="/partner" className="profile-link">
                    <span className="profile-link-icon"><House size={18} /></span>
                    <span className="profile-link-text">{t('header.partnerDashboard')}</span>
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      {verifyingPhone && user.phone_number && (
        <PhoneVerifyDialog
          phone={user.phone_number}
          onClose={() => setVerifyingPhone(false)}
          onVerified={async () => {
            await refreshUser()
            setVerifyingPhone(false)
          }}
        />
      )}
    </div>
  )
}

export default ProfilePage
