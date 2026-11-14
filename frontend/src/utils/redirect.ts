// Only a path on this site: a leading "//" or a backslash is read by the browser as another host (open redirect).
// Tek usı saytdaǵı jol: "//" yamasa backslash brauzer tárepinen basqa host dep túsiniledi (open redirect).
const SITE_PATH = /^\/(?![/\\])[^\\]*$/

function hasControlCharacter(text: string): boolean {
  return Array.from(text).some(character => character.charCodeAt(0) < 0x20)
}

/** Page to return to after login or register: `location.state.from.pathname`, else the home page. */
export function redirectPathFrom(state: unknown): string {
  if (typeof state !== 'object' || state === null) return '/'
  const from = (state as { from?: unknown }).from
  if (typeof from !== 'object' || from === null) return '/'
  const pathname = (from as { pathname?: unknown }).pathname
  return typeof pathname === 'string' && SITE_PATH.test(pathname) && !hasControlCharacter(pathname) ? pathname : '/'
}
