import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import QRCode from 'qrcode'
import { QrCode } from './QrCode'

const URI = 'otpauth://totp/TICKBRON:admin@example.com?secret=JBSWY3DPEHPK3PXP&issuer=TICKBRON'

describe('QrCode', () => {
  it('is a labelled picture for screen readers', () => {
    render(<QrCode value={URI} label="QR code for the authenticator app" />)

    expect(screen.getByRole('img', { name: 'QR code for the authenticator app' })).toBeInTheDocument()
  })

  it('draws exactly the dark squares of the code, inside a 4 module quiet zone', () => {
    render(<QrCode value={URI} label="qr" />)
    const { modules } = QRCode.create(URI, { errorCorrectionLevel: 'M' })
    let dark = 0
    for (let row = 0; row < modules.size; row += 1) {
      for (let column = 0; column < modules.size; column += 1) if (modules.get(row, column)) dark += 1
    }

    const svg = screen.getByRole('img')
    const squares = svg.querySelector('path')?.getAttribute('d')?.match(/M/g) ?? []
    expect(squares).toHaveLength(dark)
    expect(svg.getAttribute('viewBox')).toBe(`0 0 ${modules.size + 8} ${modules.size + 8}`)
  })

  it('stays black on white', () => {
    render(<QrCode value={URI} label="qr" />)

    expect(screen.getByRole('img').querySelector('rect')?.getAttribute('fill')).toBe('#fff')
    expect(screen.getByRole('img').querySelector('path')?.getAttribute('fill')).toBe('#000')
  })
})
