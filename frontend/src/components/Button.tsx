import { forwardRef } from 'react'
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, MouseEvent, ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router-dom'

export type ButtonVariant = 'primary' | 'secondary' | 'tonal' | 'ghost' | 'danger' | 'link'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface StyleProps {
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  className?: string
}

/** A button shows a label, or only an icon, which then needs an accessible name. */
type Content =
  | { iconOnly?: false; icon?: ReactNode; children: ReactNode }
  | { iconOnly: true; icon: ReactNode; 'aria-label': string; children?: never }

export type ButtonProps = StyleProps & Content & {
  loading?: boolean
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children' | 'className'>

export type ButtonLinkProps = StyleProps & Content & Omit<LinkProps, 'children' | 'className'>
  & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'children' | 'className'>

/** The shared class string, also usable on elements that cannot be a Button (for example plain anchors). */
export function buttonClassName({ variant = 'primary', size = 'md', fullWidth, iconOnly, className }: StyleProps & { iconOnly?: boolean }): string {
  return ['btn', `btn-${variant}`, size !== 'md' && `btn-${size}`, iconOnly && 'btn-icon', fullWidth && 'btn-full', className]
    .filter(Boolean)
    .join(' ')
}

function Spinner() {
  return <span className="btn-spinner" aria-hidden="true" />
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(props, ref) {
  const { variant, size, fullWidth, className, iconOnly, icon, children, loading = false, disabled, onClick, type = 'button', ...rest } = props

  // A loading button stays focusable but swallows clicks, so a form cannot be submitted twice.
  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    if (loading) {
      event.preventDefault()
      return
    }
    onClick?.(event)
  }

  return (
    <button
      {...rest}
      ref={ref}
      type={type}
      className={buttonClassName({ variant, size, fullWidth, iconOnly, className })}
      disabled={disabled}
      aria-busy={loading || undefined}
      aria-disabled={loading || undefined}
      onClick={handleClick}
    >
      {loading ? <Spinner /> : icon}
      {children}
    </button>
  )
})

export function ButtonLink({ variant, size, fullWidth, className, iconOnly, icon, children, ...rest }: ButtonLinkProps) {
  return (
    <Link {...rest} className={buttonClassName({ variant, size, fullWidth, iconOnly, className })}>
      {icon}
      {children}
    </Link>
  )
}
