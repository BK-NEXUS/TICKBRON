import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { adminAdapter, AdminUser } from '../adapters/adminAdapter'

export function AdminUserManagement() {
  const { t, formatDate: formatLocalDate } = useI18n()
  const [users, setUsers] = useState<AdminUser[]>([])
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
    } catch (err) {
      setError(t('admin.failedToLoadUsers'))
    } finally {
      setLoading(false)
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
                    <span className="detail-value">{user.first_name || 'N/A'}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.lastName')}</span>
                    <span className="detail-value">{user.last_name || 'N/A'}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.phone')}</span>
                    <span className="detail-value">{user.phone_number || 'N/A'}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.memberSince')}</span>
                    <span className="detail-value">{formatDate(user.date_joined)}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">{t('admin.lastLogin')}</span>
                    <span className="detail-value">{user.last_login ? formatDateTime(user.last_login) : 'Never'}</span>
                  </div>
                </div>
              </div>

              <div className="user-card-footer">
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
