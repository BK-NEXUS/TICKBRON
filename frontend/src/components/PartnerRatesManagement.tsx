import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerRatePlan, CreateRatePlanRequest, UpdateRatePlanRequest } from '../adapters/partnerAdapter'

interface PartnerRatesManagementProps {
  roomTypeId: number
  roomTypeName: string
  /** Open the per-date availability of a rate plan */
  onManageAvailability?: (ratePlan: { id: number; name: string }) => void
}

type ViewMode = 'list' | 'create' | 'edit'

export function PartnerRatesManagement({ roomTypeId, roomTypeName, onManageAvailability }: PartnerRatesManagementProps) {
  const { t } = useI18n()
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
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setError(t('partner.failedToLoadRate'))
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

      setSuccessMessage(t('partner.ratePlanCreatedSuccessfully'))
      setViewMode('list')
      resetForm()
      loadRatePlans()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToCreateRate'))
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

      setSuccessMessage(t('partner.ratePlanUpdatedSuccessfully'))
      setViewMode('list')
      resetForm()
      setSelectedRatePlan(null)
      loadRatePlans()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToUpdateRate'))
      setLoading(false)
    }
  }

  const handleDelete = async (ratePlanId: number) => {
    if (!confirm(t('partner.areYouSureYou2'))) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.deleteRatePlan(ratePlanId)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage(t('partner.ratePlanDeletedSuccessfully'))
      loadRatePlans()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToDeleteRate'))
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
      setError(t('partner.ratePlanNameIs'))
      return false
    }
    if (!formData.slug.trim()) {
      setError(t('partner.slugIsRequired'))
      return false
    }
    if (formData.min_nights < 1) {
      setError(t('partner.minimumNightsMustBe'))
      return false
    }
    if (formData.max_nights < formData.min_nights) {
      setError(t('partner.maximumNightsCannotBe'))
      return false
    }
    if (formData.base_price < 0) {
      setError(t('partner.basePriceMustBe'))
      return false
    }
    if (formData.deposit_required && (formData.deposit_percentage === undefined || formData.deposit_percentage < 0 || formData.deposit_percentage > 100)) {
      setError(t('partner.depositPercentageMustBe'))
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

  const handleInputChange = <K extends keyof CreateRatePlanRequest>(field: K, value: CreateRatePlanRequest[K]) => {
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
          aria-label={t('partner.addNewRatePlan')}
        >
          + {t('partner.addRatePlanButton')}
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
          {t('rooms.loadingRates')}
        </div>
      ) : ratePlans.length === 0 ? (
        <div className="empty-state">
          <p>{t('partner.noRatePlansFound')}</p>
          <p>{t('partner.clickAddRatePlan')}</p>
        </div>
      ) : (
        <div className="rate-plans-grid">
          {ratePlans.map(ratePlan => (
            <div key={ratePlan.id} className="rate-plan-card">
              <div className="rate-plan-card-header">
                <h3 className="rate-plan-name">{ratePlan.name}</h3>
                <div className="rate-plan-badges">
                  <span className={`rate-plan-badge ${ratePlan.is_active ? 'rate-plan-badge--active' : 'rate-plan-badge--inactive'}`}>
                    {ratePlan.is_active ? t('profile.active') : t('profile.inactive')}
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
                    <span className="detail-label">{t('partner.basePrice')}</span>
                    <span className="detail-value">{ratePlan.base_price} {ratePlan.currency}</span>
                  </div>
                  <div className="rate-plan-detail">
                    <span className="detail-label">{t('partner.minMaxNights')}</span>
                    <span className="detail-value">{ratePlan.min_nights} - {ratePlan.max_nights}</span>
                  </div>
                  <div className="rate-plan-detail">
                    <span className="detail-label">{t('partner.cancellation')}</span>
                    <span className="detail-value">{ratePlan.cancellation_policy}</span>
                  </div>
                  {ratePlan.deposit_required && (
                    <div className="rate-plan-detail">
                      <span className="detail-label">{t('partner.deposit')}</span>
                      <span className="detail-value">{ratePlan.deposit_percentage}%</span>
                    </div>
                  )}
                  {ratePlan.advance_booking_days && (
                    <div className="rate-plan-detail">
                      <span className="detail-label">{t('partner.advanceBooking')}</span>
                      <span className="detail-value">{ratePlan.advance_booking_days} days</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="rate-plan-card-footer">
                {onManageAvailability && (
                  <button
                    onClick={() => onManageAvailability({ id: ratePlan.id, name: ratePlan.name })}
                    className="btn btn-primary"
                    aria-label={t('partner.manageAvailabilityFor', { name: ratePlan.name })}
                  >
                    {t('partner.availability')}
                  </button>
                )}
                <button
                  onClick={() => handleEdit(ratePlan)}
                  className="btn btn-secondary"
                  aria-label={t('partner.editNamed', { name: ratePlan.name })}
                >
                  {t('partner.edit')}
                </button>
                <button
                  onClick={() => handleDelete(ratePlan.id)}
                  className="btn btn-danger"
                  aria-label={t('partner.deleteNamed', { name: ratePlan.name })}
                >
                  {t('partner.delete')}
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
          {viewMode === 'create' ? t('partner.createRatePlan') : t('partner.editRatePlan')}
        </h2>
        <button
          onClick={() => {
            setViewMode('list')
            resetForm()
            setSelectedRatePlan(null)
          }}
          className="btn btn-tertiary"
          aria-label={t('partner.cancelAndReturnTo')}
        >
          {t('common.cancel')}
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
          <label htmlFor="rate_name">{t('partner.ratePlanName')}</label>
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
          <label htmlFor="rate_slug">{t('partner.slug')}</label>
          <input
            id="rate_slug"
            type="text"
            value={formData.slug}
            onChange={(e) => handleInputChange('slug', e.target.value.toLowerCase().replace(/\s+/g, '-'))}
            className="form-input"
            required
            aria-required="true"
          />
          <small className="form-hint">{t('partner.urlFriendlyIdentifierE2')}</small>
        </div>

        <div className="form-group">
          <label htmlFor="rate_type">{t('partner.rateType')}</label>
          <select
            id="rate_type"
            value={formData.rate_type}
            onChange={(e) => handleInputChange('rate_type', e.target.value)}
            className="form-input"
            required
            aria-required="true"
          >
            <option value="standard">{t('rate.standard')}</option>
            <option value="non_refundable">{t('rate.non_refundable')}</option>
            <option value="early_bird">{t('rate.early_bird')}</option>
            <option value="last_minute">{t('rate.last_minute')}</option>
            <option value="long_stay">{t('rate.long_stay')}</option>
            <option value="seasonal">{t('rate.seasonal')}</option>
            <option value="corporate">{t('rate.corporate')}</option>
            <option value="promo">{t('partner.promo')}</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="rate_description">{t('partner.description')}</label>
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
            <label htmlFor="base_price">{t('partner.basePrice2')}</label>
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
            <label htmlFor="currency">{t('partner.currency')}</label>
            <select
              id="currency"
              value={formData.currency}
              onChange={(e) => handleInputChange('currency', e.target.value)}
              className="form-input"
              required
              aria-required="true"
            >
              <option value="USD">{t('partner.usdUsDollar')}</option>
              <option value="EUR">{t('partner.eurEuro')}</option>
              <option value="UZS">{t('partner.uzsUzbekistaniSom')}</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="min_nights">{t('partner.minimumNights')}</label>
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
            <label htmlFor="max_nights">{t('partner.maximumNights')}</label>
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
          <label htmlFor="cancellation_policy">{t('partner.cancellationPolicy')}</label>
          <select
            id="cancellation_policy"
            value={formData.cancellation_policy}
            onChange={(e) => handleInputChange('cancellation_policy', e.target.value)}
            className="form-input"
            required
            aria-required="true"
          >
            <option value="flexible">{t('partner.flexible')}</option>
            <option value="moderate">{t('dining.moderate')}</option>
            <option value="strict">{t('policies.strict')}</option>
            <option value="non_refundable">{t('rate.non_refundable')}</option>
          </select>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => handleInputChange('is_active', e.target.checked)}
            />
            <span>{t('profile.active')}</span>
          </label>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={formData.deposit_required}
              onChange={(e) => handleInputChange('deposit_required', e.target.checked)}
            />
            <span>{t('rate.deposit')}</span>
          </label>
        </div>

        {formData.deposit_required && (
          <div className="form-group">
            <label htmlFor="deposit_percentage">{t('partner.depositPercentage')}</label>
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
          <label htmlFor="advance_booking_days">{t('partner.advanceBookingDays')}</label>
          <input
            id="advance_booking_days"
            type="number"
            min="0"
            value={formData.advance_booking_days || ''}
            onChange={(e) => handleInputChange('advance_booking_days', e.target.value ? parseInt(e.target.value) : undefined)}
            className="form-input"
          />
          <small className="form-hint">{t('partner.minimumDaysInAdvance')}</small>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? t('partner.saving') : viewMode === 'create' ? t('partner.createRatePlan') : t('partner.updateRatePlan')}
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
