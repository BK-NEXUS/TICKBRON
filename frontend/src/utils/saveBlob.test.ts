import { describe, it, expect, vi, afterEach } from 'vitest'
import { saveBlob } from './saveBlob'

describe('saveBlob', () => {
  afterEach(() => vi.restoreAllMocks())

  it('downloads the blob under the file name and frees the object URL', () => {
    const create = vi.fn(() => 'blob:abc')
    const revoke = vi.fn()
    vi.stubGlobal('URL', { createObjectURL: create, revokeObjectURL: revoke })
    let downloaded = ''
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      downloaded = this.download
    })
    const blob = new Blob(['a,b'], { type: 'text/csv' })

    saveBlob(blob, 'status_hotels.csv')

    expect(create).toHaveBeenCalledWith(blob)
    expect(click).toHaveBeenCalledTimes(1)
    expect(downloaded).toBe('status_hotels.csv')
    expect(revoke).toHaveBeenCalledWith('blob:abc')
    expect(document.querySelector('a[download]')).toBeNull()
    vi.unstubAllGlobals()
  })
})
