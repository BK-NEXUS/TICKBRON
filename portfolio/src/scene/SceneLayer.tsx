import { lazy, Suspense } from 'react'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { useIsMobile } from '../hooks/useIsMobile'
import { useReducedMotion } from '../hooks/useReducedMotion'
import { useTheme } from '../theme/context'
import { sceneSettings } from './sceneSettings'

const Scene = lazy(() => import('./Scene'))

// The backdrop is always there, so content stays readable if WebGL is missing or fails.
function Backdrop() {
  return <div className="backdrop" data-testid="backdrop" aria-hidden="true" />
}

export function SceneLayer() {
  const reduced = useReducedMotion()
  const isMobile = useIsMobile()
  const settings = sceneSettings(isMobile)
  const { theme } = useTheme()

  return (
    <>
      <Backdrop />
      {!reduced && (
        <ErrorBoundary fallback={null}>
          <Suspense fallback={null}>
            <Scene {...settings} theme={theme} />
          </Suspense>
        </ErrorBoundary>
      )}
    </>
  )
}
