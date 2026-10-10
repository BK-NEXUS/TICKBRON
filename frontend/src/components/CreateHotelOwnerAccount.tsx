import { useI18n } from '../i18n/I18nContext'
import { useState } from 'react'
import { generatePassword as randomPassword } from '../utils/generatePassword'
import { adminAdapter, CreateHotelOwnerRequest, CreateHotelOwnerResponse } from '../adapters/adminAdapter'

interface CreateHotelOwnerAccountProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export function CreateHotelOwnerAccount({ onSuccess, onCancel }: CreateHotelOwnerAccountProps) {
  const { t } = useI18n()
  const [formData, setFormData] = useState<CreateHotelOwnerRequest>({
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
    setFormData({ ...formData, [name]: value })
  }

  const validateForm = (): string | null => {
    if (!formData.email.trim()) return t('admin.errEmail')
    if (!formData.first_name.trim()) return t('admin.errFirstName')
    if (!formData.last_name.trim()) return t('admin.errLastName')
    if (!formData.password) return t('admin.errPassword')
    if (formData.password.length < 12) return t('admin.errPasswordShort')
    if (formData.password !== formData.password_confirm) return t('admin.errPasswordMismatch')
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) return t('admin.errEmailInvalid')
    
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setLoading(true)

    try {
      const response = await adminAdapter.createHotelOwner(formData)
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setCreatedCredentials(response.data)
        if (onSuccess) {
          onSuccess()
        }
      }
    } catch (err) {
      setError(t('admin.failedToCreateHotel'))
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
          <h2 className="success-title">{t('admin.hotelOwnerAccountCreated')}</h2>
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
              <li>{t('admin.theHotelOwnerShould')}</li>
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
        <h2 className="form-panel-title">{t('admin.createHotelOwnerAccount')}</h2>
        <p className="form-panel-subtitle">{t('admin.superAdminOnlyCreate')}</p>

        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form-fields">
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
            <label htmlFor="phone_number">{t('admin.phoneNumberOptional')}</label>
            <input
              id="phone_number"
              name="phone_number"
              type="tel"
              value={formData.phone_number}
              onChange={handleChange}
              className="form-control"
              autoComplete="tel"
              placeholder="+998 90 123 4567"
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
                minLength={12}
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
            <small className="form-hint">{t('auth.errorPasswordShort')}</small>
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
              minLength={12}
            />
          </div>

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
            <li>{t('auth.errorPasswordShort')}</li>
            <li>{t('admin.passwordsAreHashedAnd')}</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
