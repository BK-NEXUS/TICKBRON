import { useRef } from 'react'
import type { KeyboardEvent, ReactNode } from 'react'

export interface SegmentedOption<T extends string> {
  value: T
  label: ReactNode
  ariaLabel?: string
  /** id of the panel this tab controls (tabs only) */
  controls?: string
  className?: string
  activeClassName?: string
}

interface SegmentedControlProps<T extends string> {
  options: readonly SegmentedOption<T>[]
  value: T
  onChange: (value: T) => void
  'aria-label': string
  /** tabs: a tablist whose arrow keys also select; toggle: a group of pressed buttons */
  mode?: 'tabs' | 'toggle'
  className?: string
  /** Stretch over the full width, options share it equally */
  fullWidth?: boolean
  disabled?: boolean
}

const MOVES: Record<string, (index: number, count: number) => number> = {
  ArrowRight: (index, count) => (index + 1) % count,
  ArrowLeft: (index, count) => (index - 1 + count) % count,
  Home: () => 0,
  End: (_index, count) => count - 1,
}

/** White pill container with the active option as a tinted pill. */
export function SegmentedControl<T extends string>({
  options, value, onChange, mode = 'toggle', className, fullWidth, disabled, 'aria-label': ariaLabel,
}: SegmentedControlProps<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  const isTabs = mode === 'tabs'

  const handleKeyDown = (event: KeyboardEvent, index: number) => {
    const move = MOVES[event.key]
    if (!move) return
    event.preventDefault()
    const next = move(index, options.length)
    refs.current[next]?.focus()
    if (isTabs) onChange(options[next].value)
  }

  return (
    <div
      className={['segmented', fullWidth && 'segmented--full', className].filter(Boolean).join(' ')}
      role={isTabs ? 'tablist' : 'group'}
      aria-label={ariaLabel}
    >
      {options.map((option, index) => {
        const active = option.value === value
        const itemClass = ['segmented-item', active && 'segmented-item--active', option.className, active && option.activeClassName]
          .filter(Boolean)
          .join(' ')
        return (
          <button
            key={option.value}
            ref={node => { refs.current[index] = node }}
            type="button"
            disabled={disabled}
            className={itemClass}
            aria-label={option.ariaLabel}
            {...(isTabs
              ? { role: 'tab', 'aria-selected': active, 'aria-controls': option.controls, tabIndex: active ? 0 : -1 }
              : { 'aria-pressed': active })}
            onClick={() => onChange(option.value)}
            onKeyDown={event => handleKeyDown(event, index)}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
