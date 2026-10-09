import { useI18n } from '../i18n/I18nContext'
import { useState } from 'react'
import { partnerAdapter, CreatePropertyRequest, PartnerProperty } from '../adapters/partnerAdapter'

interface PartnerPropertyWizardProps {
  onSuccess?: (property: PartnerProperty) => void
  onCancel?: () => void
}

type WizardStep = 'basic' | 'location' | 'amenities' | 'pricing' | 'confirm'

export function PartnerPropertyWizard({ onSuccess, onCancel }: PartnerPropertyWizardProps) {
  const { t } = useI18n()
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

  const handleInputChange = <K extends keyof CreatePropertyRequest>(field: K, value: CreatePropertyRequest[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  const validateStep = (step: WizardStep): boolean => {
    switch (step) {
      case 'basic':
        if (!formData.max_guests || formData.max_guests < 1) {
          setError(t('partner.maxGuestsMustBe'))
          return false
        }
        if (!formData.bedrooms || formData.bedrooms < 1) {
          setError(t('partner.bedroomsMustBeAt'))
          return false
        }
        if (!formData.bathrooms || formData.bathrooms < 1) {
          setError(t('partner.bathroomsMustBeAt'))
          return false
        }
        return true
      case 'location':
        if (!formData.address_line1.trim()) {
          setError(t('partner.addressLine1Is'))
          return false
        }
        if (!formData.city.trim()) {
          setError(t('partner.cityIsRequired'))
          return false
        }
        if (!formData.country.trim()) {
          setError(t('partner.countryIsRequired'))
          return false
        }
        return true
      case 'amenities':
        return true // No required fields
      case 'pricing':
        if (!formData.base_price || formData.base_price < 0) {
          setError(t('partner.basePriceMustBe'))
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
      setError(t('partner.failedToCreateProperty'))
      setLoading(false)
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 'basic':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">{t('partner.basicInformation')}</h2>
            <div className="wizard-form">
              <div className="form-group">
                <label htmlFor="max_guests">{t('partner.maxGuests')}</label>
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
                <label htmlFor="bedrooms">{t('partner.bedrooms2')}</label>
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
                <label htmlFor="bathrooms">{t('partner.bathrooms2')}</label>
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
                <label htmlFor="total_area">{t('partner.totalAreaSqM')}</label>
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
                <label htmlFor="floor_number">{t('partner.floorNumber')}</label>
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
            <h2 className="wizard-step-title">{t('partner.locationDetails')}</h2>
            <div className="wizard-form">
              <div className="form-group">
                <label htmlFor="address_line1">{t('partner.addressLine1')}</label>
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
                <label htmlFor="address_line2">{t('partner.addressLine2')}</label>
                <input
                  id="address_line2"
                  type="text"
                  value={formData.address_line2}
                  onChange={(e) => handleInputChange('address_line2', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="city">{t('partner.city')}</label>
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
                <label htmlFor="state">{t('partner.stateRegion')}</label>
                <input
                  id="state"
                  type="text"
                  value={formData.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="postal_code">{t('partner.postalCode')}</label>
                <input
                  id="postal_code"
                  type="text"
                  value={formData.postal_code}
                  onChange={(e) => handleInputChange('postal_code', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="country">{t('partner.country')}</label>
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
                <label htmlFor="latitude">{t('partner.latitude')}</label>
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
                <label htmlFor="longitude">{t('partner.longitude')}</label>
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
            <h2 className="wizard-step-title">{t('partner.amenitiesFeatures')}</h2>
            <div className="wizard-form">
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_elevator}
                    onChange={(e) => handleInputChange('has_elevator', e.target.checked)}
                  />
                  <span>{t('feature.elevator')}</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_parking}
                    onChange={(e) => handleInputChange('has_parking', e.target.checked)}
                  />
                  <span>{t('feature.parking')}</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_wifi}
                    onChange={(e) => handleInputChange('has_wifi', e.target.checked)}
                  />
                  <span>{t('feature.wifi')}</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_ac}
                    onChange={(e) => handleInputChange('has_ac', e.target.checked)}
                  />
                  <span>{t('feature.ac')}</span>
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.has_heating}
                    onChange={(e) => handleInputChange('has_heating', e.target.checked)}
                  />
                  <span>{t('feature.heating')}</span>
                </label>
              </div>
            </div>
          </div>
        )

      case 'pricing':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">{t('partner.pricing')}</h2>
            <div className="wizard-form">
              <div className="form-group">
                <label htmlFor="base_price">{t('partner.basePricePerNight')}</label>
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
                <label htmlFor="currency">{t('partner.currency')}</label>
                <select
                  id="currency"
                  value={formData.currency}
                  onChange={(e) => handleInputChange('currency', e.target.value)}
                  className="form-input"
                  aria-required="true"
                >
                  <option value="USD">{t('partner.usdUsDollar')}</option>
                  <option value="EUR">{t('partner.eurEuro')}</option>
                  <option value="UZS">{t('partner.uzsUzbekistaniSom')}</option>
                </select>
              </div>
            </div>
          </div>
        )

      case 'confirm':
        return (
          <div className="wizard-step">
            <h2 className="wizard-step-title">{t('partner.confirmPropertyDetails')}</h2>
            <div className="wizard-summary">
              <div className="summary-section">
                <h3>{t('partner.basicInformation')}</h3>
                <p><strong>{t('partner.maxGuests2')}</strong> {formData.max_guests}</p>
                <p><strong>{t('partner.bedrooms')}</strong> {formData.bedrooms}</p>
                <p><strong>{t('partner.bathrooms')}</strong> {formData.bathrooms}</p>
                {formData.total_area && <p><strong>{t('partner.totalArea')}</strong> {formData.total_area} sq m</p>}
                {formData.floor_number && <p><strong>{t('partner.floor')}</strong> {formData.floor_number}</p>}
              </div>
              <div className="summary-section">
                <h3>{t('property.location')}</h3>
                <p><strong>{t('partner.address')}</strong> {formData.address_line1}</p>
                {formData.address_line2 && <p><strong>{t('partner.addressLine22')}</strong> {formData.address_line2}</p>}
                <p><strong>{t('partner.city2')}</strong> {formData.city}</p>
                {formData.state && <p><strong>{t('partner.state')}</strong> {formData.state}</p>}
                {formData.postal_code && <p><strong>{t('partner.postalCode2')}</strong> {formData.postal_code}</p>}
                <p><strong>{t('partner.country2')}</strong> {formData.country}</p>
                {formData.latitude && formData.longitude && (
                  <p><strong>{t('partner.coordinates')}</strong> {formData.latitude}, {formData.longitude}</p>
                )}
              </div>
              <div className="summary-section">
                <h3>{t('filters.amenities')}</h3>
                <ul>
                  {formData.has_elevator && <li>{t('feature.elevator')}</li>}
                  {formData.has_parking && <li>{t('feature.parking')}</li>}
                  {formData.has_wifi && <li>{t('feature.wifi')}</li>}
                  {formData.has_ac && <li>{t('feature.ac')}</li>}
                  {formData.has_heating && <li>{t('feature.heating')}</li>}
                </ul>
              </div>
              <div className="summary-section">
                <h3>{t('partner.pricing')}</h3>
                <p><strong>{t('partner.basePrice')}</strong> {formData.base_price} {formData.currency} per night</p>
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
        <h1 className="wizard-title">{t('partner.listYourProperty')}</h1>
        <p className="wizard-subtitle">{t('partner.stepOf', { step: getStepNumber(), total: getTotalSteps() })}</p>
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
            className="btn btn-secondary"
            disabled={loading}
          >
            {t('crumb.back')}
          </button>
        )}
        
        {currentStep === 'confirm' ? (
          <button
            type="button"
            onClick={handleSubmit}
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? t('partner.creatingProperty') : t('partner.createProperty')}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleNext}
            className="btn btn-primary"
            disabled={loading}
          >
            {t('partner.next')}
          </button>
        )}

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="btn btn-ghost"
            disabled={loading}
          >
            {t('common.cancel')}
          </button>
        )}
      </div>
    </div>
  )
}
