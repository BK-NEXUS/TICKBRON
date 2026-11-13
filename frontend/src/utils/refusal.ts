/** Bron yamasa quote nege biykar etildi, kod hám mánisler retinde, sonda sayt bet tilinde ayta aladı */
export interface Refusal {
  code: string
  params: Record<string, string | number>
}

/** Qátelik denesiniń `reason` ı, yamasa server joq yamasa buzılǵan jiberse undefined */
export function refusalOf(body: unknown): Refusal | undefined {
  const reason = typeof body === 'object' && body !== null ? (body as { reason?: unknown }).reason : undefined
  if (typeof reason !== 'object' || reason === null) return undefined
  const { code, params } = reason as { code?: unknown; params?: unknown }
  if (typeof code !== 'string' || typeof params !== 'object' || params === null) return undefined
  return { code, params: params as Record<string, string | number> }
}
