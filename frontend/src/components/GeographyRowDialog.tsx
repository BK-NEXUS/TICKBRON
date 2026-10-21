import { ChangeEvent, FormEvent, useEffect, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { adminGeographyAdapter, type AdminGeographyRow, type GeographyKind } from '../adapters/adminGeographyAdapter'
import { DialogModal } from './DialogModal'
import { imageFileError } from '../utils/imageFile'

const NAME_FIELDS = ['name_uz', 'name_ru', 'name_en'] as const

interface GeographyRowDialogProps {
  kind: GeographyKind
  /** The open country (for a region) or region (for a city); null for a country */
  parentId: number | null
  /** The row being edited; absent when adding */
  row?: AdminGeographyRow
  onSaved: () => void
  onClose: () => void
}

/** Add or edit one country, region or city. The code, currency and parent are set only when adding. */
export function GeographyRowDialog({ kind, parentId, row, onSaved, onClose }: GeographyRowDialogProps) {
  const { t } = useI18n()
  const id = useId()
  const [names, setNames] = useState({
    name_uz: row?.name_uz ?? '', name_ru: row?.name_ru ?? '', name_en: row?.name_en ?? '',
  })
  const [code, setCode] = useState('')
  const [currency, setCurrency] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const hasPicture = kind !== 'cities'
  const currentPicture = row && 'image_url' in row ? row.image_url : null

  useEffect(() => {
    if (!image) { setPreview(null); return undefined }
    const url = URL.createObjectURL(image)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [image])

  const handlePicture = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null
    const problem = file ? imageFileError(file) : null
    setImage(problem ? null : file)
    setError(problem ? t(problem) : null)
  }

  const parentField = kind === 'regions' ? { country: parentId as number } : kind === 'cities' ? { region: parentId as number } : {}
  const picture = image ? { image } : {}
  const createBody = kind === 'countries' ? { code, currency, ...names, ...picture } : { ...parentField, ...names, ...picture }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (hasPicture && !row && !image) {
      setError(t('geoAdmin.errImageRequired'))
      return
    }
    setSaving(true)
    setError(null)
    const result = row
      ? await adminGeographyAdapter.update(kind, row.id, { ...names, ...picture })
      : await adminGeographyAdapter.create(kind, createBody)
    setSaving(false)
    if (result.error) {
      setError(result.error)
      return
    }
    onSaved()
  }

  const title = t(row ? `geoAdmin.edit.${kind}` : `geoAdmin.new.${kind}`)

  return (
    <DialogModal titleId={`${id}-title`} title={title} onClose={onClose}>
      <form onSubmit={handleSubmit} className="geography-row-form">
        {!row && kind === 'countries' && (
          <>
            <div className="form-group">
              <label htmlFor={`${id}-code`}>{t('geoAdmin.field.code')}</label>
              <input id={`${id}-code`} className="form-input" maxLength={2} required value={code}
                onChange={e => setCode(e.target.value)} />
            </div>
            <div className="form-group">
              <label htmlFor={`${id}-currency`}>{t('geoAdmin.field.currency')}</label>
              <input id={`${id}-currency`} className="form-input" maxLength={3} required value={currency}
                onChange={e => setCurrency(e.target.value)} />
            </div>
          </>
        )}
        {NAME_FIELDS.map(field => (
          <div className="form-group" key={field}>
            <label htmlFor={`${id}-${field}`}>{t(`geoAdmin.field.${field}`)}</label>
            <input id={`${id}-${field}`} className="form-input" maxLength={100} required value={names[field]}
              onChange={e => setNames(prev => ({ ...prev, [field]: e.target.value }))} />
          </div>
        ))}
        {hasPicture && (
          <div className="form-group geography-picture">
            <label htmlFor={`${id}-image`}>{t('geoAdmin.field.image')}</label>
            <input id={`${id}-image`} className="form-input" type="file" accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={handlePicture} />
            <span className="field-hint">{t('geoAdmin.imageHelp')}</span>
            {(preview || currentPicture) && (
              <img className="geography-picture-preview" src={preview ?? currentPicture ?? ''} alt={t('geoAdmin.imagePreview')} />
            )}
          </div>
        )}
        {error && <p role="alert" className="geography-picker-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>{t('geoAdmin.cancel')}</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? t('geoAdmin.saving') : t('geoAdmin.save')}
          </button>
        </div>
      </form>
    </DialogModal>
  )
}
