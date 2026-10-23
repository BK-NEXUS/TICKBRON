import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import type { PhotoApi, PropertyPhoto } from '../adapters/partnerAdapter'
import type { MessageKey } from '../i18n/messages/en'

interface PartnerPhotoManagerProps {
  /** The calls for one hotel or one room type */
  api: PhotoApi
  /** The most photos it can hold (the server enforces it; this only disables the picker) */
  max: number
  /** Unique on the page: the id of the file input and of the heading */
  idPrefix: string
  titleKey: MessageKey
  emptyHintKey: MessageKey
  headingLevel?: 2 | 3
}

/** Photos of one hotel or one room type: upload several, make one the cover, caption, delete. */
export function PartnerPhotoManager({ api, max, idPrefix, titleKey, emptyHintKey, headingLevel = 2 }: PartnerPhotoManagerProps) {
  const { t } = useI18n()
  const Heading = `h${headingLevel}` as const
  const [photos, setPhotos] = useState<PropertyPhoto[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionErrors, setActionErrors] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [captions, setCaptions] = useState<Record<number, string>>({})

  const load = useCallback(async () => {
    setLoading(true)
    const { data, error } = await api.list()
    if (error || !data) {
      setLoadError(error ?? 'Network error')
    } else {
      setLoadError(null)
      setPhotos(data)
      setCaptions(Object.fromEntries(data.map(p => [p.id, p.caption ?? ''])))
    }
    setLoading(false)
  }, [api])

  useEffect(() => { void load() }, [load])

  const run = async (action: () => Promise<string[]>) => {
    setBusy(true)
    setActionErrors(await action())
    await load()
    setBusy(false)
  }

  const handleUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []).slice(0, max - photos.length)
    event.target.value = ''
    if (files.length === 0) return
    void run(async () => {
      const errors: string[] = []
      for (const file of files) {
        const { error } = await api.upload({ photo: file, photo_type: 'other' })
        if (error) errors.push(t('photos.uploadFailed', { name: file.name, error }))
      }
      return errors
    })
  }

  const handleMakeCover = (photo: PropertyPhoto) =>
    run(async () => {
      const { error } = await api.update(photo.id, { is_primary: true })
      return error ? [error] : []
    })

  const handleSaveCaption = (photo: PropertyPhoto) =>
    run(async () => {
      const { error } = await api.update(photo.id, { caption: captions[photo.id] ?? '' })
      return error ? [error] : []
    })

  const handleDelete = (photo: PropertyPhoto) => {
    if (!window.confirm(t('photos.confirmDelete'))) return
    void run(async () => {
      const { error } = await api.remove(photo.id)
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
    <section className="partner-photos" aria-labelledby={`${idPrefix}-title`}>
      <div className="partner-photos-header">
        <Heading id={`${idPrefix}-title`}>{t(titleKey)}</Heading>
        <p className="partner-photos-count">{t('photos.count', { count: photos.length, max })}</p>
      </div>

      <div className="partner-photos-upload">
        <label className="btn btn-primary" htmlFor={`${idPrefix}-input`}>{t('photos.add')}</label>
        <input
          id={`${idPrefix}-input`}
          className="sr-only"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          multiple
          aria-label={t('photos.add')}
          disabled={busy || photos.length >= max}
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
          <p>{t(emptyHintKey)}</p>
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
