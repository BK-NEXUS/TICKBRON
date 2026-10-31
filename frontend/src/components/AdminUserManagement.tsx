import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { adminAdapter, AdminUser, ContactChange } from '../adapters/adminAdapter'
import { isPhoneValid } from '../utils/inputFilters'
import { Button } from './Button'
import { useAuth } from '../contexts/AuthContext'

export function AdminUserManagement() {
  const { t, formatDate: formatLocalDate } = useI18n()
  const { user: viewer } = useAuth()
  const [users, setUsers] = useState<AdminUser[]>([])
  // The account whose two-step sign-in the super admin is about to reset, with the super admin's own code
  const [resetting, setResetting] = useState<AdminUser | null>(null)
  const [ownCode, setOwnCode] = useState('')
  const [resetError, setResetError] = useState('')
  const [resetBusy, setResetBusy] = useState(false)
  const [resetDone, setResetDone] = useState('')
  // The account whose phone number and/or e-mail a super admin or a staff admin is changing
  const [editing, setEditing] = useState<AdminUser | null>(null)
  const [newPhone, setNewPhone] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [contactError, setContactError] = useState('')
  const [contactBusy, setContactBusy] = useState(false)
  const [contactDone, setContactDone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadUsers()
    // Loads once; the loader is also the Retry action, so it stays a plain function
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadUsers = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await adminAdapter.getUsers()
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        // Sort by date joined (most recent first)
        const sortedUsers = [...response.data].sort((a, b) => 
          new Date(b.date_joined).getTime() - new Date(a.date_joined).getTime()
        )
        setUsers(sortedUsers)
      }
    } catch {
      setError(t('admin.failedToLoadUsers'))
    } finally {
      setLoading(false)
    }
  }

  const openReset = (user: AdminUser) => {
    setResetting(user)
    setOwnCode('')
    setResetError('')
    setResetDone('')
  }

  const submitReset = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!resetting) return
    if (!ownCode.trim()) {
      setResetError(t('admin.twoFactorOwnCodeRequired'))
      return
    }
    setResetError('')
    setResetBusy(true)
    const response = await adminAdapter.resetTwoFactor(resetting.id, ownCode.trim())
    setResetBusy(false)
    if (response.data) {
      const reset = response.data
      setUsers(previous => previous.map(user => (user.id === reset.id ? reset : user)))
      setResetDone(t('admin.twoFactorResetDone', { email: resetting.email }))
      setResetting(null)
    } else {
      setResetError(response.error || t('admin.failedToLoadUsers'))
    }
  }

  // Staff may change guests and owners; a super admin also staff admins; nobody changes a super admin here
  const canEditContact = (account: AdminUser) => (
    !account.is_superuser && (Boolean(viewer?.is_superuser) || !account.is_staff)
  )

  const openContact = (account: AdminUser) => {
    setEditing(account)
    setNewPhone('')
    setNewEmail('')
    setContactError('')
    setContactDone('')
  }

  const submitContact = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!editing) return
    const change: ContactChange = {}
    if (newPhone.trim()) change.phone_number = newPhone.trim()
    if (newEmail.trim()) change.email = newEmail.trim()
    if (!change.phone_number && !change.email) {
      setContactError(t('admin.contactNeedOne'))
      return
    }
    if (change.phone_number && !isPhoneValid(change.phone_number)) {
      setContactError(t('auth.errPhone'))
      return
    }
    setContactError('')
    setContactBusy(true)
    const response = await adminAdapter.changeContact(editing.id, change)
    setContactBusy(false)
    if (response.data) {
      const changed = response.data
      setUsers(previous => previous.map(account => (account.id === changed.id ? { ...account, ...changed } : account)))
      setContactDone(t('admin.contactSaved', { email: changed.email }))
      setEditing(null)
    } else {
      setContactError(response.error || t('admin.failedToLoadUsers'))
    }
  }

  const getRoleBadgeClass = (role: string, isStaff: boolean, isSuperuser: boolean) => {
    if (isSuperuser) return 'role-badge--super-admin'
    if (isStaff) return 'role-badge--staff'
    if (role === 'hotel-owner') return 'role-badge--hotel-owner'
    return 'role-badge--user'
  }

  const getRoleLabel = (role: string, isStaff: boolean, isSuperuser: boolean) => {
    if (isSuperuser) return t('admin.superAdmin')
    if (isStaff) return t('admin.staff')
    if (role === 'hotel-owner') return t('admin.roleHotelOwner')
    return t('admin.roleUser')
  }

  const getStatusClass = (isActive: boolean) => {
    return isActive ? 'status-badge--active' : 'status-badge--inactive'
  }

  const formatDate = (dateString: string) => formatLocalDate(dateString)

  const formatDateTime = (dateString: string) => formatLocalDate(dateString, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })

  return (
    <div className="admin-user-management">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('admin.userManagement')}</h2>
        <p className="admin-view-subtitle">{t('admin.viewAndManageUser')}</p>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {resetDone && <p className="alert alert-success" role="status">{resetDone}</p>}
      {contactDone && <p className="alert alert-success" role="status">{contactDone}</p>}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          {t('admin.loadingUsers')}
        </div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <p>{t('admin.noUsersFound')}</p>
          <p>{t('admin.usersWillAppearHere')}</p>
        </div>
      ) : (
        <div className="users-list">
          <div className="users-count">
            <p>{t('admin.totalUsers', { count: users.length })}</p>
          </div>
          
          {users.map(user => (
            <div key={user.id} className="user-card">
              <div className="user-card-header">
                <div className="user-info">
                  <h3 className="user-name">{user.full_name || user.email}</h3>
                  <p className="user-email">{user.email}</p>
                  <p className="user-id">ID: {user.id}</p>
                </div>
                <div className="user-badges">
                  <span className={`role-badge ${getRoleBadgeClass(user.role, user.is_staff, user.is_superuser)}`}>
                    {getRoleLabel(user.role, user.is_staff, user.is_superuser)}
                  </span>
                  <span className={`status-badge ${getStatusClass(user.is_active)}`}>
                    {user.is_active ? t('profile.active') : t('profile.inactive')}
                  </span>
                </div>
              </div>

              <div className="user-card-body">
                <div className="user-details-grid">
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.firstName')}</span>
                    <span className="detail-value">{user.first_name || t('admin.na')}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.lastName')}</span>
                    <span className="detail-value">{user.last_name || t('admin.na')}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.phone')}</span>
                    <span className="detail-value">{user.phone_number || t('admin.na')}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.memberSince')}</span>
                    <span className="detail-value">{formatDate(user.date_joined)}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.lastLogin')}</span>
                    <span className="detail-value">{user.last_login ? formatDateTime(user.last_login) : t('profile.never')}</span>
                  </div>
                </div>
              </div>

              <div className="user-card-footer">
                {canEditContact(user) && (
                  <div className="user-contact-block">
                    {editing?.id !== user.id ? (
                      <Button type="button" variant="secondary" size="sm" onClick={() => openContact(user)}>
                        {t('admin.contactEdit')}
                      </Button>
                    ) : (
                      <form className="user-contact-form" onSubmit={submitContact} noValidate>
                        <p className="auth-hint">{t('admin.contactHint')}</p>
                        {contactError && <div className="alert alert-error" role="alert">{contactError}</div>}
                        <label htmlFor={`new-phone-${user.id}`}>{t('admin.contactNewPhone')}</label>
                        <input id={`new-phone-${user.id}`} className="search-input" type="tel" inputMode="tel"
                          autoComplete="off" value={newPhone} disabled={contactBusy} placeholder="+998 90 123 45 67"
                          onChange={(event) => setNewPhone(event.target.value)} />
                        <label htmlFor={`new-email-${user.id}`}>{t('admin.contactNewEmail')}</label>
                        <input id={`new-email-${user.id}`} className="search-input" type="email"
                          autoComplete="off" value={newEmail} disabled={contactBusy}
                          onChange={(event) => setNewEmail(event.target.value)} />
                        <div className="user-two-factor-actions">
                          <Button type="submit" size="sm" loading={contactBusy} disabled={contactBusy}>{t('admin.contactSave')}</Button>
                          <Button type="button" variant="secondary" size="sm" disabled={contactBusy} onClick={() => setEditing(null)}>
                            {t('admin.contactCancel')}
                          </Button>
                        </div>
                      </form>
                    )}
                  </div>
                )}
                <div className="user-two-factor-block">
                  <p className="user-two-factor">{t(user.two_factor_enabled ? 'admin.twoFactorOn' : 'admin.twoFactorOff')}</p>
                  {viewer?.is_superuser && !user.is_superuser && user.two_factor_enabled && resetting?.id !== user.id && (
                    <Button type="button" variant="secondary" size="sm" onClick={() => openReset(user)}>
                      {t('admin.twoFactorReset')}
                    </Button>
                  )}
                  {resetting?.id === user.id && (
                    <form className="user-two-factor-reset" onSubmit={submitReset} noValidate>
                      <p className="auth-hint">{t('admin.twoFactorResetHint', { email: user.email })}</p>
                      {resetError && <div className="alert alert-error" role="alert">{resetError}</div>}
                      <label htmlFor={`own-code-${user.id}`}>{t('admin.twoFactorOwnCode')}</label>
                      <input
                        id={`own-code-${user.id}`}
                        className="search-input"
                        value={ownCode}
                        onChange={(event) => setOwnCode(event.target.value)}
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        maxLength={7}
                        disabled={resetBusy}
                      />
                      <div className="user-two-factor-actions">
                        <Button type="submit" size="sm" loading={resetBusy} disabled={resetBusy}>
                          {resetBusy ? t('admin.twoFactorResetting') : t('admin.twoFactorResetConfirm')}
                        </Button>
                        <Button type="button" variant="secondary" size="sm" disabled={resetBusy} onClick={() => setResetting(null)}>
                          {t('admin.twoFactorResetCancel')}
                        </Button>
                      </div>
                    </form>
                  )}
                </div>
                <div className="user-dates">
                  <small className="user-created">
                    {t('admin.joinedOnShort', { date: formatDate(user.date_joined) })}
                  </small>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
