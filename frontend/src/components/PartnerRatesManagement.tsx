import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerRatePlan, CreateRatePlanRequest, UpdateRatePlanRequest } from '../adapters/partnerAdapter'

interface PartnerRatesManagementProps {
  roomTypeId: number
  roomTypeName: string
}

type ViewMode = 'list' | 'create' | 'edit'

export function PartnerRatesManagement({ roomTypeId, roomTypeName }: PartnerRatesManagementProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [ratePlans, setRatePlans] = useState<PartnerRatePlan[]>([])
  const [selectedRatePlan, setSelectedRatePlan] = useState<PartnerRatePlan | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const [formData, setFormData] = useState<CreateRatePlanRequest>({
    room_type: roomTypeId,
    name: '',
    slug: '',
    rate_type: 'standard',
    description: '',
    base_price: 100,
    currency: 'USD',
    min_nights: 1,
    max_nights: 30,
    is_active: true,
    cancellation_policy: 'flexible',
    deposit_required: false,
    deposit_percentage: undefined,
    advance_booking_days: undefined,
  })

  useEffect(() => {
    loadRatePlans()
  }, [roomTypeId])

  const loadRatePlans = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.getRatePlans()
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        // Filter rate plans for this room type
        const roomTypeRatePlans = response.data.filter(rp => rp.room_type === roomTypeId)
        setRatePlans(roomTypeRatePlans)
      }
    } catch (err) {
      setError('Failed to load rate plans. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!validateForm()) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.createRatePlan(formData)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage('Rate plan created successfully')
      setViewMode('list')
      resetForm()
      loadRatePlans()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to create rate plan. Please try again.')
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!selectedRatePlan || !validateForm()) return

    setLoading(true)
    setError(null)

    try {
      const updateData: UpdateRatePlanRequest = {
        name: formData.name,
        slug: formData.slug,
        rate_type: formData.rate_type,
        description: formData.description,
        base_price: formData.base_price,
        currency: formData.currency,
        min_nights: formData.min_nights,
        max_nights: formData.max_nights,
        is_active: formData.is_active,
        cancellation_policy: formData.cancellation_policy,
        deposit_required: formData.deposit_required,
        deposit_percentage: formData.deposit_percentage,
        advance_booking_days: formData.advance_booking_days,
      }

      const response = await partnerAdapter.updateRatePlan(selectedRatePlan.id, updateData)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage('Rate plan updated successfully')
      setViewMode('list')
      resetForm()
      setSelectedRatePlan(null)
      loadRatePlans()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to update rate plan. Please try again.')
      setLoading(false)
    }
  }

  const handleDelete = async (ratePlanId: number) => {
    if (!confirm('Are you sure you want to delete this rate plan?')) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.deleteRatePlan(ratePlanId)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage('Rate plan deleted successfully')
      loadRatePlans()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to delete rate plan. Please try again.')
      setLoading(false)
    }
  }

  const handleEdit = (ratePlan: PartnerRatePlan) => {
    setSelectedRatePlan(ratePlan)
    setFormData({
      room_type: roomTypeId,
      name: ratePlan.name,
      slug: ratePlan.slug,
      rate_type: ratePlan.rate_type,
      description: ratePlan.description,
      base_price: ratePlan.base_price,
      currency: ratePlan.currency,
      min_nights: ratePlan.min_nights,
      max_nights: ratePlan.max_nights,
      is_active: ratePlan.is_active,
      cancellation_policy: ratePlan.cancellation_policy,
      deposit_required: ratePlan.deposit_required,
      deposit_percentage: ratePlan.deposit_percentage,
      advance_booking_days: ratePlan.advance_booking_days,
    })
    setViewMode('edit')
  }

  const validateForm = (): boolean => {
    if (!formData.name.trim()) {
      setError('Rate plan name is required')
      return false
    }
    if (!formData.slug.trim()) {
      setError('Slug is required')
      return false
    }
    if (formData.min_nights < 1) {
      setError('Minimum nights must be at least 1')
      return false
    }
    if (formData.max_nights < formData.min_nights) {
      setError('Maximum nights cannot be less than minimum nights')
      return false
    }
    if (formData.base_price < 0) {
      setError('Base price must be positive')
      return false
    }
    if (formData.deposit_required && (formData.deposit_percentage === undefined || formData.deposit_percentage < 0 || formData.deposit_percentage > 100)) {
      setError('Deposit percentage must be between 0 and 100 when deposit is required')
      return false
    }
    return true
  }

  const resetForm = () => {
    setFormData({
      room_type: roomTypeId,
      name: '',
      slug: '',
      rate_type: 'standard',
      description: '',
      base_price: 100,
      currency: 'USD',
      min_nights: 1,
      max_nights: 30,
      is_active: true,
      cancellation_policy: 'flexible',
      deposit_required: false,
      deposit_percentage: undefined,
      advance_booking_days: undefined,
    })
  }

  const handleInputChange = (field: keyof CreateRatePlanRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  const renderListView = () => (
    <div className="partner-rates-list">
      <div className="rates-list-header">
        <h2 className="rates-list-title">Rate Plans for {roomTypeName}</h2>
        <button
          onClick={() => {
            resetForm()
            setViewMode('create')
          }}
          className="btn btn-primary"
          aria-label="Add new rate plan"
        >
          + Add Rate Plan
        </button>
      </div>

      {successMessage && (
        <div className="alert alert-success" role="alert" aria-live="polite">
          {successMessage}
        </div>
      )}

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          Loading rate plans...
        </div>
      ) : ratePlans.length === 0 ? (
        <div className="empty-state">
          <p>No rate plans found for this room type.</p>
          <p>Click "Add Rate Plan" to create your first rate plan.</p>
        </div>
      ) : (
        <div className="rate-plans-grid">
          {ratePlans.map(ratePlan => (
            <div key={ratePlan.id} className="rate-plan-card">
              <div className="rate-plan-card-header">
                <h3 className="rate-plan-name">{ratePlan.name}</h3>
                <div className="rate-plan-badges">
                  <span className={`rate-plan-badge ${ratePlan.is_active ? 'rate-plan-badge--active' : 'rate-plan-badge--inactive'}`}>
                    {ratePlan.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <span className="rate-plan-badge rate-plan-badge--type">
                    {ratePlan.rate_type}
                  </span>
                </div>
              </div>
              <div className="rate-plan-card-body">
                <p className="rate-plan-description">{ratePlan.description}</p>
                <div className="rate-plan-details">
                  <div className="rate-plan-detail">
                    <span className="detail-label">Base Price:</span>
                    <span className="detail-value">{ratePlan.base_price} {ratePlan.currency}</span>
                  </div>
                  <div className="rate-plan-detail">
                    <span className="detail-label">Min/Max Nights:</span>
                    <span className="detail-value">{ratePlan.min_nights} - {ratePlan.max_nights}</span>
                  </div>
                  <div className="rate-plan-detail">
                    <span className="detail-label">Cancellation:</span>
                    <span className="detail-value">{ratePlan.cancellation_policy}</span>
                  </div>
                  {ratePlan.deposit_required && (
                    <div className="rate-plan-detail">
                      <span className="detail-label">Deposit:</span>
                      <span className="detail-value">{ratePlan.deposit_percentage}%</span>
                    </div>
                  )}
                  {ratePlan.advance_booking_days && (
                    <div className="rate-plan-detail">
                      <span className="detail-label">Advance Booking:</span>
                      <span className="detail-value">{ratePlan.advance_booking_days} days</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="rate-plan-card-footer">
                <button
                  onClick={() => handleEdit(ratePlan)}
                  className="btn btn-secondary"
                  aria-label={`Edit ${ratePlan.name}`}
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(ratePlan.id)}
                  className="btn btn-danger"
                  aria-label={`Delete ${ratePlan.name}`}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const renderFormView = () => (
    <div className="partner-rates-form">
      <div className="rates-form-header">
        <h2 className="rates-form-title">
          {viewMode === 'create' ? 'Create Rate Plan' : 'Edit Rate Plan'}
        </h2>
        <button
          onClick={() => {
            setViewMode('list')
            resetForm()
            setSelectedRatePlan(null)
          }}
          className="btn btn-tertiary"
          aria-label="Cancel and return to list"
        >
          Cancel
        </button>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      <form className="rates-form" onSubmit={(e) => {
        e.preventDefault()
        viewMode === 'create' ? handleCreate() : handleUpdate()
      }}>
        <div className="form-group">
          <label htmlFor="rate_name">Rate Plan Name *</label>
          <input
            id="rate_name"
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className="form-input"
            required
            aria-required="true"
          />
        </div>

        <div className="form-group">
          <label htmlFor="rate_slug">Slug *</label>
          <input
            id="rate_slug"
            type="text"
            value={formData.slug}
            onChange={(e) => handleInputChange('slug', e.target.value.toLowerCase().replace(/\s+/g, '-'))}
            className="form-input"
            required
            aria-required="true"
          />
          <small className="form-hint">URL-friendly identifier (e.g., "standard-rate")</small>
        </div>

        <div className="form-group">
          <label htmlFor="rate_type">Rate Type *</label>
          <select
            id="rate_type"
            value={formData.rate_type}
            onChange={(e) => handleInputChange('rate_type', e.target.value)}
            className="form-input"
            required
            aria-required="true"
          >
            <option value="standard">Standard</option>
            <option value="non_refundable">Non-Refundable</option>
            <option value="early_bird">Early Bird</option>
            <option value="last_minute">Last Minute</option>
            <option value="long_stay">Long Stay</option>
            <option value="seasonal">Seasonal</option>
            <option value="corporate">Corporate</option>
            <option value="promo">Promo</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="rate_description">Description</label>
          <textarea
            id="rate_description"
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className="form-input"
            rows={3}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="base_price">Base Price *</label>
            <input
              id="base_price"
              type="number"
              min="0"
              step="0.01"
              value={formData.base_price}
              onChange={(e) => handleInputChange('base_price', parseFloat(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label htmlFor="currency">Currency *</label>
            <select
              id="currency"
              value={formData.currency}
              onChange={(e) => handleInputChange('currency', e.target.value)}
              className="form-input"
              required
              aria-required="true"
            >
              <option value="USD">USD - US Dollar</option>
              <option value="EUR">EUR - Euro</option>
              <option value="UZS">UZS - Uzbekistani Som</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="min_nights">Minimum Nights *</label>
            <input
              id="min_nights"
              type="number"
              min="1"
              value={formData.min_nights}
              onChange={(e) => handleInputChange('min_nights', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label htmlFor="max_nights">Maximum Nights *</label>
            <input
              id="max_nights"
              type="number"
              min="1"
              value={formData.max_nights}
              onChange={(e) => handleInputChange('max_nights', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="cancellation_policy">Cancellation Policy *</label>
          <select
            id="cancellation_policy"
            value={formData.cancellation_policy}
            onChange={(e) => handleInputChange('cancellation_policy', e.target.value)}
            className="form-input"
            required
            aria-required="true"
          >
            <option value="flexible">Flexible</option>
            <option value="moderate">Moderate</option>
            <option value="strict">Strict</option>
            <option value="non_refundable">Non-Refundable</option>
          </select>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => handleInputChange('is_active', e.target.checked)}
            />
            <span>Active</span>
          </label>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={formData.deposit_required}
              onChange={(e) => handleInputChange('deposit_required', e.target.checked)}
            />
            <span>Deposit Required</span>
          </label>
        </div>

        {formData.deposit_required && (
          <div className="form-group">
            <label htmlFor="deposit_percentage">Deposit Percentage *</label>
            <input
              id="deposit_percentage"
              type="number"
              min="0"
              max="100"
              step="1"
              value={formData.deposit_percentage || ''}
              onChange={(e) => handleInputChange('deposit_percentage', e.target.value ? parseInt(e.target.value) : undefined)}
              className="form-input"
              required={formData.deposit_required}
              aria-required={formData.deposit_required}
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="advance_booking_days">Advance Booking Days</label>
          <input
            id="advance_booking_days"
            type="number"
            min="0"
            value={formData.advance_booking_days || ''}
            onChange={(e) => handleInputChange('advance_booking_days', e.target.value ? parseInt(e.target.value) : undefined)}
            className="form-input"
          />
          <small className="form-hint">Minimum days in advance required for booking (optional)</small>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : viewMode === 'create' ? 'Create Rate Plan' : 'Update Rate Plan'}
          </button>
        </div>
      </form>
    </div>
  )

  return (
    <div className="partner-rates-management">
      {viewMode === 'list' ? renderListView() : renderFormView()}
    </div>
  )
}
