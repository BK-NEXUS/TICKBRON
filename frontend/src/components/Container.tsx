interface ContainerProps {
  children: React.ReactNode
  size?: 'mobile' | 'tablet' | 'desktop' | 'large-desktop' | 'full'
  className?: string
}

/**
 * Túrli ekran ólshemlerine beyimlesetuǵın responsive konteyner komponenti
 * TICKBRON Plan V4 breakpoint larına muwapıq:
 * - 320–767px: mobil
 * - 768–1023px: planshet
 * - 1024–1439px: kompyuter
 * - 1440px+: úlken kompyuter
 */
export function Container({ 
  children, 
  size = 'desktop',
  className = '' 
}: ContainerProps) {
  const sizeClasses = {
    mobile: 'container-mobile',
    tablet: 'container-tablet',
    desktop: 'container-desktop',
    'large-desktop': 'container-large-desktop',
    full: 'container-full',
  }

  return (
    <div className={`container ${sizeClasses[size]} ${className}`}>
      {children}
    </div>
  )
}
