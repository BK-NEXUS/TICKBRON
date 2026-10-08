import { useState, useEffect } from 'react'
import { Lock, House, Calendar, BedDouble, Banknote } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { partnerAdapter, PartnerProperty } from '../adapters/partnerAdapter'
import { PartnerPropertyWizard } from '../components/PartnerPropertyWizard'
import { PartnerRoomsManagement } from '../components/PartnerRoomsManagement'
import { PartnerRatesManagement } from '../components/PartnerRatesManagement'
import { PartnerAvailabilityManagement } from '../components/PartnerAvailabilityManagement'
import { PartnerRoomCalendar } from '../components/PartnerRoomCalendar'
import { PartnerBookingsView } from '../components/PartnerBookingsView'
import { PartnerStatusTab } from '../components/PartnerStatusTab'
import { EmptyState } from '../components/EmptyState'
import { Crumb, usePageTrail } from '../components/Breadcrumbs'

type DashboardView = 'properties' | 'rooms' | 'rates' | 'availability' | 'calendar' | 'bookings' | 'status' | 'add-property'

/** Hotel name for cards and headings (older API responses have no name: fall back to the city) */
const propertyName = (property: PartnerProperty) => property.name || property.city

export function PartnerDashboardPage() {
  const { user, isAuthenticated } = useAuth()
  const [currentView, setCurrentView] = useState<DashboardView>('properties')
  const [properties, setProperties] = useState<PartnerProperty[]>([])
  const [selectedProperty, setSelectedProperty] = useState<PartnerProperty | null>(null)
  const [selectedRoomType, setSelectedRoomType] = useState<{ id: number; name: string } | null>(null)
  const [selectedRatePlan, setSelectedRatePlan] = useState<{ id: number; name: string } | null>(null)
  const [calendarRoomType, setCalendarRoomType] = useState<{ id: number; name: string; totalRooms: number } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isAuthenticated) {
      loadProperties()
    }
  }, [isAuthenticated])

  const loadProperties = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.getProperties()
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setProperties(response.data)
      }
    } catch (err) {
      setError('Failed to load properties. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handlePropertyCreated = (property: PartnerProperty) => {
    setProperties(prev => [...prev, property])
    setCurrentView('properties')
  }

  const handlePropertySelect = (property: PartnerProperty) => {
    setSelectedProperty(property)
    setCurrentView('rooms')
  }

  const handleBackToProperties = () => {
    setSelectedProperty(null)
    setSelectedRoomType(null)
    setSelectedRatePlan(null)
    setCalendarRoomType(null)
    setCurrentView('properties')
  }

  const handleRoomTypeSelect = (roomType: { id: number; name: string }) => {
    setSelectedRoomType(roomType)
    setSelectedRatePlan(null)
    setCurrentView('rates')
  }

  const handleCalendarSelect = (roomType: { id: number; name: string; totalRooms: number }) => {
    setCalendarRoomType(roomType)
    setCurrentView('calendar')
  }

  const handleRatePlanSelect = (ratePlan: { id: number; name: string }) => {
    setSelectedRatePlan(ratePlan)
    setCurrentView('availability')
  }

  const handleBackToRooms = () => {
    setSelectedRoomType(null)
    setSelectedRatePlan(null)
    setCalendarRoomType(null)
    setCurrentView('rooms')
  }

  const handleBackToRates = () => {
    setSelectedRatePlan(null)
    setCurrentView('rates')
  }

  // Home › Partner Dashboard › Hotel › Room type › Rate plan, shown by the layout's Breadcrumbs.
  // Each level is a button that goes back to that view; Back steps up one level.
  const trail: Crumb[] = [{ label: 'Partner Dashboard' }]
  if (currentView !== 'properties') trail[0] = { label: 'Partner Dashboard', onClick: handleBackToProperties }
  if (currentView === 'add-property') trail.push({ label: 'Add Property' })
  if (currentView === 'bookings') trail.push({ label: 'Bookings' })
  if (currentView === 'status') trail.push({ label: 'Status' })
  if (selectedProperty && ['rooms', 'rates', 'availability', 'calendar'].includes(currentView)) {
    trail.push(currentView === 'rooms'
      ? { label: propertyName(selectedProperty) }
      : { label: propertyName(selectedProperty), onClick: handleBackToRooms })
    if (selectedRoomType && currentView !== 'rooms' && currentView !== 'calendar') {
      trail.push(currentView === 'rates'
        ? { label: selectedRoomType.name }
        : { label: selectedRoomType.name, onClick: handleBackToRates })
    }
    if (selectedRatePlan && currentView === 'availability') trail.push({ label: selectedRatePlan.name })
    if (calendarRoomType && currentView === 'calendar') trail.push({ label: calendarRoomType.name })
  }
  usePageTrail(trail)

  if (!isAuthenticated || !user) {
    return (
      <div className="partner-dashboard-page">
        <div className="container">
          <EmptyState
            icon={<Lock size={40} />}
            title="Authentication required"
            message="Please sign in to access the partner dashboard."
            ctaText="Sign In"
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  const renderNavigation = () => (
    <nav className="partner-dashboard-nav" aria-label="Partner dashboard navigation">
      <button
        onClick={() => setCurrentView('properties')}
        className={`nav-item ${currentView === 'properties' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'properties' ? 'page' : undefined}
      >
        <span className="nav-icon"><House size={18} /></span>
        <span className="nav-label">Properties</span>
      </button>
      <button
        onClick={() => setCurrentView('bookings')}
        className={`nav-item ${currentView === 'bookings' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'bookings' ? 'page' : undefined}
      >
        <span className="nav-icon"><Calendar size={18} /></span>
        <span className="nav-label">Bookings</span>
      </button>
      <button
        onClick={() => setCurrentView('status')}
        className={`nav-item ${currentView === 'status' ? 'nav-item--active' : ''}`}
        aria-current={currentView === 'status' ? 'page' : undefined}
      >
        <span className="nav-icon" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" focusable="false">
            <rect x="1" y="9" width="3" height="6" rx="0.5" />
            <rect x="6.5" y="5" width="3" height="10" rx="0.5" />
            <rect x="12" y="1" width="3" height="14" rx="0.5" />
          </svg>
        </span>
        <span className="nav-label">Status</span>
      </button>
      {selectedProperty && (
        <>
          <button
            onClick={() => setCurrentView('rooms')}
            className={`nav-item ${currentView === 'rooms' ? 'nav-item--active' : ''}`}
            aria-current={currentView === 'rooms' ? 'page' : undefined}
          >
            <span className="nav-icon"><BedDouble size={18} /></span>
            <span className="nav-label">Rooms</span>
          </button>
          {calendarRoomType && (
            <button
              onClick={() => setCurrentView('calendar')}
              className={`nav-item ${currentView === 'calendar' ? 'nav-item--active' : ''}`}
              aria-current={currentView === 'calendar' ? 'page' : undefined}
            >
              <span className="nav-icon"><Calendar size={18} /></span>
              <span className="nav-label">Calendar</span>
            </button>
          )}
          {selectedRoomType && (
            <>
              <button
                onClick={() => setCurrentView('rates')}
                className={`nav-item ${currentView === 'rates' ? 'nav-item--active' : ''}`}
                aria-current={currentView === 'rates' ? 'page' : undefined}
              >
                <span className="nav-icon"><Banknote size={18} /></span>
                <span className="nav-label">Rates</span>
              </button>
              {selectedRatePlan && (
                <button
                  onClick={() => setCurrentView('availability')}
                  className={`nav-item ${currentView === 'availability' ? 'nav-item--active' : ''}`}
                  aria-current={currentView === 'availability' ? 'page' : undefined}
                >
                  <span className="nav-icon"><Calendar size={18} /></span>
                  <span className="nav-label">Availability</span>
                </button>
              )}
            </>
          )}
        </>
      )}
    </nav>
  )

  const renderPropertiesView = () => (
    <div className="partner-properties-view">
      <div className="properties-view-header">
        <h1 className="properties-view-title">My Properties</h1>
        <button
          onClick={() => setCurrentView('add-property')}
          className="btn btn-primary"
          aria-label="Add new property"
        >
          + Add Property
        </button>
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
        <EmptyState
          icon={<House size={40} />}
          title="No properties yet"
          message="Start by listing your first property to begin accepting bookings."
          ctaText="Add Your First Property"
          onClick={() => setCurrentView('add-property')}
        />
      ) : (
        <div className="properties-grid">
          {properties.map(property => (
            <div key={property.id} className="property-card">
              <div className="property-card-header">
                <h3 className="property-card-title">{propertyName(property)}</h3>
                <span className={`property-status property-status--${property.status}`}>
                  {property.status}
                </span>
              </div>
              <div className="property-card-body">
                <p className="property-address">{property.city}, {property.address_line1}</p>
                {property.address_line2 && <p className="property-address">{property.address_line2}</p>}
                <div className="property-details">
                  <div className="property-detail">
                    <span className="detail-label">Guests:</span>
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
                    <span className="detail-value">{property.base_price} {property.currency}</span>
                  </div>
                </div>
                <div className="property-amenities">
                  {property.has_wifi && <span className="amenity-tag">WiFi</span>}
                  {property.has_parking && <span className="amenity-tag">Parking</span>}
                  {property.has_ac && <span className="amenity-tag">AC</span>}
                  {property.has_heating && <span className="amenity-tag">Heating</span>}
                  {property.has_elevator && <span className="amenity-tag">Elevator</span>}
                </div>
              </div>
              <div className="property-card-footer">
                <button
                  onClick={() => handlePropertySelect(property)}
                  className="btn btn-primary"
                  aria-label={`Manage ${propertyName(property)}`}
                >
                  Manage
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const renderCurrentView = () => {
    switch (currentView) {
      case 'properties':
        return renderPropertiesView()
      case 'add-property':
        return (
          <div className="partner-add-property-view">
            <PartnerPropertyWizard
              onSuccess={handlePropertyCreated}
              onCancel={() => setCurrentView('properties')}
            />
          </div>
        )
      case 'rooms':
        return selectedProperty ? (
          <PartnerRoomsManagement
            propertyId={selectedProperty.id}
            propertyName={propertyName(selectedProperty)}
            onManageRates={handleRoomTypeSelect}
            onManageCalendar={handleCalendarSelect}
          />
        ) : null
      case 'calendar':
        return calendarRoomType ? (
          <PartnerRoomCalendar
            roomTypeId={calendarRoomType.id}
            roomTypeName={calendarRoomType.name}
            totalRooms={calendarRoomType.totalRooms}
          />
        ) : null
      case 'rates':
        return selectedRoomType ? (
          <PartnerRatesManagement
            roomTypeId={selectedRoomType.id}
            roomTypeName={selectedRoomType.name}
            onManageAvailability={handleRatePlanSelect}
          />
        ) : null
      case 'availability':
        return selectedRatePlan ? (
          <PartnerAvailabilityManagement
            ratePlanId={selectedRatePlan.id}
            ratePlanName={selectedRatePlan.name}
          />
        ) : null
      case 'bookings':
        return <PartnerBookingsView />
      case 'status':
        return <PartnerStatusTab />
      default:
        return renderPropertiesView()
    }
  }

  return (
    <div className="partner-dashboard-page">
      <div className="container container-large-desktop">
        <div className="dashboard-header">
          <h1 className="dashboard-title">Partner Dashboard</h1>
          <p className="dashboard-subtitle">Welcome, {user.first_name || user.email}</p>
        </div>

        {renderNavigation()}

        <div className="dashboard-content">
          {renderCurrentView()}
        </div>
      </div>
    </div>
  )
}

export default PartnerDashboardPage
