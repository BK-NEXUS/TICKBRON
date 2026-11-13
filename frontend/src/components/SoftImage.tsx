import { useEffect, useRef, useState, type ImgHTMLAttributes } from 'react'

/**
 * Fayli júklengennen keyin ásten payda bolatuǵın súwret (ásten payda bolıw CSS te hám tek háreketke ruxsat berilgende
 * isleydi).
 * Brauzerde aldınan bar súwret yamasa júklenbegen súwret birden kórsetiledi, sol sebepli alt teksti hesh qashan jasırılmaydı.
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
