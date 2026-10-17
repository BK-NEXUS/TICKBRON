import { useEffect, useRef, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { statusAdapter } from '../adapters/statusAdapter'
import { GeographyPicker, type GeographyValue } from './GeographyPicker'

interface PropertyLocationFieldProps {
  propertyId: number
  /** Saved location; all three null = "Unspecified" */
  location: GeographyValue
  onSaved?: (location: GeographyValue) => void
}

const keyOf = (propertyId: number, location: GeographyValue) =>
  `${propertyId}:${location.country_ref}:${location.region_ref}:${location.city_ref}`

const sameLocation = (a: GeographyValue, b: GeographyValue) =>
  a.country_ref === b.country_ref && a.region_ref === b.region_ref && a.city_ref === b.city_ref

/** A location is whole (all three ids) or cleared (none): the backend refuses anything in between. */
const isComplete = (value: GeographyValue) =>
  (value.country_ref === null) === (value.region_ref === null) && (value.region_ref === null) === (value.city_ref === null)

/** Admin: set a property's country, region and city, used by Status (country > region > hotel). */
export function PropertyLocationField({ propertyId, location, onSaved }: PropertyLocationFieldProps) {
  const { t } = useI18n()
  const [saved, setSaved] = useState(location)
  const [value, setValue] = useState(location)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Another property, or its location changed elsewhere: start from the new value.
  // Our own save coming back through the props keeps the "Location saved" message.
  const current = useRef(keyOf(propertyId, location))
  useEffect(() => {
    const key = keyOf(propertyId, location)
    if (key === current.current) return
    current.current = key
    setSaved(location)
    setValue(location)
    setMessage(null)
    setError(null)
  }, [propertyId, location])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setMessage(null)
    const response = await statusAdapter.setPropertyLocation(propertyId, value)
    setSaving(false)
    if (response.error) {
      setError(response.error)
      return
    }
    current.current = keyOf(propertyId, value)
    setSaved(value)
    setMessage(t('location.saved'))
    onSaved?.(value)
  }

  return (
    <div className="property-region-field">
      <GeographyPicker value={value} onChange={next => { setValue(next); setMessage(null) }} />
      <button
        type="button"
        className="btn btn-secondary btn-small"
        disabled={saving || sameLocation(value, saved) || !isComplete(value)}
        onClick={handleSave}
      >
        {saving ? t('profile.saving') : t('location.save')}
      </button>
      {message && <span role="status" className="property-region-saved">{message}</span>}
      {error && <span role="alert" className="property-region-error">{error}</span>}
    </div>
  )
}
