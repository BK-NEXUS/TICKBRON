import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const policy = readFileSync(join(__dirname, '..', 'index.html'), 'utf8').match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)?.[1] ?? ''
const directive = (name: string) => policy.match(new RegExp(`(?:^|; )${name} ([^;]+)`))?.[1].split(/\s+/) ?? []

describe('the policy inside index.html is as strict as the one the servers send', () => {
  it('runs no inline script and no eval', () => {
    expect(directive('script-src')).toEqual(["'self'"])
  })

  it('never allows plain http: and keeps every request on this site', () => {
    expect(policy).not.toMatch(/\bhttp:/)
    expect(directive('connect-src')).toEqual(["'self'"])
    expect(directive('img-src')).not.toContain('https:')
  })

  it('forbids plugins and a changed base address', () => {
    expect(directive('object-src')).toEqual(["'none'"])
    expect(directive('base-uri')).toEqual(["'self'"])
  })
})
