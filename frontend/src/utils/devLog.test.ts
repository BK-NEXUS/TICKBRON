import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { logDevError } from './devLog'

describe('logDevError', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('writes to the console while developing', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logDevError('failed', new Error('x'))
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('says nothing in the production build (error text can carry personal data)', () => {
    vi.stubEnv('DEV', false)
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logDevError('failed', new Error('x'))
    expect(spy).not.toHaveBeenCalled()
  })

  it('is the only place of the site source that calls console.error', () => {
    const files = (folder: string): string[] => readdirSync(folder).flatMap(name => {
      const path = join(folder, name)
      if (statSync(path).isDirectory()) return files(path)
      return /\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name) && name !== 'devLog.ts' ? [path] : []
    })
    const offenders = files(join(__dirname, '..')).filter(path => /console\.error\(/.test(readFileSync(path, 'utf8')))
    expect(offenders).toEqual([])
  })
})
