/**
 * Client logo (gold, with a soft shadow) on a transparent background: made from the logo sheet by
 * tools/make_logo.py, so it sits on any page color. Two kinds of artwork: the full lockup with the
 * name for the sign-in pages, and the symbol alone for the header and footer, where the name is
 * written next to it. Each has a dark-theme version (drawn for a dark background); CSS shows the
 * one that matches the theme.
 */
const LOGO_FILES = {
  lockup: { light: '/brand/tickbron-logo.webp', dark: '/brand/tickbron-logo-dark.webp' },
  mark: { light: '/brand/tickbron-mark.webp', dark: '/brand/tickbron-mark-dark.webp' },
} as const

type BrandLogoVariant = 'header' | 'footer' | 'auth'

const ARTWORK: Record<BrandLogoVariant, keyof typeof LOGO_FILES> = {
  header: 'mark',
  footer: 'mark',
  auth: 'lockup',
}

interface BrandLogoProps {
  variant: BrandLogoVariant
  /** Empty alt when a visible "TICKBRON" text sits next to the logo */
  decorative?: boolean
}

export function BrandLogo({ variant, decorative = false }: BrandLogoProps) {
  const files = LOGO_FILES[ARTWORK[variant]]
  const className = `brand-logo brand-logo--${variant}`
  return (
    <>
      <img
        src={files.light}
        alt={decorative ? '' : 'TICKBRON — Online Booking'}
        className={className}
        decoding="async"
      />
      <img src={files.dark} alt="" aria-hidden="true" className={`${className} brand-logo--dark`} decoding="async" />
    </>
  )
}
