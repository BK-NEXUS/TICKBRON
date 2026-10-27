import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { DialogModal as Modal } from './DialogModal'
import { useI18n } from '../i18n/I18nContext'
import { promotionAdapter, type AdPhoto, type AdminPromotion } from '../adapters/promotionAdapter'
import { MAX_AD_PHOTOS } from '../utils/adPhotos'
import { imageFileError } from '../utils/imageFile'
import { promotionErrorKey } from '../utils/promotionErrors'

interface PromotionPhotosDialogProps {
  promotion: AdminPromotion
  /** Only a super admin changes the photos; staff can look */
  canEdit: boolean
  /** Opened right after the ad was created: asks for the photos */
  justCreated?: boolean
  onClose: () => void
  onChanged: () => void
}

/** The pictures of one ad (up to 10): add, remove, and what the site accepts. */
export function PromotionPhotosDialog({ promotion, canEdit, justCreated = false, onClose, onChanged }: PromotionPhotosDialogProps) {
  const { t } = useI18n()
  const [photos, setPhotos] = useState<AdPhoto[]>(promotion.photos)
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  const reload = async () => {
    const result = await promotionAdapter.getPromotionPhotos(promotion.id)
    if (result.data) setPhotos(result.data)
    onChanged()
  }

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []).slice(0, MAX_AD_PHOTOS - photos.length)
    event.target.value = ''
    if (files.length === 0) return
    setBusy(true)
    const problems: string[] = []
    for (const file of files) {
      const wrong = imageFileError(file)
      if (wrong) {
        problems.push(t('promoAdmin.photosUploadFailed', { name: file.name, error: t(wrong) }))
        continue
      }
      const result = await promotionAdapter.uploadPromotionPhoto(promotion.id, file)
      if (result.error) problems.push(t('promoAdmin.photosUploadFailed', { name: file.name, error: t(promotionErrorKey(result.code)) }))
    }
    setErrors(problems)
    await reload()
    setBusy(false)
  }

  const remove = async (photo: AdPhoto) => {
    if (!window.confirm(t('promoAdmin.photosConfirmRemove'))) return
    setBusy(true)
    const result = await promotionAdapter.deletePromotionPhoto(promotion.id, photo.id)
    setErrors(result.error ? [t(promotionErrorKey(result.code))] : [])
    await reload()
    setBusy(false)
  }

  return (
    <Modal titleId="promotion-photos-title" title={t('promoAdmin.photosTitle', { hotel: promotion.property.name })} onClose={onClose}>
      {justCreated && <p className="alert alert-success" role="status">{t('promoAdmin.photosAfterCreate')}</p>}
      <p className="partner-photos-count">{t('promoAdmin.photosCount', { count: photos.length, max: MAX_AD_PHOTOS })}</p>

      {canEdit ? (
        <div className="partner-photos-upload">
          <label className="btn btn-primary" htmlFor="promotion-photos-input">{t('promoAdmin.photosAdd')}</label>
          <input
            id="promotion-photos-input"
            className="sr-only"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            multiple
            aria-label={t('promoAdmin.photosAdd')}
            disabled={busy || photos.length >= MAX_AD_PHOTOS}
            onChange={upload}
          />
          <span className="field-hint">{t('promoAdmin.photosHelp')}</span>
          {busy && <span role="status" aria-live="polite">{t('promoAdmin.photosLoading')}</span>}
        </div>
      ) : (
        <p className="field-hint">{t('promoAdmin.photosReadOnly')}</p>
      )}

      {errors.length > 0 && (
        <div className="alert alert-error" role="alert">
          {errors.map(message => <p key={message}>{message}</p>)}
        </div>
      )}

      {photos.length === 0 ? (
        <p className="empty-state">{t('promoAdmin.photosEmpty')}</p>
      ) : (
        <ul className="promotion-photo-grid">
          {photos.map((photo, index) => (
            <li key={photo.id} className="promotion-photo-item">
              {photo.photo_url && <img src={photo.photo_url} alt="" loading="lazy" />}
              {canEdit && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={busy}
                  aria-label={t('promoAdmin.photosRemove', { number: index + 1 })}
                  onClick={() => void remove(photo)}
                >
                  {t('photos.delete')}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="modal-actions">
        <button type="button" className="btn btn-secondary" onClick={onClose}>{t('promoAdmin.close')}</button>
      </div>
    </Modal>
  )
}
