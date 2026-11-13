import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { ImageRequirements } from './ImageRequirements'
import { imageProblem } from '../utils/imageFile'

interface RoomPhotoQueueProps {
  files: File[]
  onChange: (files: File[]) => void
  max: number
  disabled?: boolean
}

/** Xona túri ele saqlanbaǵan waqıtta tańlanǵan súwretler: olar xona túri jaratılǵannan keyin birden júklenedi. */
export function RoomPhotoQueue({ files, onChange, max, disabled }: RoomPhotoQueueProps) {
  const { t } = useI18n()
  const [problems, setProblems] = useState<string[]>([])
  const previews = useMemo(
    () => files.map(file => (typeof URL.createObjectURL === 'function' ? URL.createObjectURL(file) : '')),
    [files],
  )
  useEffect(() => () => {
    if (typeof URL.revokeObjectURL === 'function') previews.forEach(url => url && URL.revokeObjectURL(url))
  }, [previews])

  const handlePick = async (event: ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(event.target.files ?? [])
    event.target.value = ''
    const fits: File[] = []
    const refused: string[] = []
    for (const file of picked) {
      const problem = await imageProblem(file, 'room')
      if (problem) refused.push(t('photos.uploadFailed', { name: file.name, error: t(problem.key, problem.params) }))
      else fits.push(file)
    }
    setProblems(refused)
    if (fits.length > 0) onChange([...files, ...fits].slice(0, max))
  }

  return (
    <div className="room-photo-queue">
      <div className="partner-photos-upload">
        <label className="btn btn-secondary" htmlFor="room-photo-queue-input">{t('photos.add')}</label>
        <input
          id="room-photo-queue-input"
          className="sr-only"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          aria-label={t('photos.add')}
          disabled={disabled || files.length >= max}
          onChange={handlePick}
        />
        <span className="field-hint">{t('roomForm.queueHint')}</span>
        <ImageRequirements kind="room" />
      </div>
      {problems.length > 0 && (
        <div className="alert alert-error" role="alert">
          {problems.map(message => <p key={message}>{message}</p>)}
        </div>
      )}
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
