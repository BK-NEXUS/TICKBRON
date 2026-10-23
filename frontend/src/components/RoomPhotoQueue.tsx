import { useEffect, useMemo } from 'react'
import type { ChangeEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'

interface RoomPhotoQueueProps {
  files: File[]
  onChange: (files: File[]) => void
  max: number
  disabled?: boolean
}

/** Photos chosen while the room type is not saved yet: they are uploaded right after it is created. */
export function RoomPhotoQueue({ files, onChange, max, disabled }: RoomPhotoQueueProps) {
  const { t } = useI18n()
  const previews = useMemo(
    () => files.map(file => (typeof URL.createObjectURL === 'function' ? URL.createObjectURL(file) : '')),
    [files],
  )
  useEffect(() => () => {
    if (typeof URL.revokeObjectURL === 'function') previews.forEach(url => url && URL.revokeObjectURL(url))
  }, [previews])

  const handlePick = (event: ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(event.target.files ?? [])
    event.target.value = ''
    onChange([...files, ...picked].slice(0, max))
  }

  return (
    <div className="room-photo-queue">
      <div className="partner-photos-upload">
        <label className="btn btn-secondary" htmlFor="room-photo-queue-input">{t('photos.add')}</label>
        <input
          id="room-photo-queue-input"
          className="sr-only"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          multiple
          aria-label={t('photos.add')}
          disabled={disabled || files.length >= max}
          onChange={handlePick}
        />
        <span className="field-hint">{t('roomForm.queueHint')}</span>
      </div>
      {files.length > 0 && (
        <>
          <p className="partner-photos-count">{t('roomForm.queued', { count: files.length, max })}</p>
          <ul className="room-photo-queue-grid">
            {files.map((file, index) => (
              <li key={`${file.name}-${index}`} className="room-photo-queue-item">
                {previews[index] && <img src={previews[index]} alt="" />}
                {index === 0 && <span className="partner-photo-cover">{t('photos.cover')}</span>}
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={disabled}
                  aria-label={t('roomForm.removeQueued', { name: file.name })}
                  onClick={() => onChange(files.filter((_, i) => i !== index))}
                >
                  {t('photos.delete')}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
