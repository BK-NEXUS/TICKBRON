import { useState } from 'react'
import { partnerAdapter, CreatePropertyRequest } from '../adapters/partnerAdapter'

interface PartnerPropertyWizardProps {
  onSuccess?: (property: any) => void
  onCancel?: () => void
}

type WizardStep = 'basic' | 'location' | 'amenities' | 'pricing' | 'confirm'

export function PartnerPropertyWizard({ onSuccess, onCancel }: PartnerPropertyWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('basic')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<CreatePropertyRequest>({
    property_type: 1, // Default property type (should be selected from a list)
    max_guests: 2,
    bedrooms: 1,
    bathrooms: 1,
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'Uzbekistan',
    latitude: undefined,
    longitude: undefined,
    base_price: 100,
    currency: 'USD',
    total_area: undefined,
    floor_number: undefined,
    has_elevator: false,
    has_parking: false,
    has_wifi: true,
    has_ac: false,
    has_heating: false,
  })

  const handleInputChange = (field: keyof CreatePropertyRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  const validateStep = (step: WizardStep): boolean => {
    switch (step) {
      case 'basic':
        if (!formData.max_guests || formData.max_guests < 1) {
          setError('Max guests must be at least 1')
          return false
        }
        if (!formData.bedrooms || formData.bedrooms < 1) {
          setError('Bedrooms must be at least 1')
          return false
        }
        if (!formData.bathrooms || formData.bathrooms < 1) {
          setError('Bathrooms must be at least 1')
          return false
        }
        return true
      case 'location':
        if (!formData.address_line1.trim()) {
          setError('Address line 1 is required')
          return false
        }
        if (!formData.city.trim()) {
          setError('City is required')
          return false
        }
        if (!formData.country.trim()) {
          setError('Country is required')
          return false
        }
        return true
      case 'amenities':
        return true // No required fields
      case 'pricing':
        if (!formData.base_price || formData.base_price < 0) {
          setError('Base price must be positive')
          return false
        }
        return true
      case 'confirm':
        return true
      default:
        return true
    }
  }

  const handleNext = () => {
    if (!validateStep(currentStep)) return

    const steps: WizardStep[] = ['basic', 'location', 'amenities', 'pricing', 'confirm']
    const currentIndex = steps.indexOf(currentStep)
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1])
    }
  }

  const handleBack = () => {
    const steps: WizardStep[] = ['basic', 'location', 'amenities', 'pricing', 'confirm']
    const currentIndex = steps.indexOf(currentStep)
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1])
    }
  }

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return

    setLoading(true)
    setError(null)

    try {
      const response = await partnerAdapter.createProperty(formData)
      
      if (response.error) {
        setError(response.error)
        setLoading(false)
        return
      }

      if (response.data && onSuccess) {
        onSuccess(response.data)
      }
    } catch (err) {
      setError('Failed to create property. Please try again.')
      setLoading(false)
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 'basic':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">Basic Information</h2>
            <div className="wizard-form">
              <div className="form-group">
                <label htmlFor="max_guests">Max Guests *</label>
                <input
                  id="max_guests"
                  type="number"
                  min="1"
                  value={formData.max_guests}
                  onChange={(e) => handleInputChange('max_guests', parseInt(e.target.value) || 0)}
                  className="form-input"
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="bedrooms">Bedrooms *</label>
                <input
                  id="bedrooms"
                  type="number"
                  min="1"
                  value={formData.bedrooms}
                  onChange={(e) => handleInputChange('bedrooms', parseInt(e.target.value) || 0)}
                  className="form-input"
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="bathrooms">Bathrooms *</label>
                <input
                  id="bathrooms"
                  type="number"
                  min="1"
                  step="0.5"
                  value={formData.bathrooms}
                  onChange={(e) => handleInputChange('bathrooms', parseFloat(e.target.value) || 0)}
                  className="form-input"
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="total_area">Total Area (sq m)</label>
                <input
                  id="total_area"
                  type="number"
                  min="0"
                  value={formData.total_area || ''}
                  onChange={(e) => handleInputChange('total_area', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="floor_number">Floor Number</label>
                <input
                  id="floor_number"
                  type="number"
                  value={formData.floor_number || ''}
                  onChange={(e) => handleInputChange('floor_number', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        )

      case 'location':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">Location Details</h2>
            <div className="wizard-form">
              <div className="form-group">
                <label htmlFor="address_line1">Address Line 1 *</label>
                <input
                  id="address_line1"
                  type="text"
                  value={formData.address_line1}
                  onChange={(e) => handleInputChange('address_line1', e.target.value)}
                  className="form-input"
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="address_line2">Address Line 2</label>
                <input
                  id="address_line2"
                  type="text"
                  value={formData.address_line2}
                  onChange={(e) => handleInputChange('address_line2', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="city">City *</label>
                <input
                  id="city"
                  type="text"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  className="form-input"
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="state">State/Region</label>
                <input
                  id="state"
                  type="text"
                  value={formData.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="postal_code">Postal Code</label>
                <input
                  id="postal_code"
                  type="text"
                  value={formData.postal_code}
                  onChange={(e) => handleInputChange('postal_code', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="country">Country *</label>
                <input
                  id="country"
                  type="text"
                  value={formData.country}
                  onChange={(e) => handleInputChange('country', e.target.value)}
                  className="form-input"
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="latitude">Latitude</label>
                <input
                  id="latitude"
                  type="number"
                  step="any"
                  value={formData.latitude || ''}
                  onChange={(e) => handleInputChange('latitude', e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="longitude">Longitude</label>
                <input
                  id="longitude"
                  type="number"
                  step="any"
                  value={formData.longitude || ''}
                  onChange={(e) => handleInputChange('longitude', e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        )

      case 'amenities':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">Amenities & Features</h2>
            <div className="wizard-form">
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_elevator}
                    onChange={(e) => handleInputChange('has_elevator', e.target.checked)}
                  />
                  <span>Elevator</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_parking}
                    onChange={(e) => handleInputChange('has_parking', e.target.checked)}
                  />
                  <span>Parking</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_wifi}
                    onChange={(e) => handleInputChange('has_wifi', e.target.checked)}
                  />
                  <span>WiFi</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_ac}
                    onChange={(e) => handleInputChange('has_ac', e.target.checked)}
                  />
                  <span>Air Conditioning</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_heating}
                    onChange={(e) => handleInputChange('has_heating', e.target.checked)}
                  />
                  <span>Heating</span>
                </label>
              </div>
            </div>
          </div>
        )

      case 'pricing':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">Pricing</h2>
            <div className="wizard-form">
              <div className="form-group">
                <label htmlFor="base_price">Base Price per Night *</label>
                <input
                  id="base_price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.base_price}
                  onChange={(e) => handleInputChange('base_price', parseFloat(e.target.value) || 0)}
                  className="form-input"
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
                  aria-required="true"
                >
                  <option value="USD">USD - US Dollar</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="UZS">UZS - Uzbekistani Som</option>
                </select>
              </div>
            </div>
          </div>
        )

      case 'confirm':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">Confirm Property Details</h2>
            <div className="wizard-summary">
              <div className="summary-section">
                <h3>Basic Information</h3>
                <p><strong>Max Guests:</strong> {formData.max_guests}</p>
                <p><strong>Bedrooms:</strong> {formData.bedrooms}</p>
                <p><strong>Bathrooms:</strong> {formData.bathrooms}</p>
                {formData.total_area && <p><strong>Total Area:</strong> {formData.total_area} sq m</p>}
                {formData.floor_number && <p><strong>Floor:</strong> {formData.floor_number}</p>}
              </div>
              <div className="summary-section">
                <h3>Location</h3>
                <p><strong>Address:</strong> {formData.address_line1}</p>
                {formData.address_line2 && <p><strong>Address Line 2:</strong> {formData.address_line2}</p>}
                <p><strong>City:</strong> {formData.city}</p>
                {formData.state && <p><strong>State:</strong> {formData.state}</p>}
                {formData.postal_code && <p><strong>Postal Code:</strong> {formData.postal_code}</p>}
                <p><strong>Country:</strong> {formData.country}</p>
                {formData.latitude && formData.longitude && (
                  <p><strong>Coordinates:</strong> {formData.latitude}, {formData.longitude}</p>
                )}
              </div>
              <div className="summary-section">
                <h3>Amenities</h3>
                <ul>
                  {formData.has_elevator && <li>Elevator</li>}
                  {formData.has_parking && <li>Parking</li>}
                  {formData.has_wifi && <li>WiFi</li>}
                  {formData.has_ac && <li>Air Conditioning</li>}
                  {formData.has_heating && <li>Heating</li>}
                </ul>
              </div>
              <div className="summary-section">
                <h3>Pricing</h3>
                <p><strong>Base Price:</strong> {formData.base_price} {formData.currency} per night</p>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  const getStepNumber = () => {
    const steps: WizardStep[] = ['basic', 'location', 'amenities', 'pricing', 'confirm']
    return steps.indexOf(currentStep) + 1
  }

  const getTotalSteps = () => {
    return 5
  }

  return (
    <div className="partner-property-wizard">
      <div className="wizard-header">
        <h1 className="wizard-title">List Your Property</h1>
        <p className="wizard-subtitle">Step {getStepNumber()} of {getTotalSteps()}</p>
        <div className="wizard-progress">
          <div 
            className="wizard-progress-bar" 
            style={{ width: `${(getStepNumber() / getTotalSteps()) * 100}%` }}
            role="progressbar"
            aria-valuenow={getStepNumber()}
            aria-valuemin={1}
            aria-valuemax={getTotalSteps()}
          />
        </div>
      </div>

      {error && (
        <div className="wizard-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {renderStep()}

      <div className="wizard-footer">
        {currentStep !== 'basic' && (
          <button
            type="button"
            onClick={handleBack}
            className="wizard-button wizard-button--secondary"
            disabled={loading}
          >
            Back
          </button>
        )}
        
        {currentStep === 'confirm' ? (
          <button
            type="button"
            onClick={handleSubmit}
            className="wizard-button wizard-button--primary"
            disabled={loading}
          >
            {loading ? 'Creating Property...' : 'Create Property'}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleNext}
            className="wizard-button wizard-button--primary"
            disabled={loading}
          >
            Next
          </button>
        )}

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="wizard-button wizard-button--tertiary"
            disabled={loading}
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}
