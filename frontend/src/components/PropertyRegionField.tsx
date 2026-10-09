import { useI18n } from '../i18n/I18nContext'
import { FormEvent, useEffect, useId, useRef, useState } from 'react'
import { statusAdapter } from '../adapters/statusAdapter'

interface PropertyRegionFieldProps {
  propertyId: number
  /** Current region (the property's `state`); null or blank = "Unspecified" */
  region: string | null | undefined
  onSaved?: (region: string | null) => void
}

/** Admin: set a property's region, used by Status (country > region > hotel) */
export function PropertyRegionField({ propertyId, region, onSaved }: PropertyRegionFieldProps) {
  const { t } = useI18n()
  const id = useId()
  const [saved, setSaved] = useState(region ?? '')
  const [value, setValue] = useState(region ?? '')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Another property, or its region changed elsewhere: start from the new value.
  // Our own save coming back through the props keeps the "Region saved" message.
  const current = useRef(`${propertyId}:${region ?? ''}`)
  useEffect(() => {
    const key = `${propertyId}:${region ?? ''}`
    if (key === current.current) return
    current.current = key
    setSaved(region ?? '')
    setValue(region ?? '')
    setMessage(null)
    setError(null)
  }, [propertyId, region])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const next = value.trim()
    setSaving(true)
    setError(null)
    setMessage(null)
    const response = await statusAdapter.setPropertyRegion(propertyId, next)
    setSaving(false)
    if (response.error) {
      setError(response.error)
      return
    }
    current.current = `${propertyId}:${next}`
    setSaved(next)
    setValue(next)
    setMessage(t('region.regionSaved'))
    onSaved?.(next || null)
  }

  return (
    <form className="property-region-field" onSubmit={handleSubmit}>
      <label htmlFor={`${id}-region`} className="detail-label">{t('region.region')}</label>
      <input
        id={`${id}-region`}
        type="text"
        maxLength={150}
        placeholder={t('region.unspecified')}
        value={value}
        onChange={e => { setValue(e.target.value); setMessage(null) }}
      />
      <button type="submit" className="btn btn-secondary btn-small" disabled={saving || value.trim() === saved}>
        {saving ? t('profile.saving') : t('region.saveRegion')}
      </button>
      {message && <span role="status" className="property-region-saved">{message}</span>}
      {error && <span role="alert" className="property-region-error">{error}</span>}
    </form>
  )
}
