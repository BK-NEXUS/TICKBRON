import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerRoomType, CreateRoomTypeRequest, UpdateRoomTypeRequest } from '../adapters/partnerAdapter'

interface PartnerRoomsManagementProps {
  propertyId: number
  propertyName: string
  /** Open the rate plans (and from there availability) of a room type */
  onManageRates?: (roomType: { id: number; name: string }) => void
}

type ViewMode = 'list' | 'create' | 'edit'

export function PartnerRoomsManagement({ propertyId, propertyName, onManageRates }: PartnerRoomsManagementProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [roomTypes, setRoomTypes] = useState<PartnerRoomType[]>([])
  const [selectedRoomType, setSelectedRoomType] = useState<PartnerRoomType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const [formData, setFormData] = useState<CreateRoomTypeRequest>({
    property: propertyId,
    name: '',
    slug: '',
    description: '',
    base_occupancy: 1,
    max_occupancy: 2,
    base_price: 100,
    currency: 'USD',
    total_rooms: 1,
    bed_configuration: '',
    room_size: undefined,
  })

  useEffect(() => {
    loadRoomTypes()
  }, [propertyId])

  const loadRoomTypes = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.getRoomTypes()
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        // Filter room types for this property
        const propertyRoomTypes = response.data.filter(rt => rt.property === propertyId)
        setRoomTypes(propertyRoomTypes)
      }
    } catch (err) {
      setError('Failed to load room types. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!validateForm()) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.createRoomType(formData)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage('Room type created successfully')
      setViewMode('list')
      resetForm()
      loadRoomTypes()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to create room type. Please try again.')
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!selectedRoomType || !validateForm()) return

    setLoading(true)
    setError(null)

    try {
      const updateData: UpdateRoomTypeRequest = {
        name: formData.name,
        slug: formData.slug,
        description: formData.description,
        base_occupancy: formData.base_occupancy,
        max_occupancy: formData.max_occupancy,
        base_price: formData.base_price,
        currency: formData.currency,
        total_rooms: formData.total_rooms,
        bed_configuration: formData.bed_configuration,
        room_size: formData.room_size,
      }

      const response = await partnerAdapter.updateRoomType(selectedRoomType.id, updateData)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage('Room type updated successfully')
      setViewMode('list')
      resetForm()
      setSelectedRoomType(null)
      loadRoomTypes()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to update room type. Please try again.')
      setLoading(false)
    }
  }

  const handleDelete = async (roomTypeId: number) => {
    if (!confirm('Are you sure you want to delete this room type?')) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.deleteRoomType(roomTypeId)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage('Room type deleted successfully')
      loadRoomTypes()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Failed to delete room type. Please try again.')
      setLoading(false)
    }
  }

  const handleEdit = (roomType: PartnerRoomType) => {
    setSelectedRoomType(roomType)
    setFormData({
      property: propertyId,
      name: roomType.name,
      slug: roomType.slug,
      description: roomType.description,
      base_occupancy: roomType.base_occupancy,
      max_occupancy: roomType.max_occupancy,
      base_price: roomType.base_price,
      currency: roomType.currency,
      total_rooms: roomType.total_rooms,
      bed_configuration: roomType.bed_configuration,
      room_size: roomType.room_size,
    })
    setViewMode('edit')
  }

  const validateForm = (): boolean => {
    if (!formData.name.trim()) {
      setError('Room name is required')
      return false
    }
    if (!formData.slug.trim()) {
      setError('Slug is required')
      return false
    }
    if (formData.base_occupancy < 1) {
      setError('Base occupancy must be at least 1')
      return false
    }
    if (formData.max_occupancy < formData.base_occupancy) {
      setError('Max occupancy cannot be less than base occupancy')
      return false
    }
    if (formData.total_rooms < 1) {
      setError('Total rooms must be at least 1')
      return false
    }
    if (formData.base_price < 0) {
      setError('Base price must be positive')
      return false
    }
    return true
  }

  const resetForm = () => {
    setFormData({
      property: propertyId,
      name: '',
      slug: '',
      description: '',
      base_occupancy: 1,
      max_occupancy: 2,
      base_price: 100,
      currency: 'USD',
      total_rooms: 1,
      bed_configuration: '',
      room_size: undefined,
    })
  }

  const handleInputChange = (field: keyof CreateRoomTypeRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  const renderListView = () => (
    <div className="partner-rooms-list">
      <div className="rooms-list-header">
        <h2 className="rooms-list-title">Room Types for {propertyName}</h2>
        <button
          onClick={() => {
            resetForm()
            setViewMode('create')
          }}
          className="btn btn-primary"
          aria-label="Add new room type"
        >
          + Add Room Type
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
          Loading room types...
        </div>
      ) : roomTypes.length === 0 ? (
        <div className="empty-state">
          <p>No room types found for this property.</p>
          <p>Click "Add Room Type" to create your first room type.</p>
        </div>
      ) : (
        <div className="room-types-grid">
          {roomTypes.map(roomType => (
            <div key={roomType.id} className="room-type-card">
              <div className="room-type-card-header">
                <h3 className="room-type-name">{roomType.name}</h3>
                <span className="room-type-slug">{roomType.slug}</span>
              </div>
              <div className="room-type-card-body">
                <p className="room-type-description">{roomType.description}</p>
                <div className="room-type-details">
                  <div className="room-type-detail">
                    <span className="detail-label">Occupancy:</span>
                    <span className="detail-value">{roomType.base_occupancy} - {roomType.max_occupancy} guests</span>
                  </div>
                  <div className="room-type-detail">
                    <span className="detail-label">Total Rooms:</span>
                    <span className="detail-value">{roomType.total_rooms}</span>
                  </div>
                  <div className="room-type-detail">
                    <span className="detail-label">Base Price:</span>
                    <span className="detail-value">{roomType.base_price} {roomType.currency}</span>
                  </div>
                  {roomType.room_size && (
                    <div className="room-type-detail">
                      <span className="detail-label">Room Size:</span>
                      <span className="detail-value">{roomType.room_size} sq m</span>
                    </div>
                  )}
                  <div className="room-type-detail">
                    <span className="detail-label">Bed Configuration:</span>
                    <span className="detail-value">{roomType.bed_configuration}</span>
                  </div>
                </div>
              </div>
              <div className="room-type-card-footer">
                {onManageRates && (
                  <button
                    onClick={() => onManageRates({ id: roomType.id, name: roomType.name })}
                    className="btn btn-primary"
                    aria-label={`Manage rates and availability for ${roomType.name}`}
                  >
                    Rates &amp; availability
                  </button>
                )}
                <button
                  onClick={() => handleEdit(roomType)}
                  className="btn btn-secondary"
                  aria-label={`Edit ${roomType.name}`}
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(roomType.id)}
                  className="btn btn-danger"
                  aria-label={`Delete ${roomType.name}`}
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
    <div className="partner-rooms-form">
      <div className="rooms-form-header">
        <h2 className="rooms-form-title">
          {viewMode === 'create' ? 'Create Room Type' : 'Edit Room Type'}
        </h2>
        <button
          onClick={() => {
            setViewMode('list')
            resetForm()
            setSelectedRoomType(null)
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

      <form className="rooms-form" onSubmit={(e) => {
        e.preventDefault()
        viewMode === 'create' ? handleCreate() : handleUpdate()
      }}>
        <div className="form-group">
          <label htmlFor="room_name">Room Name *</label>
          <input
            id="room_name"
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className="form-input"
            required
            aria-required="true"
          />
        </div>

        <div className="form-group">
          <label htmlFor="room_slug">Slug *</label>
          <input
            id="room_slug"
            type="text"
            value={formData.slug}
            onChange={(e) => handleInputChange('slug', e.target.value.toLowerCase().replace(/\s+/g, '-'))}
            className="form-input"
            required
            aria-required="true"
          />
          <small className="form-hint">URL-friendly identifier (e.g., "deluxe-suite")</small>
        </div>

        <div className="form-group">
          <label htmlFor="room_description">Description</label>
          <textarea
            id="room_description"
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className="form-input"
            rows={3}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="base_occupancy">Base Occupancy *</label>
            <input
              id="base_occupancy"
              type="number"
              min="1"
              value={formData.base_occupancy}
              onChange={(e) => handleInputChange('base_occupancy', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label htmlFor="max_occupancy">Max Occupancy *</label>
            <input
              id="max_occupancy"
              type="number"
              min="1"
              value={formData.max_occupancy}
              onChange={(e) => handleInputChange('max_occupancy', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="total_rooms">Total Rooms *</label>
            <input
              id="total_rooms"
              type="number"
              min="1"
              value={formData.total_rooms}
              onChange={(e) => handleInputChange('total_rooms', parseInt(e.target.value) || 0)}
              className="form-input"
              required
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label htmlFor="room_size">Room Size (sq m)</label>
            <input
              id="room_size"
              type="number"
              min="0"
              value={formData.room_size || ''}
              onChange={(e) => handleInputChange('room_size', e.target.value ? parseInt(e.target.value) : undefined)}
              className="form-input"
            />
          </div>
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

        <div className="form-group">
          <label htmlFor="bed_configuration">Bed Configuration *</label>
          <input
            id="bed_configuration"
            type="text"
            value={formData.bed_configuration}
            onChange={(e) => handleInputChange('bed_configuration', e.target.value)}
            className="form-input"
            placeholder="e.g., 1 King Bed, 2 Queen Beds"
            required
            aria-required="true"
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : viewMode === 'create' ? 'Create Room Type' : 'Update Room Type'}
          </button>
        </div>
      </form>
    </div>
  )

  return (
    <div className="partner-rooms-management">
      {viewMode === 'list' ? renderListView() : renderFormView()}
    </div>
  )
}
