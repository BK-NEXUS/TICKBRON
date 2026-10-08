import { describe, it, expect } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, resolve, sep } from 'node:path'

// UI icons are lucide-react or SVG, never emoji: emoji render differently on every platform.
const ROOT = resolve(__dirname, '../..')
const EMOJI = /\p{Extended_Pictographic}|\p{Regional_Indicator}/u
// Copyright, registered and trademark signs are text, not decoration
const ALLOWED_SIGNS = /[©®™]/g

// TODO: remove once the SVG country selector replaces the flag emoji
const ALLOWED_FILES = new Set([
  'src/utils/phone.ts',
  // TODO: the i18n session owns these two; remove when its language and currency selectors are done
  'src/components/LanguageSelector.tsx',
  'src/components/LanguageSelector.test.tsx',
  'src/components/CurrencySelector.tsx',
  'src/components/CurrencySelector.test.tsx',
])

const SCANNED_EXTENSIONS = /\.(tsx?|css|html|json|svg)$/

function filesUnder(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) return name === 'node_modules' ? [] : filesUnder(path)
    return SCANNED_EXTENSIONS.test(name) ? [path] : []
  })
}

describe('no emoji in the UI', () => {
  it('finds none in src/ or index.html', () => {
    const self = relative(ROOT, __filename).split(sep).join('/')
    const files = [...filesUnder(join(ROOT, 'src')), join(ROOT, 'index.html')]
    const hits: string[] = []

    for (const file of files) {
      const name = relative(ROOT, file).split(sep).join('/')
      if (name === self || ALLOWED_FILES.has(name)) continue
      readFileSync(file, 'utf-8').split(/\r?\n/).forEach((line, index) => {
        if (EMOJI.test(line.replace(ALLOWED_SIGNS, ''))) hits.push(`${name}:${index + 1}: ${line.trim().slice(0, 80)}`)
      })
    }

    expect(hits, `Emoji found, use a lucide-react icon instead:\n${hits.join('\n')}`).toEqual([])
  })
})
