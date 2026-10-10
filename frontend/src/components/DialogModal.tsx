import type { ReactNode } from 'react'
import { useDialogFocus } from '../hooks/useDialogFocus'

interface DialogModalProps {
  titleId: string
  title: string
  onClose: () => void
  children: ReactNode
}

export function DialogModal({ titleId, title, onClose, children }: DialogModalProps) {
  const dialogRef = useDialogFocus<HTMLDivElement>(true, onClose)
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby={titleId}>
      <div className="modal-content" ref={dialogRef} tabIndex={-1}>
        <h2 id={titleId} className="modal-title">{title}</h2>
        {children}
      </div>
    </div>
  )
}
