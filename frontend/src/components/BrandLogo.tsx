/**
 * Mijoz logotipi (altın, jumsaq kóleńke menen) tiniq fonda: logotip betinen
 * tools/make_logo.py arqalı jasalǵan, sol sebepli qálegen bet reńine otıradı. Eki túrli dizayn: kirisiw betleri ushın atı bar
 * tolıq lockup, hám header hám footer ushın tek belgi, olarda atı janında
 * jazıladı. Hárbirinde qarańǵı tema nusqası bar (qarańǵı fonǵa salınǵan); CSS temaǵa
 * sáykes keletuǵının kórsetedi.
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
  /** Logotip janında kórinetuǵın "TICKBRON" teksti bar bolsa bos alt */
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
