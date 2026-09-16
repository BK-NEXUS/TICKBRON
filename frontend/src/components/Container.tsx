interface ContainerProps {
  children: React.ReactNode
  size?: 'mobile' | 'tablet' | 'desktop' | 'large-desktop' | 'full'
  className?: string
}

/**
 * Responsive container component that adapts to different screen sizes
 * following TICKBRON Plan V4 breakpoints:
 * - 320–767px: mobile
 * - 768–1023px: tablet
 * - 1024–1439px: desktop
 * - 1440px+: large desktop
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
