import { useState, useEffect } from 'react'
import { useDialogFocus } from '../hooks/useDialogFocus'
import { adminAdapter, AdminProperty, ApprovePropertyRequest } from '../adapters/adminAdapter'
import { PropertyRegionField } from './PropertyRegionField'

export function AdminPropertyModeration() {
  const [properties, setProperties] = useState<AdminProperty[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [rejectModal, setRejectModal] = useState<{ propertyId: number; propertyName: string } | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')

  useEffect(() => {
    loadProperties()
  }, [])

  const loadProperties = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await adminAdapter.getProperties()
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        // Sort by creation date (most recent first)
        const sortedProperties = [...response.data].sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        setProperties(sortedProperties)
      }
    } catch (err) {
      setError('Failed to load properties. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (propertyId: number) => {
    setActionLoading(propertyId)
    setError(null)

    try {
      const response = await adminAdapter.approveProperty(propertyId, {})
      
      if (response.error) {
        setError(response.error)
      } else {
        // Refresh the list
        await loadProperties()
      }
    } catch (err) {
      setError('Failed to approve property. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleRejectClick = (propertyId: number, propertyName: string) => {
    setRejectModal({ propertyId, propertyName })
    setRejectionReason('')
  }

  const handleRejectSubmit = async () => {
    if (!rejectModal) return

    setActionLoading(rejectModal.propertyId)
    setError(null)

    try {
      const requestData: ApprovePropertyRequest = { rejection_reason: rejectionReason }
      const response = await adminAdapter.approveProperty(rejectModal.propertyId, requestData)
      
      if (response.error) {
        setError(response.error)
      } else {
        setRejectModal(null)
        setRejectionReason('')
        // Refresh the list
        await loadProperties()
      }
    } catch (err) {
      setError('Failed to reject property. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const dialogRef = useDialogFocus<HTMLDivElement>(rejectModal !== null, () => handleRejectCancel())

  const handleRejectCancel = () => {
    setRejectModal(null)
    setRejectionReason('')
  }

  const handleSuspend = async (propertyId: number) => {
    setActionLoading(propertyId)
    setError(null)

    try {
      const response = await adminAdapter.suspendProperty(propertyId)
      
      if (response.error) {
        setError(response.error)
      } else {
        // Refresh the list
        await loadProperties()
      }
    } catch (err) {
      setError('Failed to suspend property. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'property-status--active'
      case 'pending':
        return 'property-status--pending'
      case 'rejected':
        return 'property-status--rejected'
      case 'suspended':
        return 'property-status--suspended'
      default:
        return 'property-status--unknown'
    }
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="admin-property-moderation">
      <div className="admin-view-header">
        <h1 className="admin-view-title">Property Moderation</h1>
        <p className="admin-view-subtitle">Review and moderate property submissions</p>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          Loading properties...
        </div>
      ) : properties.length === 0 ? (
        <div className="empty-state">
          <p>No properties found for moderation.</p>
          <p>Properties will appear here once hotel-owners submit them.</p>
        </div>
      ) : (
        <div className="properties-list">
          {properties.map(property => (
            <div key={property.id} className="property-card">
              <div className="property-card-header">
                <div className="property-info">
                  <h3 className="property-name">
                    {property.city}, {property.country}
                  </h3>
                  <p className="property-address">{property.address_line1}</p>
                  {property.address_line2 && <p className="property-address">{property.address_line2}</p>}
                  <p className="property-owner">Owner: {property.owner_name || `ID: ${property.owner}`}</p>
                </div>
                <div className="property-status-badges">
                  <span className={`property-status ${getStatusClass(property.status)}`}>
                    {property.status.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="property-card-body">
                <div className="property-details-grid">
                  <div className="property-detail">
                    <span className="detail-label">Max Guests:</span>
                    <span className="detail-value">{property.max_guests}</span>
                  </div>
                  <div className="property-detail">
                    <span className="detail-label">Bedrooms:</span>
                    <span className="detail-value">{property.bedrooms}</span>
                  </div>
                  <div className="property-detail">
                    <span className="detail-label">Bathrooms:</span>
                    <span className="detail-value">{property.bathrooms}</span>
                  </div>
                  <div className="property-detail">
                    <span className="detail-label">Base Price:</span>
                    <span className="detail-value">{formatCurrency(property.base_price, property.currency)}</span>
                  </div>
                  <div className="property-detail">
                    <span className="detail-label">Created:</span>
                    <span className="detail-value">{formatDate(property.created_at)}</span>
                  </div>
                  {property.approved_at && (
                    <div className="property-detail">
                      <span className="detail-label">Approved:</span>
                      <span className="detail-value">{formatDate(property.approved_at)}</span>
                    </div>
                  )}
                </div>

                <PropertyRegionField
                  propertyId={property.id}
                  region={property.state}
                  onSaved={state => setProperties(prev => prev.map(p => p.id === property.id ? { ...p, state: state ?? undefined } : p))}
                />

                {property.rejection_reason && (
                  <div className="property-rejection-reason">
                    <span className="detail-label">Rejection Reason:</span>
                    <p className="detail-value">{property.rejection_reason}</p>
                  </div>
                )}

                <div className="property-amenities">
                  <span className="detail-label">Features:</span>
                  <div className="amenities-tags">
                    {property.has_elevator && <span className="amenity-tag">Elevator</span>}
                    {property.has_parking && <span className="amenity-tag">Parking</span>}
                    {property.has_wifi && <span className="amenity-tag">WiFi</span>}
                    {property.has_ac && <span className="amenity-tag">Air Conditioning</span>}
                    {property.has_heating && <span className="amenity-tag">Heating</span>}
                  </div>
                </div>
              </div>

              <div className="property-card-footer">
                <div className="property-actions">
                  {property.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleApprove(property.id)}
                        disabled={actionLoading === property.id}
                        className="btn btn-primary"
                        aria-label={`Approve property at ${property.city}, ${property.country}`}
                      >
                        {actionLoading === property.id ? 'Processing...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleRejectClick(property.id, `${property.city}, ${property.country}`)}
                        disabled={actionLoading === property.id}
                        className="btn btn-secondary"
                        aria-label={`Reject property at ${property.city}, ${property.country}`}
                      >
                        Reject
                      </button>
                    </>
                  )}
                  {property.status === 'active' && (
                    <button
                      onClick={() => handleSuspend(property.id)}
                      disabled={actionLoading === property.id}
                      className="btn btn-danger"
                      aria-label={`Suspend property at ${property.city}, ${property.country}`}
                    >
                      {actionLoading === property.id ? 'Processing...' : 'Suspend'}
                    </button>
                  )}
                  {property.status === 'suspended' && (
                    <button
                      onClick={() => handleApprove(property.id)}
                      disabled={actionLoading === property.id}
                      className="btn btn-primary"
                      aria-label={`Reactivate property at ${property.city}, ${property.country}`}
                    >
                      {actionLoading === property.id ? 'Processing...' : 'Reactivate'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {rejectModal && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="reject-modal-title">
          <div className="modal-content" ref={dialogRef} tabIndex={-1}>
            <h2 id="reject-modal-title" className="modal-title">Reject Property</h2>
            <p className="modal-subtitle">You are rejecting: {rejectModal.propertyName}</p>
            
            <div className="form-group">
              <label htmlFor="rejection-reason">Rejection Reason (required):</label>
              <textarea
                id="rejection-reason"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="form-control"
                rows={4}
                required
                aria-required="true"
                placeholder="Please provide a reason for rejection..."
              />
            </div>

            <div className="modal-actions">
              <button
                onClick={handleRejectSubmit}
                disabled={!rejectionReason.trim() || actionLoading === rejectModal.propertyId}
                className="btn btn-danger"
              >
                {actionLoading === rejectModal.propertyId ? 'Processing...' : 'Reject Property'}
              </button>
              <button
                onClick={handleRejectCancel}
                disabled={actionLoading === rejectModal.propertyId}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
