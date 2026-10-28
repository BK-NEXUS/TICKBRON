import { useI18n } from '../i18n/I18nContext'
import { formAccepts } from '../utils/formProblem'
import { useState } from 'react'
import { GeographyPicker, type GeographyValue } from './GeographyPicker'
import { cleanField, isPhoneValid } from '../utils/inputFilters'
import { generatePassword as randomPassword } from '../utils/generatePassword'
import { MIN_PASSWORD_LENGTH, passwordFormatProblem, PASSWORD_PROBLEM_MESSAGE } from '../utils/passwordRules'
import { adminAdapter, CreateHotelOwnerRequest, CreateHotelOwnerResponse } from '../adapters/adminAdapter'

interface CreateHotelOwnerAccountProps {
  /** `owner` (default) picks the place of the hotels; `admin` adds an administrator, which has no place */
  kind?: 'owner' | 'admin'
  onSuccess?: () => void
  onCancel?: () => void
}

const NO_PLACE: GeographyValue = { country_ref: null, region_ref: null, city_ref: null }

export function CreateHotelOwnerAccount({ kind = 'owner', onSuccess, onCancel }: CreateHotelOwnerAccountProps) {
  const { t } = useI18n()
  const isAdmin = kind === 'admin'
  const [place, setPlace] = useState<GeographyValue>(NO_PLACE)
  const [formData, setFormData] = useState<Omit<CreateHotelOwnerRequest, 'country_ref' | 'region_ref' | 'city_ref'>>({
    email: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    password: '',
    password_confirm: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [createdCredentials, setCreatedCredentials] = useState<CreateHotelOwnerResponse | null>(null)

  const generatePassword = () => {
    const password = randomPassword(16)
    setFormData({ ...formData, password, password_confirm: password })
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: cleanField(name, value) })
  }

  const validateForm = (): string | null => {
    if (!isAdmin && (place.country_ref === null || place.region_ref === null || place.city_ref === null)) return t('admin.errPlace')
    if (!formData.email.trim()) return t('admin.errEmail')
    if (!formData.first_name.trim()) return t('admin.errFirstName')
    if (!isPhoneValid(formData.phone_number)) return t('auth.errPhone')
    if (!formData.last_name.trim()) return t('admin.errLastName')
    if (!formData.password) return t('admin.errPassword')
    const passwordProblem = passwordFormatProblem(formData.password)
    if (passwordProblem) return t(PASSWORD_PROBLEM_MESSAGE[passwordProblem])
    if (formData.password !== formData.password_confirm) return t('admin.errPasswordMismatch')
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) return t('admin.errEmailInvalid')
    
    return null
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    if (!formAccepts(e.currentTarget, t, setError)) return

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setLoading(true)

    try {
      const response = isAdmin
        ? await adminAdapter.createAdmin(formData)
        : await adminAdapter.createHotelOwner({
          ...formData,
          country_ref: place.country_ref as number,
          region_ref: place.region_ref as number,
          city_ref: place.city_ref as number,
        })
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setCreatedCredentials(response.data)
        if (onSuccess) {
          onSuccess()
        }
      }
    } catch (err) {
      setError(t(isAdmin ? 'admin.failedToCreateAdmin' : 'admin.failedToCreateHotel'))
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFormData({
      email: '',
      first_name: '',
      last_name: '',
      phone_number: '',
      password: '',
      password_confirm: '',
    })
    setPlace(NO_PLACE)
    setError(null)
    setCreatedCredentials(null)
  }

  const handleCancel = () => {
    if (onCancel) {
      onCancel()
    }
  }

  if (createdCredentials) {
    return (
      <div className="create-hotel-owner-account">
        <div className="success-panel">
          <div className="success-icon">✓</div>
          <h2 className="success-title">{t(isAdmin ? 'admin.adminAccountCreated' : 'admin.hotelOwnerAccountCreated')}</h2>
          <p className="success-subtitle">{t('admin.pleaseShareTheseCredentials')}</p>
          
          <div className="credentials-display">
            <div className="credential-item">
              <span className="credential-label">{t('admin.email')}</span>
              <span className="credential-value">{createdCredentials.email}</span>
            </div>
            <div className="credential-item">
              <span className="credential-label">{t('admin.name2')}</span>
              <span className="credential-value">{createdCredentials.full_name}</span>
            </div>
            <div className="credential-item">
              <span className="credential-label">{t('admin.password')}</span>
              <span className="credential-value password-value">{formData.password}</span>
            </div>
            <div className="credential-item">
              <span className="credential-label">{t('admin.accountId')}</span>
              <span className="credential-value">{createdCredentials.id}</span>
            </div>
          </div>

          <div className="security-notice">
            <p className="notice-title">{t('admin.securityNotice')}</p>
            <ul className="notice-list">
              <li>{t('admin.theseCredentialsAreShown')}</li>
              <li>{t('admin.pleaseSaveThemSecurely')}</li>
              <li>{t(isAdmin ? 'admin.theAdminShould' : 'admin.theHotelOwnerShould')}</li>
              <li>{t('admin.doNotShareThese')}</li>
            </ul>
          </div>

          <div className="success-actions">
            <button onClick={handleReset} className="btn btn-primary">
              {t('admin.createAnotherAccount')}
            </button>
            <button onClick={handleCancel} className="btn btn-secondary">
              {t('admin.close')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="create-hotel-owner-account">
      <div className="form-panel">
        <h2 className="form-panel-title">{t(isAdmin ? 'admin.createAdminAccount' : 'admin.createHotelOwnerAccount')}</h2>
        <p className="form-panel-subtitle">{t('admin.superAdminOnlyCreate')}</p>

        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form-fields" noValidate>
          <div className="form-group">
            <label htmlFor="email">{t('admin.emailAddress')}</label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="email"
              placeholder={t('admin.ownerExampleCom')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="first_name">{t('admin.firstName')}</label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              value={formData.first_name}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="given-name"
              placeholder={t('admin.john')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="last_name">{t('admin.lastName')}</label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              value={formData.last_name}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="family-name"
              placeholder={t('admin.doe')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone_number">{t('auth.phone')}</label>
            <input
              id="phone_number"
              name="phone_number"
              type="tel"
              inputMode="tel"
              value={formData.phone_number}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="tel"
              placeholder="+998 90 123 45 67"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('admin.password')}</label>
            <div className="password-input-group">
              <input
                id="password"
                name="password"
                type="text"
                value={formData.password}
                onChange={handleChange}
                className="form-control"
                required
                autoComplete="new-password"
                placeholder={t('admin.enterPasswordOrGenerate')}
                minLength={MIN_PASSWORD_LENGTH}
              />
              <button
                type="button"
                onClick={generatePassword}
                className="btn btn-secondary password-generate-btn"
                aria-label={t('admin.generateRandomPassword')}
              >
                {t('admin.generate')}
              </button>
            </div>
            <small className="form-hint">{t('auth.passwordHint')}</small>
          </div>

          <div className="form-group">
            <label htmlFor="password_confirm">{t('admin.confirmPassword')}</label>
            <input
              id="password_confirm"
              name="password_confirm"
              type="text"
              value={formData.password_confirm}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="new-password"
              placeholder={t('admin.confirmPassword2')}
              minLength={MIN_PASSWORD_LENGTH}
            />
          </div>

          {!isAdmin && (
            <fieldset className="form-group create-owner-place">
              <legend>{t('admin.whereHotelAppears')}</legend>
              <GeographyPicker value={place} required disabled={loading}
                onChange={next => { setPlace(next); setError(null) }} />
            </fieldset>
          )}

          <div className="form-actions">
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? t('auth.creatingAccount') : t('auth.createAccount')}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              disabled={loading}
              className="btn btn-secondary"
            >
              {t('common.cancel')}
            </button>
          </div>
        </form>

        <div className="security-info">
          <p className="info-title">{t('admin.important')}</p>
          <ul className="info-list">
            <li>{t('admin.onlySuperAdminsCan')}</li>
            <li>{t('admin.credentialsWillBeShown')}</li>
            <li>{t('auth.passwordHint')}</li>
            <li>{t('admin.passwordsAreHashedAnd')}</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
