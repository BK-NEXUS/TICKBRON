import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VipBadge } from './VipBadge'
import { I18nProvider } from '../i18n/I18nContext'

describe('VipBadge', () => {
  beforeEach(() => { localStorage.clear(); localStorage.setItem('tickbron.language', 'en') })

  it('shows "VIP" and tells a screen reader it is a VIP room', () => {
    render(<I18nProvider><VipBadge /></I18nProvider>)
    expect(screen.getByLabelText('VIP room')).toHaveTextContent('VIP')
  })

  it('speaks the page language for the accessible name', () => {
    localStorage.setItem('tickbron.language', 'ru')
    render(<I18nProvider><VipBadge /></I18nProvider>)
    expect(screen.getByLabelText('VIP-номер')).toBeInTheDocument()
  })
})
