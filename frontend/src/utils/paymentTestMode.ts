/**
 * The card form is for the test payment mode only (backend PAYMENT_TEST_MODE, which needs DEBUG). It is
 * off unless VITE_PAYMENT_TEST_MODE is "true", and never in a production build: real payments go through
 * the provider's own page (Payme, Click, Visa), so card numbers are never typed into our site.
 */
export const isCardTestMode = (): boolean =>
  import.meta.env.VITE_PAYMENT_TEST_MODE === 'true' && !import.meta.env.PROD
