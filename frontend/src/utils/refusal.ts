/** Why a booking or a quote was refused, as a code with its values, so the site can say it in the page language */
export interface Refusal {
  code: string
  params: Record<string, string | number>
}

/** The `reason` of an error body, or undefined when the server sent none or a malformed one */
export function refusalOf(body: unknown): Refusal | undefined {
  const reason = typeof body === 'object' && body !== null ? (body as { reason?: unknown }).reason : undefined
  if (typeof reason !== 'object' || reason === null) return undefined
  const { code, params } = reason as { code?: unknown; params?: unknown }
  if (typeof code !== 'string' || typeof params !== 'object' || params === null) return undefined
  return { code, params: params as Record<string, string | number> }
}
