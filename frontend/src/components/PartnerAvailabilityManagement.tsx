import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerDateInventory, CreateDateInventoryRequest, UpdateDateInventoryRequest, BulkPriceRequest } from '../adapters/partnerAdapter'

interface PartnerAvailabilityManagementProps {
  ratePlanId: number
  ratePlanName: string
}

type ViewMode = 'list' | 'create' | 'edit' | 'bulk-price'

export function PartnerAvailabilityManagement({ ratePlanId, ratePlanName }: PartnerAvailabilityManagementProps) {
  const { t } = useI18n()
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [dateInventory, setDateInventory] = useState<PartnerDateInventory[]>([])
  const [selectedInventory, setSelectedInventory] = useState<PartnerDateInventory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const [bulkPriceData, setBulkPriceData] = useState<Omit<BulkPriceRequest, 'rate_plan'>>({
    date_from: '',
    date_to: '',
    price: 100,
  })
  const [bulkSaving, setBulkSaving] = useState(false)

  const [formData, setFormData] = useState<CreateDateInventoryRequest>({
    rate_plan: ratePlanId,
    date: '',
    available_rooms: 1,
    price: 100,
    currency: 'USD',
    is_available: true,
    minimum_stay: 1,
    maximum_stay: 30,
    notes: '',
  })

  useEffect(() => {
    loadDateInventory()
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ratePlanId])

  const loadDateInventory = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.getDateInventory()
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        // Filter date inventory for this rate plan
        const ratePlanInventory = response.data.filter(di => di.rate_plan === ratePlanId)
        // Sort by date
        ratePlanInventory.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
        setDateInventory(ratePlanInventory)
      }
    } catch (err) {
      setError(t('partner.failedToLoadDate'))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!validateForm()) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.createDateInventory(formData)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage(t('partner.dateInventoryCreatedSuccessfully'))
      setViewMode('list')
      resetForm()
      loadDateInventory()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToCreateDate'))
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!selectedInventory || !validateForm()) return

    setLoading(true)
    setError(null)

    try {
      const updateData: UpdateDateInventoryRequest = {
        available_rooms: formData.available_rooms,
        price: formData.price,
        currency: formData.currency,
        is_available: formData.is_available,
        minimum_stay: formData.minimum_stay,
        maximum_stay: formData.maximum_stay,
        notes: formData.notes,
      }

      const response = await partnerAdapter.updateDateInventory(selectedInventory.id, updateData)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage(t('partner.dateInventoryUpdatedSuccessfully'))
      setViewMode('list')
      resetForm()
      setSelectedInventory(null)
      loadDateInventory()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToUpdateDate'))
      setLoading(false)
    }
  }

  const handleDelete = async (inventoryId: number) => {
    if (!confirm(t('partner.areYouSureYou3'))) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.deleteDateInventory(inventoryId)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage(t('partner.dateInventoryDeletedSuccessfully'))
      loadDateInventory()

      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToDeleteDate'))
      setLoading(false)
    }
  }

  const handleBulkPriceApply = async () => {
    setBulkSaving(true)
    setError(null)

    try {
      const response = await partnerAdapter.bulkSetPrice({ rate_plan: ratePlanId, ...bulkPriceData })

      if (response.error) {
        setError(response.error)
        setBulkSaving(false)
        return
      }

      setSuccessMessage(t('partner.priceUpdatedForThe'))
      setViewMode('list')
      setBulkSaving(false)
      loadDateInventory()

      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToUpdateThe'))
      setBulkSaving(false)
    }
  }

  const handleEdit = (inventory: PartnerDateInventory) => {
    setSelectedInventory(inventory)
    setFormData({
      rate_plan: ratePlanId,
      date: inventory.date,
      available_rooms: inventory.available_rooms,
      price: inventory.price,
      currency: inventory.currency,
      is_available: inventory.is_available,
      minimum_stay: inventory.minimum_stay,
      maximum_stay: inventory.maximum_stay,
      notes: inventory.notes || '',
    })
    setViewMode('edit')
  }

  const validateForm = (): boolean => {
    if (!formData.date) {
      setError(t('partner.dateIsRequired'))
      return false
    }
    if (formData.available_rooms < 0) {
      setError(t('partner.availableRoomsCannotBe'))
      return false
    }
    if (formData.price < 0) {
      setError(t('partner.priceMustBePositive'))
      return false
    }
    if (formData.minimum_stay < 1) {
      setError(t('partner.minimumStayMustBe'))
      return false
    }
    if (formData.maximum_stay < formData.minimum_stay) {
      setError(t('partner.maximumStayCannotBe'))
      return false
    }
    return true
  }

  const resetForm = () => {
    setFormData({
      rate_plan: ratePlanId,
      date: '',
      available_rooms: 1,
      price: 100,
      currency: 'USD',
      is_available: true,
      minimum_stay: 1,
      maximum_stay: 30,
      notes: '',
    })
  }

  const handleInputChange = <K extends keyof CreateDateInventoryRequest>(field: K, value: CreateDateInventoryRequest[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  const getAvailabilityStatus = (inventory: PartnerDateInventory) => {
    if (!inventory.is_available) return t('partner.unavailable')
    if (inventory.available_rooms === 0) return t('partner.fullyBooked')
    if (inventory.available_rooms <= 3) return t('partner.limited')
    return t('partner.available')
  }

  const getAvailabilityClass = (inventory: PartnerDateInventory) => {
    if (!inventory.is_available) return 'availability-status--unavailable'
    if (inventory.available_rooms === 0) return 'availability-status--fully-booked'
    if (inventory.available_rooms <= 3) return 'availability-status--limited'
    return 'availability-status--available'
  }

  const renderListView = () => (
    <div className="partner-availability-list">
      <div className="availability-list-header">
        <h2 className="availability-list-title">Date Inventory for {ratePlanName}</h2>
        <div className="availability-list-header-actions">
          <button
            onClick={() => {
              setBulkPriceData({ date_from: '', date_to: '', price: 100 })
              setError(null)
              setViewMode('bulk-price')
            }}
            className="btn btn-secondary"
            aria-label={t('partner.bulkPriceFor', { name: ratePlanName })}
          >
            {t('partner.bulkPriceEdit')}
          </button>
          <button
            onClick={() => {
              resetForm()
              setViewMode('create')
            }}
            className="btn btn-primary"
            aria-label={t('partner.addNewDateInventory')}
          >
            + {t('partner.addDateInventoryButton')}
          </button>
        </div>
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
          {t('partner.loadingDateInventory')}
        </div>
      ) : dateInventory.length === 0 ? (
        <div className="empty-state">
          <p>{t('partner.noDateInventoryFound')}</p>
          <p>{t('partner.clickAddDateInventory')}</p>
        </div>
      ) : (
        <div className="date-inventory-table">
          <table>
            <thead>
              <tr>
                <th>{t('partner.date')}</th>
                <th>{t('partner.status')}</th>
                <th>{t('calendar.available')}</th>
                <th>{t('partner.booked')}</th>
                <th>{t('partner.price')}</th>
                <th>{t('partner.minMaxStay')}</th>
                <th>{t('partner.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {dateInventory.map(inventory => (
                <tr key={inventory.id}>
                  <td>{new Date(inventory.date).toLocaleDateString()}</td>
                  <td>
                    <span className={`availability-status ${getAvailabilityClass(inventory)}`}>
                      {getAvailabilityStatus(inventory)}
                    </span>
                  </td>
                  <td>{inventory.available_rooms}</td>
                  <td>{inventory.booked_rooms}</td>
                  <td>{inventory.price} {inventory.currency}</td>
                  <td>{inventory.minimum_stay} - {inventory.maximum_stay} nights</td>
                  <td>
                    <button
                      onClick={() => handleEdit(inventory)}
                      className="btn btn-secondary btn-sm"
                      aria-label={t('partner.editInventoryFor', { date: inventory.date })}
                    >
                      {t('partner.edit')}
                    </button>
                    <button
                      onClick={() => handleDelete(inventory.id)}
                      className="btn btn-danger btn-sm"
                      aria-label={t('partner.deleteInventoryFor', { date: inventory.date })}
                    >
                      {t('partner.delete')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )

  const renderFormView = () => (
    <div className="partner-availability-form">
      <div className="availability-form-header">
        <h2 className="availability-form-title">
          {viewMode === 'create' ? t('partner.createDateInventory') : t('partner.editDateInventory')}
        </h2>
        <button
          onClick={() => {
            setViewMode('list')
            resetForm()
            setSelectedInventory(null)
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

      <form className="availability-form" onSubmit={(e) => {
        e.preventDefault()
        viewMode === 'create' ? handleCreate() : handleUpdate()
      }}>
        <div className="form-group">
          <label htmlFor="inventory_date">{t('partner.date2')}</label>
          <input
            id="inventory_date"
            type="date"
            value={formData.date}
            onChange={(e) => handleInputChange('date', e.target.value)}
            className="form-input"
            required
            aria-required="true"
            disabled={viewMode === 'edit'}
          />
          {viewMode === 'edit' && (
            <small className="form-hint">{t('partner.dateCannotBeChanged')}</small>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="available_rooms">{t('partner.availableRooms')}</label>
            <input
              id="available_rooms"
              type="number"
              min="0"
              value={formData.available_rooms}
              onChange={(e) => handleInputChange('available_rooms', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label htmlFor="price">{t('partner.price2')}</label>
            <input
              id="price"
              type="number"
              min="0"
              step="0.01"
              value={formData.price}
              onChange={(e) => handleInputChange('price', parseFloat(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>
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

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="minimum_stay">{t('partner.minimumStayNights')}</label>
            <input
              id="minimum_stay"
              type="number"
              min="1"
              value={formData.minimum_stay}
              onChange={(e) => handleInputChange('minimum_stay', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label htmlFor="maximum_stay">{t('partner.maximumStayNights')}</label>
            <input
              id="maximum_stay"
              type="number"
              min="1"
              value={formData.maximum_stay}
              onChange={(e) => handleInputChange('maximum_stay', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={formData.is_available}
              onChange={(e) => handleInputChange('is_available', e.target.checked)}
            />
            <span>{t('partner.availableForBooking')}</span>
          </label>
        </div>

        <div className="form-group">
          <label htmlFor="notes">{t('partner.notes')}</label>
          <textarea
            id="notes"
            value={formData.notes}
            onChange={(e) => handleInputChange('notes', e.target.value)}
            className="form-input"
            rows={3}
            placeholder={t('partner.optionalNotesAboutThis')}
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? t('partner.saving') : viewMode === 'create' ? t('partner.createDateInventory') : t('partner.updateDateInventory')}
          </button>
        </div>
      </form>
    </div>
  )

  const renderBulkPriceView = () => (
    <div className="partner-availability-form">
      <div className="availability-form-header">
        <h2 className="availability-form-title">Bulk price edit for {ratePlanName}</h2>
        <button
          onClick={() => setViewMode('list')}
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

      <form className="availability-form" onSubmit={(e) => { e.preventDefault(); handleBulkPriceApply() }}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="bulk_date_from">{t('partner.from')}</label>
            <input
              id="bulk_date_from"
              type="date"
              value={bulkPriceData.date_from}
              onChange={(e) => setBulkPriceData(prev => ({ ...prev, date_from: e.target.value }))}
              className="form-input"
              required
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label htmlFor="bulk_date_to">{t('partner.toExclusive')}</label>
            <input
              id="bulk_date_to"
              type="date"
              value={bulkPriceData.date_to}
              onChange={(e) => setBulkPriceData(prev => ({ ...prev, date_to: e.target.value }))}
              className="form-input"
              required
              aria-required="true"
            />
            <small className="form-hint">{t('partner.theLastNightPriced')}</small>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="bulk_price">{t('partner.nightlyPrice')}</label>
          <input
            id="bulk_price"
            type="number"
            min="0"
            step="0.01"
            value={bulkPriceData.price}
            onChange={(e) => setBulkPriceData(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
            className="form-input"
            required
            aria-required="true"
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={bulkSaving}
          >
            {bulkSaving ? t('partner.applying') : t('partner.apply')}
          </button>
        </div>
      </form>
    </div>
  )

  return (
    <div className="partner-availability-management">
      {viewMode === 'list' && renderListView()}
      {viewMode === 'bulk-price' && renderBulkPriceView()}
      {(viewMode === 'create' || viewMode === 'edit') && renderFormView()}
    </div>
  )
}
