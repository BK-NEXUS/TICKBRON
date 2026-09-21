import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerDateInventory, CreateDateInventoryRequest, UpdateDateInventoryRequest } from '../adapters/partnerAdapter'

interface PartnerAvailabilityManagementProps {
  ratePlanId: number
  ratePlanName: string
}

type ViewMode = 'list' | 'create' | 'edit'

export function PartnerAvailabilityManagement({ ratePlanId, ratePlanName }: PartnerAvailabilityManagementProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [dateInventory, setDateInventory] = useState<PartnerDateInventory[]>([])
  const [selectedInventory, setSelectedInventory] = useState<PartnerDateInventory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

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
      setError('Failed to load date inventory. Please try again.')
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

      setSuccessMessage('Date inventory created successfully')
      setViewMode('list')
      resetForm()
      loadDateInventory()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to create date inventory. Please try again.')
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

      setSuccessMessage('Date inventory updated successfully')
      setViewMode('list')
      resetForm()
      setSelectedInventory(null)
      loadDateInventory()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to update date inventory. Please try again.')
      setLoading(false)
    }
  }

  const handleDelete = async (inventoryId: number) => {
    if (!confirm('Are you sure you want to delete this date inventory?')) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.deleteDateInventory(inventoryId)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage('Date inventory deleted successfully')
      loadDateInventory()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to delete date inventory. Please try again.')
      setLoading(false)
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
      setError('Date is required')
      return false
    }
    if (formData.available_rooms < 0) {
      setError('Available rooms cannot be negative')
      return false
    }
    if (formData.price < 0) {
      setError('Price must be positive')
      return false
    }
    if (formData.minimum_stay < 1) {
      setError('Minimum stay must be at least 1 night')
      return false
    }
    if (formData.maximum_stay < formData.minimum_stay) {
      setError('Maximum stay cannot be less than minimum stay')
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

  const handleInputChange = (field: keyof CreateDateInventoryRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  const getAvailabilityStatus = (inventory: PartnerDateInventory) => {
    if (!inventory.is_available) return 'Unavailable'
    if (inventory.available_rooms === 0) return 'Fully Booked'
    if (inventory.available_rooms <= 3) return 'Limited'
    return 'Available'
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
        <button
          onClick={() => {
            resetForm()
            setViewMode('create')
          }}
          className="btn btn-primary"
          aria-label="Add new date inventory"
        >
          + Add Date Inventory
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
          Loading date inventory...
        </div>
      ) : dateInventory.length === 0 ? (
        <div className="empty-state">
          <p>No date inventory found for this rate plan.</p>
          <p>Click "Add Date Inventory" to create your first date inventory entry.</p>
        </div>
      ) : (
        <div className="date-inventory-table">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Status</th>
                <th>Available</th>
                <th>Booked</th>
                <th>Price</th>
                <th>Min/Max Stay</th>
                <th>Actions</th>
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
                      aria-label={`Edit inventory for ${inventory.date}`}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(inventory.id)}
                      className="btn btn-danger btn-sm"
                      aria-label={`Delete inventory for ${inventory.date}`}
                    >
                      Delete
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
          {viewMode === 'create' ? 'Create Date Inventory' : 'Edit Date Inventory'}
        </h2>
        <button
          onClick={() => {
            setViewMode('list')
            resetForm()
            setSelectedInventory(null)
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

      <form className="availability-form" onSubmit={(e) => {
        e.preventDefault()
        viewMode === 'create' ? handleCreate() : handleUpdate()
      }}>
        <div className="form-group">
          <label htmlFor="inventory_date">Date *</label>
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
            <small className="form-hint">Date cannot be changed after creation</small>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="available_rooms">Available Rooms *</label>
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
            <label htmlFor="price">Price *</label>
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

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="minimum_stay">Minimum Stay (nights) *</label>
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
            <label htmlFor="maximum_stay">Maximum Stay (nights) *</label>
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
            <span>Available for Booking</span>
          </label>
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            value={formData.notes}
            onChange={(e) => handleInputChange('notes', e.target.value)}
            className="form-input"
            rows={3}
            placeholder="Optional notes about this date (e.g., special events, maintenance, etc.)"
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : viewMode === 'create' ? 'Create Date Inventory' : 'Update Date Inventory'}
          </button>
        </div>
      </form>
    </div>
  )

  return (
    <div className="partner-availability-management">
      {viewMode === 'list' ? renderListView() : renderFormView()}
    </div>
  )
}
