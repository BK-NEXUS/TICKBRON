import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SegmentedControl } from './SegmentedControl'

const OPTIONS = [
  { value: 'a', label: 'Alpha' },
  { value: 'b', label: 'Beta' },
  { value: 'c', label: 'Gamma' },
] as const

function Harness({ mode }: { mode: 'tabs' | 'toggle' }) {
  const [value, setValue] = useState<'a' | 'b' | 'c'>('a')
  return <SegmentedControl aria-label="Letters" mode={mode} options={OPTIONS} value={value} onChange={setValue} />
}

describe('SegmentedControl', () => {
  it('marks the active option as pressed in toggle mode', async () => {
    render(<Harness mode="toggle" />)
    expect(screen.getByRole('group', { name: 'Letters' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Alpha' })).toHaveAttribute('aria-pressed', 'true')
    await userEvent.click(screen.getByRole('button', { name: 'Beta' }))
    expect(screen.getByRole('button', { name: 'Beta' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Beta' })).toHaveClass('segmented-item--active')
    expect(screen.getByRole('button', { name: 'Alpha' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('reports the chosen value', async () => {
    const onChange = vi.fn()
    render(<SegmentedControl aria-label="Letters" options={OPTIONS} value="a" onChange={onChange} />)
    await userEvent.click(screen.getByRole('button', { name: 'Gamma' }))
    expect(onChange).toHaveBeenCalledWith('c')
  })

  it('is a tablist with a roving tabindex in tabs mode', () => {
    render(<Harness mode="tabs" />)
    expect(screen.getByRole('tablist', { name: 'Letters' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Alpha' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Alpha' })).toHaveAttribute('tabindex', '0')
    expect(screen.getByRole('tab', { name: 'Beta' })).toHaveAttribute('tabindex', '-1')
  })

  it('moves and selects with the arrow keys, Home and End in tabs mode', async () => {
    render(<Harness mode="tabs" />)
    screen.getByRole('tab', { name: 'Alpha' }).focus()
    await userEvent.keyboard('{ArrowRight}')
    expect(screen.getByRole('tab', { name: 'Beta' })).toHaveFocus()
    expect(screen.getByRole('tab', { name: 'Beta' })).toHaveAttribute('aria-selected', 'true')
    await userEvent.keyboard('{End}')
    expect(screen.getByRole('tab', { name: 'Gamma' })).toHaveFocus()
    await userEvent.keyboard('{ArrowRight}')
    expect(screen.getByRole('tab', { name: 'Alpha' })).toHaveFocus()
    await userEvent.keyboard('{ArrowLeft}')
    expect(screen.getByRole('tab', { name: 'Gamma' })).toHaveFocus()
    await userEvent.keyboard('{Home}')
    expect(screen.getByRole('tab', { name: 'Alpha' })).toHaveAttribute('aria-selected', 'true')
  })

  it('moves focus without changing the value in toggle mode', async () => {
    render(<Harness mode="toggle" />)
    screen.getByRole('button', { name: 'Alpha' }).focus()
    await userEvent.keyboard('{ArrowRight}')
    expect(screen.getByRole('button', { name: 'Beta' })).toHaveFocus()
    expect(screen.getByRole('button', { name: 'Alpha' })).toHaveAttribute('aria-pressed', 'true')
  })
})
