import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { useDialogFocus } from '../hooks/useDialogFocus'
import type { PropertyPhoto } from '../adapters/propertyAdapter'

interface PhotoLightboxProps {
  photos: PropertyPhoto[]
  startIndex: number
  /** The property name, for the dialog title and the generated alt text */
  name: string
  onClose: () => void
}

/** The photos of a property full screen: arrows or keys to move, Escape or a click beside the photo to close. */
export function PhotoLightbox({ photos, startIndex, name, onClose }: PhotoLightboxProps) {
  const { t } = useI18n()
  const [index, setIndex] = useState(startIndex)
  const dialogRef = useDialogFocus<HTMLDivElement>(true, onClose)
  const many = photos.length > 1
  const current = photos[index]

  const step = (by: 1 | -1) => setIndex(i => (i + by + photos.length) % photos.length)

  // Arrow keys move through the photos while the lightbox is open (Escape and Tab are the dialog's own)
  useEffect(() => {
    if (!many) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowRight') step(1)
      else if (event.key === 'ArrowLeft') step(-1)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
    // `step` only uses the setter and the list length
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [many, photos.length])

  // Only a click on the empty area closes it, not one on a button or the photo
  const closeOnEmptyArea = (event: React.MouseEvent) => {
    if (event.target === event.currentTarget) onClose()
  }

  const alt = current.alt_text || current.caption || t('gallery.alt', { name, number: index + 1 })

  return (
    <div
      className="lightbox"
      role="dialog"
      aria-modal="true"
      aria-label={t('gallery.fullScreenLabel', { name })}
      data-testid="lightbox-backdrop"
      onClick={closeOnEmptyArea}
    >
      <div className="lightbox-inner" ref={dialogRef} tabIndex={-1} onClick={closeOnEmptyArea}>
        <button type="button" className="lightbox-close" aria-label={t('gallery.close')} onClick={onClose}>
          <X size={24} aria-hidden="true" />
        </button>
        {many && (
          <button type="button" className="lightbox-nav lightbox-nav--prev" aria-label={t('gallery.previous')} onClick={() => step(-1)}>
            <ChevronLeft size={32} aria-hidden="true" />
          </button>
        )}
        <figure className="lightbox-figure">
          <img className="lightbox-image" src={current.photo} alt={alt} />
          {(current.caption || many) && (
            <figcaption className="lightbox-caption">
              {current.caption && <span>{current.caption}</span>}
              {many && <span className="lightbox-counter">{t('gallery.counter', { current: index + 1, total: photos.length })}</span>}
            </figcaption>
          )}
        </figure>
        {many && (
          <button type="button" className="lightbox-nav lightbox-nav--next" aria-label={t('gallery.next')} onClick={() => step(1)}>
            <ChevronRight size={32} aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  )
}
