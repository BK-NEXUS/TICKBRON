import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { SATELLITE_URL, TILE_URL } from './components/mapTiles'

const REPO = join(__dirname, '..', '..')

/** The `img-src` sources of the Content-Security-Policy the SPA is served with */
function imageSources(file: string, marker: RegExp): string[] {
  const policy = readFileSync(join(REPO, file), 'utf8').split('\n').find(line => marker.test(line)) ?? ''
  const directive = policy.match(/img-src ([^;"`]+)/)?.[1] ?? ''
  return directive.trim().split(/\s+/)
}

describe('the Content-Security-Policy of the deploy files', () => {
  const tileOrigin = new URL(TILE_URL.replace('{z}/{x}/{y}', '0/0/0')).origin
  const satelliteOrigin = new URL(SATELLITE_URL.replace('{z}/{y}/{x}', '0/0/0')).origin

  it('nginx.conf.example lets the browser load the map tiles (otherwise every map is empty)', () => {
    expect(imageSources('deploy/nginx.conf.example', /add_header Content-Security-Policy "default-src 'self'/)).toContain(tileOrigin)
  })

  it('nginx.conf.example also lets the satellite pictures through', () => {
    expect(imageSources('deploy/nginx.conf.example', /add_header Content-Security-Policy "default-src 'self'/)).toContain(satelliteOrigin)
  })

  it('the release checklist starting point lists the satellite host too', () => {
    expect(imageSources('.ai/RELEASE_CHECKLIST.md', /^\s*`default-src 'self'; script-src 'self'/)).toContain(satelliteOrigin)
  })

  it('the release checklist starting point agrees', () => {
    expect(imageSources('.ai/RELEASE_CHECKLIST.md', /^\s*`default-src 'self'; script-src 'self'/)).toContain(tileOrigin)
  })
})
