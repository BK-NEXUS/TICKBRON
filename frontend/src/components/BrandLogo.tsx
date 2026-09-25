/**
 * Client logo. The file is the only place the image is referenced: to switch to a
 * transparent, SVG or horizontal version, replace the file (or change BRAND_LOGO_SRC).
 * The current JPG has a cream paper background, so place it on a cream
 * (--color-background-alt) area so its edges do not show as a box.
 */
export const BRAND_LOGO_SRC = '/brand/tickbron-logo.jpg'

type BrandLogoVariant = 'header' | 'footer' | 'auth'

interface BrandLogoProps {
  variant: BrandLogoVariant
  /** Empty alt when a visible "TICKBRON" text sits next to the logo */
  decorative?: boolean
}

export function BrandLogo({ variant, decorative = false }: BrandLogoProps) {
  return (
    <img
      src={BRAND_LOGO_SRC}
      alt={decorative ? '' : 'TICKBRON — Online Booking'}
      className={`brand-logo brand-logo--${variant}`}
      decoding="async"
    />
  )
}
