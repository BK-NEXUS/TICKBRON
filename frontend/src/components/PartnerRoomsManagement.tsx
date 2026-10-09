import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerRoomType, CreateRoomTypeRequest, UpdateRoomTypeRequest } from '../adapters/partnerAdapter'

interface PartnerRoomsManagementProps {
  propertyId: number
  propertyName: string
  /** Open the rate plans (and from there availability) of a room type */
  onManageRates?: (roomType: { id: number; name: string }) => void
  /** Open the calendar (RoomInventory + external-booking blocks) of a room type */
  onManageCalendar?: (roomType: { id: number; name: string; totalRooms: number }) => void
}

type ViewMode = 'list' | 'create' | 'edit'

export function PartnerRoomsManagement({ propertyId, propertyName, onManageRates, onManageCalendar }: PartnerRoomsManagementProps) {
  const { t } = useI18n()
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
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setError(t('partner.failedToLoadRoom'))
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

      setSuccessMessage(t('partner.roomTypeCreatedSuccessfully'))
      setViewMode('list')
      resetForm()
      loadRoomTypes()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToCreateRoom'))
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

      setSuccessMessage(t('partner.roomTypeUpdatedSuccessfully'))
      setViewMode('list')
      resetForm()
      setSelectedRoomType(null)
      loadRoomTypes()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToUpdateRoom'))
      setLoading(false)
    }
  }

  const handleDelete = async (roomTypeId: number) => {
    if (!confirm(t('partner.areYouSureYou'))) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.deleteRoomType(roomTypeId)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      setSuccessMessage(t('partner.roomTypeDeletedSuccessfully'))
      loadRoomTypes()
      
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(t('partner.failedToDeleteRoom'))
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
      setError(t('partner.roomNameIsRequired'))
      return false
    }
    if (!formData.slug.trim()) {
      setError(t('partner.slugIsRequired'))
      return false
    }
    if (formData.base_occupancy < 1) {
      setError(t('partner.baseOccupancyMustBe'))
      return false
    }
    if (formData.max_occupancy < formData.base_occupancy) {
      setError(t('partner.maxOccupancyCannotBe'))
      return false
    }
    if (formData.total_rooms < 1) {
      setError(t('partner.totalRoomsMustBe'))
      return false
    }
    if (formData.base_price < 0) {
      setError(t('partner.basePriceMustBe'))
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

  const handleInputChange = <K extends keyof CreateRoomTypeRequest>(field: K, value: CreateRoomTypeRequest[K]) => {
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
          aria-label={t('partner.addNewRoomType')}
        >
          + {t('partner.addRoomTypeButton')}
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
          {t('partner.loadingRoomTypes')}
        </div>
      ) : roomTypes.length === 0 ? (
        <div className="empty-state">
          <p>{t('partner.noRoomTypesFound')}</p>
          <p>{t('partner.clickAddRoomType')}</p>
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
                    <span className="detail-label">{t('partner.occupancy')}</span>
                    <span className="detail-value">{roomType.base_occupancy} - {roomType.max_occupancy} guests</span>
                  </div>
                  <div className="room-type-detail">
                    <span className="detail-label">{t('partner.totalRooms')}</span>
                    <span className="detail-value">{roomType.total_rooms}</span>
                  </div>
                  <div className="room-type-detail">
                    <span className="detail-label">{t('partner.basePrice')}</span>
                    <span className="detail-value">{roomType.base_price} {roomType.currency}</span>
                  </div>
                  {roomType.room_size && (
                    <div className="room-type-detail">
                      <span className="detail-label">{t('partner.roomSize')}</span>
                      <span className="detail-value">{roomType.room_size} sq m</span>
                    </div>
                  )}
                  <div className="room-type-detail">
                    <span className="detail-label">{t('partner.bedConfiguration')}</span>
                    <span className="detail-value">{roomType.bed_configuration}</span>
                  </div>
                </div>
              </div>
              <div className="room-type-card-footer">
                {onManageRates && (
                  <button
                    onClick={() => onManageRates({ id: roomType.id, name: roomType.name })}
                    className="btn btn-primary"
                    aria-label={t('partner.manageRatesFor', { name: roomType.name })}
                  >
                    {t('partner.ratesAndAvailability')}
                  </button>
                )}
                {onManageCalendar && (
                  <button
                    onClick={() => onManageCalendar({ id: roomType.id, name: roomType.name, totalRooms: roomType.total_rooms })}
                    className="btn btn-secondary"
                    aria-label={t('partner.manageCalendarFor', { name: roomType.name })}
                  >
                    {t('partner.calendar')}
                  </button>
                )}
                <button
                  onClick={() => handleEdit(roomType)}
                  className="btn btn-secondary"
                  aria-label={t('partner.editNamed', { name: roomType.name })}
                >
                  {t('partner.edit')}
                </button>
                <button
                  onClick={() => handleDelete(roomType.id)}
                  className="btn btn-danger"
                  aria-label={t('partner.deleteNamed', { name: roomType.name })}
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
    <div className="partner-rooms-form">
      <div className="rooms-form-header">
        <h2 className="rooms-form-title">
          {viewMode === 'create' ? t('partner.createRoomType') : t('partner.editRoomType')}
        </h2>
        <button
          onClick={() => {
            setViewMode('list')
            resetForm()
            setSelectedRoomType(null)
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

      <form className="rooms-form" onSubmit={(e) => {
        e.preventDefault()
        viewMode === 'create' ? handleCreate() : handleUpdate()
      }}>
        <div className="form-group">
          <label htmlFor="room_name">{t('partner.roomName')}</label>
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
          <label htmlFor="room_slug">{t('partner.slug')}</label>
          <input
            id="room_slug"
            type="text"
            value={formData.slug}
            onChange={(e) => handleInputChange('slug', e.target.value.toLowerCase().replace(/\s+/g, '-'))}
            className="form-input"
            required
            aria-required="true"
          />
          <small className="form-hint">{t('partner.urlFriendlyIdentifierE')}</small>
        </div>

        <div className="form-group">
          <label htmlFor="room_description">{t('partner.description')}</label>
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
            <label htmlFor="base_occupancy">{t('partner.baseOccupancy')}</label>
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
            <label htmlFor="max_occupancy">{t('partner.maxOccupancy')}</label>
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
            <label htmlFor="total_rooms">{t('partner.totalRooms2')}</label>
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
            <label htmlFor="room_size">{t('partner.roomSizeSqM')}</label>
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

        <div className="form-group">
          <label htmlFor="bed_configuration">{t('partner.bedConfiguration2')}</label>
          <input
            id="bed_configuration"
            type="text"
            value={formData.bed_configuration}
            onChange={(e) => handleInputChange('bed_configuration', e.target.value)}
            className="form-input"
            placeholder={t('partner.eG1King')}
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
            {loading ? t('partner.saving') : viewMode === 'create' ? t('partner.createRoomType') : t('partner.updateRoomType')}
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
