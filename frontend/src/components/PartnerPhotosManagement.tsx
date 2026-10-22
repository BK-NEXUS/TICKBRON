import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { partnerAdapter } from '../adapters/partnerAdapter'
import type { PropertyPhoto } from '../adapters/partnerAdapter'

interface PartnerPhotosManagementProps {
  propertyId: number
}

// Same as MAX_PHOTOS_PER_PROPERTY on the backend; the server enforces it, this only disables the picker.
const MAX_PHOTOS = 50

export function PartnerPhotosManagement({ propertyId }: PartnerPhotosManagementProps) {
  const { t } = useI18n()
  const [photos, setPhotos] = useState<PropertyPhoto[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionErrors, setActionErrors] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [captions, setCaptions] = useState<Record<number, string>>({})

  const load = useCallback(async () => {
    setLoading(true)
    const { data, error } = await partnerAdapter.getPropertyPhotos(propertyId)
    if (error || !data) {
      setLoadError(error ?? 'Network error')
    } else {
      setLoadError(null)
      setPhotos(data)
      setCaptions(Object.fromEntries(data.map(p => [p.id, p.caption ?? ''])))
    }
    setLoading(false)
  }, [propertyId])

  useEffect(() => { void load() }, [load])

  const run = async (action: () => Promise<string[]>) => {
    setBusy(true)
    setActionErrors(await action())
    await load()
    setBusy(false)
  }

  const handleUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []).slice(0, MAX_PHOTOS - photos.length)
    event.target.value = ''
    if (files.length === 0) return
    void run(async () => {
      const errors: string[] = []
      for (const file of files) {
        const { error } = await partnerAdapter.uploadPropertyPhoto(propertyId, { photo: file, photo_type: 'other' })
        if (error) errors.push(t('photos.uploadFailed', { name: file.name, error }))
      }
      return errors
    })
  }

  const handleMakeCover = (photo: PropertyPhoto) =>
    run(async () => {
      const { error } = await partnerAdapter.updatePropertyPhoto(propertyId, photo.id, { is_primary: true })
      return error ? [error] : []
    })

  const handleSaveCaption = (photo: PropertyPhoto) =>
    run(async () => {
      const { error } = await partnerAdapter.updatePropertyPhoto(propertyId, photo.id, { caption: captions[photo.id] ?? '' })
      return error ? [error] : []
    })

  const handleDelete = (photo: PropertyPhoto) => {
    if (!window.confirm(t('photos.confirmDelete'))) return
    void run(async () => {
      const { error } = await partnerAdapter.deletePropertyPhoto(propertyId, photo.id)
      return error ? [error] : []
    })
  }

  if (loading && photos.length === 0 && !loadError) {
    return <div className="loading-state" role="status" aria-live="polite">{t('photos.loading')}</div>
  }

  if (loadError && photos.length === 0) {
    return (
      <div className="alert alert-error" role="alert">
        <p>{loadError}</p>
        <button type="button" className="btn btn-secondary" onClick={() => void load()}>{t('common.tryAgain')}</button>
      </div>
    )
  }

  return (
    <section className="partner-photos" aria-labelledby="partner-photos-title">
      <div className="partner-photos-header">
        <h2 id="partner-photos-title">{t('photos.title')}</h2>
        <p className="partner-photos-count">{t('photos.count', { count: photos.length, max: MAX_PHOTOS })}</p>
      </div>

      <div className="partner-photos-upload">
        <label className="btn btn-primary" htmlFor="partner-photos-input">{t('photos.add')}</label>
        <input
          id="partner-photos-input"
          className="sr-only"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          multiple
          aria-label={t('photos.add')}
          disabled={busy || photos.length >= MAX_PHOTOS}
          onChange={handleUpload}
        />
        <span className="field-hint">{t('photos.help')}</span>
        {busy && <span role="status" aria-live="polite">{t('photos.uploading')}</span>}
      </div>

      {actionErrors.length > 0 && (
        <div className="alert alert-error" role="alert">
          {actionErrors.map(message => <p key={message}>{message}</p>)}
        </div>
      )}

      {photos.length === 0 ? (
        <div className="empty-state">
          <h3>{t('photos.empty')}</h3>
          <p>{t('photos.emptyHint')}</p>
        </div>
      ) : (
        <ul className="partner-photos-grid">
          {photos.map((photo, index) => (
            <li key={photo.id} className="partner-photo-card">
              <div className="partner-photo-frame">
                <img
                  src={photo.photo_url ?? photo.photo}
                  alt={photo.alt_text || photo.caption || t('photos.alt', { number: index + 1 })}
                  loading="lazy"
                />
                {photo.is_primary && <span className="partner-photo-cover">{t('photos.cover')}</span>}
              </div>
              <label className="partner-photo-caption">
                <span className="detail-label">{t('photos.caption')}</span>
                <input
                  type="text"
                  value={captions[photo.id] ?? ''}
                  maxLength={255}
                  onChange={event => setCaptions(prev => ({ ...prev, [photo.id]: event.target.value }))}
                />
              </label>
              <div className="partner-photo-actions">
                <button type="button" className="btn btn-secondary" disabled={busy}
                  onClick={() => void handleSaveCaption(photo)}>{t('photos.saveCaption')}</button>
                {!photo.is_primary && (
                  <button type="button" className="btn btn-secondary" disabled={busy}
                    onClick={() => void handleMakeCover(photo)}>{t('photos.makeCover')}</button>
                )}
                <button type="button" className="btn btn-danger" disabled={busy}
                  onClick={() => handleDelete(photo)}>{t('photos.delete')}</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
