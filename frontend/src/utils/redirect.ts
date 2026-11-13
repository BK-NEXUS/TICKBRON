/** Kirgennen yamasa dizimnen ótkennen keyin qaytatuǵın bet: `location.state.from.pathname`, bolmasa bas bet. */
export function redirectPathFrom(state: unknown): string {
  if (typeof state !== 'object' || state === null) return '/'
  const from = (state as { from?: unknown }).from
  if (typeof from !== 'object' || from === null) return '/'
  const pathname = (from as { pathname?: unknown }).pathname
  return typeof pathname === 'string' && pathname ? pathname : '/'
}
