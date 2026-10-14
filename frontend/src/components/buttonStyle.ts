export type ButtonVariant = 'primary' | 'secondary' | 'tonal' | 'ghost' | 'danger' | 'link'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonStyleProps {
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  className?: string
}

/** The shared class string, also usable on elements that cannot be a Button (for example plain anchors). */
export function buttonClassName({ variant = 'primary', size = 'md', fullWidth, iconOnly, className }: ButtonStyleProps & { iconOnly?: boolean }): string {
  return ['btn', `btn-${variant}`, size !== 'md' && `btn-${size}`, iconOnly && 'btn-icon', fullWidth && 'btn-full', className]
    .filter(Boolean)
    .join(' ')
}
