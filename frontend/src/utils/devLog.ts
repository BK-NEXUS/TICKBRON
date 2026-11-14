// Error text from the API or the browser can hold personal data; the production build keeps the console clean.
// Klientte qátelik teksti jeke maǵlıwmatlardı óz ishine alıwı múmkin; production build console-dı taza ustaydı.

/** console.error while developing, silent in the production build. */
export function logDevError(...details: unknown[]): void {
  if (import.meta.env.DEV) console.error(...details)
}
