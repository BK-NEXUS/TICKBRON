import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useDialogFocus } from './useDialogFocus'

function Dialog({ onClose }: { onClose: () => void }) {
  const ref = useDialogFocus<HTMLDivElement>(true, onClose)
  return (
    <div ref={ref} role="dialog" aria-modal="true" aria-label="Test dialog" tabIndex={-1}>
      <button>First</button>
      <button>Last</button>
    </div>
  )
}

describe('useDialogFocus', () => {
  it('moves focus into the dialog', () => {
    render(<Dialog onClose={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'First' })).toHaveFocus()
  })

  it('closes on Escape', async () => {
    const onClose = vi.fn()
    render(<Dialog onClose={onClose} />)
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('keeps Tab and Shift+Tab inside the dialog', async () => {
    render(<Dialog onClose={vi.fn()} />)
    await userEvent.tab()
    expect(screen.getByRole('button', { name: 'Last' })).toHaveFocus()
    await userEvent.tab()
    expect(screen.getByRole('button', { name: 'First' })).toHaveFocus()
    await userEvent.tab({ shift: true })
    expect(screen.getByRole('button', { name: 'Last' })).toHaveFocus()
  })

  it('returns focus to the opener when it closes', () => {
    const opener = document.createElement('button')
    document.body.appendChild(opener)
    opener.focus()
    const { unmount } = render(<Dialog onClose={vi.fn()} />)
    unmount()
    expect(opener).toHaveFocus()
    opener.remove()
  })
})
