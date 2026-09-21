import { useState, useEffect } from 'react'
import { adminAdapter, AdminUser } from '../adapters/adminAdapter'

export function AdminUserManagement() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadUsers()
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
      setError('Failed to load users. Please try again.')
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
    if (isSuperuser) return 'Super Admin'
    if (isStaff) return 'Staff'
    if (role === 'hotel-owner') return 'Hotel Owner'
    return 'User'
  }

  const getStatusClass = (isActive: boolean) => {
    return isActive ? 'status-badge--active' : 'status-badge--inactive'
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="admin-user-management">
      <div className="admin-view-header">
        <h1 className="admin-view-title">User Management</h1>
        <p className="admin-view-subtitle">View and manage user accounts</p>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          Loading users...
        </div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <p>No users found.</p>
          <p>Users will appear here once they register or are created.</p>
        </div>
      ) : (
        <div className="users-list">
          <div className="users-count">
            <p>Total users: {users.length}</p>
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
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              <div className="user-card-body">
                <div className="user-details-grid">
                  <div className="user-detail">
                    <span className="detail-label">First Name:</span>
                    <span className="detail-value">{user.first_name || 'N/A'}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">Last Name:</span>
                    <span className="detail-value">{user.last_name || 'N/A'}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">Phone:</span>
                    <span className="detail-value">{user.phone_number || 'N/A'}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">Member Since:</span>
                    <span className="detail-value">{formatDate(user.date_joined)}</span>
                  </div>
                  <div className="user-detail">
                    <span className="detail-label">Last Login:</span>
                    <span className="detail-value">{user.last_login ? formatDateTime(user.last_login) : 'Never'}</span>
                  </div>
                </div>
              </div>

              <div className="user-card-footer">
                <div className="user-dates">
                  <small className="user-created">
                    Joined on {formatDate(user.date_joined)}
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
