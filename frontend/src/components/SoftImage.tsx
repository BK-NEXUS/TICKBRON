import { useEffect, useRef, useState, type ImgHTMLAttributes } from 'react'

/**
 * A picture that fades in once its file has loaded (the fade is in the CSS and only runs when motion is allowed).
 * A picture the browser already has, or one that fails to load, is shown at once, so the alt text is never hidden.
 */
export function SoftImage({ className, onLoad, onError, ...rest }: ImgHTMLAttributes<HTMLImageElement>) {
  const [loaded, setLoaded] = useState(false)
  const ref = useRef<HTMLImageElement>(null)

  useEffect(() => {
    if (ref.current?.complete) setLoaded(true)
  }, [])

  return (
    <img
      ref={ref}
      {...rest}
      className={['soft-image', loaded ? 'is-loaded' : '', className].filter(Boolean).join(' ')}
      onLoad={event => { setLoaded(true); onLoad?.(event) }}
      onError={event => { setLoaded(true); onError?.(event) }}
    />
  )
}
