import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { useDialogFocus } from '../hooks/useDialogFocus'
import type { PropertyPhoto } from '../adapters/propertyAdapter'

interface PhotoLightboxProps {
  photos: PropertyPhoto[]
  startIndex: number
  /** Mehmanxana atı, dialog sarlawhası hám jaratılǵan alt teksti ushın */
  name: string
  onClose: () => void
}

/**
 * Mehmanxananıń pútkil ekrandaǵı súwretleri: kóshiw ushın strelkalar yamasa klavishler, jawıw ushın Escape yamasa súwret
 * janına klik.
 */
export function PhotoLightbox({ photos, startIndex, name, onClose }: PhotoLightboxProps) {
  const { t } = useI18n()
  const [index, setIndex] = useState(startIndex)
  const dialogRef = useDialogFocus<HTMLDivElement>(true, onClose)
  const many = photos.length > 1
  const current = photos[index]

  const step = (by: 1 | -1) => setIndex(i => (i + by + photos.length) % photos.length)

  // Lightbox ashıq waqıtta strelka klavishleri súwretler boylap júrgizedi (Escape hám Tab dialogtıń óziki)
  useEffect(() => {
    if (!many) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowRight') step(1)
      else if (event.key === 'ArrowLeft') step(-1)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
    // `step` tek setter di hám dizim uzınlıǵın paydalanadı
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [many, photos.length])

  // Tek bos orınǵa klik onı jabadı, túymege yamasa súwretke klik emes
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
