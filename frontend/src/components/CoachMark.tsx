import { useState, useEffect } from 'react'

interface CoachMarkProps {
  featureId: string
  title: string
  message: string
  position?: 'top' | 'bottom' | 'left' | 'right'
  showOnce?: boolean
  onClose?: () => void
}

export function CoachMark({ 
  featureId, 
  title, 
  message, 
  position = 'top',
  showOnce = true,
  onClose 
}: CoachMarkProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Check if this coach mark has been shown before
    const storageKey = `coachmark-${featureId}-shown`
    const hasBeenShown = localStorage.getItem(storageKey)

    if (showOnce) {
      // Only show if never shown before
      if (!hasBeenShown) {
        setIsVisible(true)
      }
    } else {
      // Always show when showOnce is false
      setIsVisible(true)
    }
  }, [featureId, showOnce])

  const handleClose = () => {
    if (showOnce) {
      const storageKey = `coachmark-${featureId}-shown`
      localStorage.setItem(storageKey, 'true')
    }
    setIsVisible(false)
    onClose?.()
  }

  if (!isVisible) {
    return null
  }

  const positionClasses = {
    top: 'coach-mark--top',
    bottom: 'coach-mark--bottom',
    left: 'coach-mark--left',
    right: 'coach-mark--right',
  }

  return (
    <div className={`coach-mark ${positionClasses[position]}`} role="dialog" aria-labelledby={`coachmark-title-${featureId}`}>
      <div className="coach-mark-content">
        <button 
          className="coach-mark-close" 
          onClick={handleClose}
          aria-label="Close coach mark"
        >
          ×
        </button>
        <h3 id={`coachmark-title-${featureId}`} className="coach-mark-title">{title}</h3>
        <p className="coach-mark-message">{message}</p>
      </div>
      <div className="coach-mark-arrow" aria-hidden="true" />
    </div>
  )
}
