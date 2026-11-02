import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { SceneLayer } from './SceneLayer'
import { sceneSettings } from './sceneSettings'

function stubMedia(reduced: boolean, mobile: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: query.includes('reduced-motion') ? reduced : query.includes('max-width') ? mobile : false,
      addEventListener: () => {},
      removeEventListener: () => {},
    })),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
  vi.doUnmock('./Scene')
})

describe('sceneSettings', () => {
  it('uses a coarser blob and a lower dpr on mobile', () => {
    expect(sceneSettings(true)).toEqual({ segments: 48, dpr: 1 })
    expect(sceneSettings(false)).toEqual({ segments: 128, dpr: 1.5 })
  })
})

describe('SceneLayer', () => {
  it('renders only the static backdrop with reduced motion', () => {
    stubMedia(true, false)
    render(<SceneLayer />)
    expect(screen.getByTestId('backdrop')).toBeInTheDocument()
    expect(screen.queryByTestId('scene-loaded')).not.toBeInTheDocument()
  })

  it('keeps the backdrop when the scene fails to load', async () => {
    stubMedia(false, false)
    vi.doMock('./Scene', () => {
      throw new Error('webgl unavailable')
    })
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const { SceneLayer: Fresh } = await import('./SceneLayer')
    render(<Fresh />)
    await waitFor(() => expect(screen.getByTestId('backdrop')).toBeInTheDocument())
    expect(screen.queryByTestId('scene-loaded')).not.toBeInTheDocument()
  })
})
