import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

/** Forget state shared between flows in a previous run (booking code, property ids). */
export default function globalSetup() {
  const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), 'screenshots')
  fs.rmSync(path.join(dir, 'shared.json'), { force: true })
}
