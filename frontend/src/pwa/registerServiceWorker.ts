interface ServiceWorkerHost {
  serviceWorker?: { register(url: string, options?: { scope: string }): Promise<unknown> }
}

/**
 * Kishi offline worker di (public/sw.js) qurılǵan saytta dizimnen ótkizedi; bunıń sátsiz bolıwı kelwshige hesh qashan
 * áhmiyetli emes
 */
export async function registerServiceWorker(
  production: boolean = import.meta.env.PROD,
  host: ServiceWorkerHost = navigator,
): Promise<void> {
  if (!production || !host.serviceWorker) return
  try {
    await host.serviceWorker.register('/sw.js', { scope: '/' })
  } catch {
    // Sayt onsız da birdey isleydi
  }
}
