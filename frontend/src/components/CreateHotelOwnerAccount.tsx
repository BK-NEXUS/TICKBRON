import { useState } from 'react'
import { adminAdapter, CreateHotelOwnerRequest, CreateHotelOwnerResponse } from '../adapters/adminAdapter'

interface CreateHotelOwnerAccountProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export function CreateHotelOwnerAccount({ onSuccess, onCancel }: CreateHotelOwnerAccountProps) {
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
    const length = 16
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    let password = ''
    for (let i = 0; i < length; i++) {
      password += charset.charAt(Math.floor(Math.random() * charset.length))
    }
    setFormData({ ...formData, password, password_confirm: password })
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: value })
  }

  const validateForm = (): string | null => {
    if (!formData.email.trim()) return 'Email is required'
    if (!formData.first_name.trim()) return 'First name is required'
    if (!formData.last_name.trim()) return 'Last name is required'
    if (!formData.password) return 'Password is required'
    if (formData.password.length < 12) return 'Password must be at least 12 characters'
    if (formData.password !== formData.password_confirm) return 'Passwords do not match'
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) return 'Please enter a valid email address'
    
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
      setError('Failed to create hotel owner account. Please try again.')
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
          <h2 className="success-title">Hotel Owner Account Created Successfully</h2>
          <p className="success-subtitle">Please share these credentials with the hotel owner</p>
          
          <div className="credentials-display">
            <div className="credential-item">
              <span className="credential-label">Email:</span>
              <span className="credential-value">{createdCredentials.email}</span>
            </div>
            <div className="credential-item">
              <span className="credential-label">Name:</span>
              <span className="credential-value">{createdCredentials.full_name}</span>
            </div>
            <div className="credential-item">
              <span className="credential-label">Password:</span>
              <span className="credential-value password-value">{formData.password}</span>
            </div>
            <div className="credential-item">
              <span className="credential-label">Account ID:</span>
              <span className="credential-value">{createdCredentials.id}</span>
            </div>
          </div>

          <div className="security-notice">
            <p className="notice-title">Security Notice:</p>
            <ul className="notice-list">
              <li>These credentials are shown only once</li>
              <li>Please save them securely before closing this panel</li>
              <li>The hotel owner should change their password after first login</li>
              <li>Do not share these credentials via unsecured channels</li>
            </ul>
          </div>

          <div className="success-actions">
            <button onClick={handleReset} className="btn btn-primary">
              Create Another Account
            </button>
            <button onClick={handleCancel} className="btn btn-secondary">
              Close
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="create-hotel-owner-account">
      <div className="form-panel">
        <h2 className="form-panel-title">Create Hotel Owner Account</h2>
        <p className="form-panel-subtitle">Super-admin only: Create a new hotel owner account</p>

        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form-fields">
          <div className="form-group">
            <label htmlFor="email">Email Address:</label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="email"
              placeholder="owner@example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="first_name">First Name:</label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              value={formData.first_name}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="given-name"
              placeholder="John"
            />
          </div>

          <div className="form-group">
            <label htmlFor="last_name">Last Name:</label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              value={formData.last_name}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="family-name"
              placeholder="Doe"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone_number">Phone Number (optional):</label>
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
            <label htmlFor="password">Password:</label>
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
                placeholder="Enter password or generate one"
                minLength={12}
              />
              <button
                type="button"
                onClick={generatePassword}
                className="btn btn-secondary password-generate-btn"
                aria-label="Generate random password"
              >
                Generate
              </button>
            </div>
            <small className="form-hint">Password must be at least 12 characters</small>
          </div>

          <div className="form-group">
            <label htmlFor="password_confirm">Confirm Password:</label>
            <input
              id="password_confirm"
              name="password_confirm"
              type="text"
              value={formData.password_confirm}
              onChange={handleChange}
              className="form-control"
              required
              autoComplete="new-password"
              placeholder="Confirm password"
              minLength={12}
            />
          </div>

          <div className="form-actions">
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              disabled={loading}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>

        <div className="security-info">
          <p className="info-title">Important:</p>
          <ul className="info-list">
            <li>Only super-admins can create hotel owner accounts</li>
            <li>Credentials will be shown once after creation</li>
            <li>Password must be at least 12 characters</li>
            <li>Passwords are hashed and never stored in plain text</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
