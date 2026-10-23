import { useState, type FormEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { partnerAdapter, type PartnerProperty } from '../adapters/partnerAdapter'
import { HotelTextsFields } from './HotelTextsFields'
import { hasHotelName, hotelTextsFromApi, hotelTextsToApi, type HotelTextsForm } from '../utils/hotelTexts'

interface PartnerPropertyEditProps {
  property: PartnerProperty
  onSaved: (property: PartnerProperty) => void
}

/** The owner changes the hotel's name, description and address; the place and the status are not editable. */
export function PartnerPropertyEdit({ property, onSaved }: PartnerPropertyEditProps) {
  const { t } = useI18n()
  const [texts, setTexts] = useState<HotelTextsForm>(() => hotelTextsFromApi(property.translations))
  const [address1, setAddress1] = useState(property.address_line1)
  const [address2, setAddress2] = useState(property.address_line2 ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSaved(false)
    if (!hasHotelName(texts)) return setError(t('hotelTexts.nameRequired'))
    if (!address1.trim()) return setError(t('partner.addressLine1Is'))

    setSaving(true)
    setError(null)
    const { data, error: failure } = await partnerAdapter.updateProperty(property.id, {
      translations: hotelTextsToApi(texts),
      address_line1: address1.trim(),
      address_line2: address2.trim(),
    })
    setSaving(false)
    if (failure || !data) return setError(failure ?? t('hotelEdit.failed'))
    setSaved(true)
    onSaved(data)
  }

  return (
    <form className="partner-property-edit" onSubmit={handleSubmit} noValidate>
      <h2>{t('hotelEdit.title')}</h2>
      <HotelTextsFields idPrefix="edit" value={texts} onChange={(next) => { setTexts(next); setSaved(false) }} disabled={saving} />
      <fieldset className="hotel-texts-language" disabled={saving}>
        <legend>{t('partner.address')}</legend>
        <div className="form-group">
          <label htmlFor="edit-address1">{t('partner.addressLine1')}</label>
          <input id="edit-address1" type="text" className="form-input" value={address1}
            onChange={(e) => { setAddress1(e.target.value); setSaved(false) }} aria-required="true" />
        </div>
        <div className="form-group">
          <label htmlFor="edit-address2">{t('partner.addressLine2')}</label>
          <input id="edit-address2" type="text" className="form-input" value={address2}
            onChange={(e) => { setAddress2(e.target.value); setSaved(false) }} />
        </div>
        <p className="form-hint">{t('hotelEdit.placeNote')}</p>
      </fieldset>
      {error && <div className="profile-form-error" role="alert">{error}</div>}
      {saved && <div className="profile-form-success" role="status">{t('hotelEdit.saved')}</div>}
      <button type="submit" className="btn btn-primary" disabled={saving}>
        {saving ? t('hotelEdit.saving') : t('hotelEdit.save')}
      </button>
    </form>
  )
}
