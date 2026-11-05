interface ServiceWorkerHost {
  serviceWorker?: { register(url: string, options?: { scope: string }): Promise<unknown> }
}

/** Registers the small offline worker (public/sw.js) in the built site; failing to do so never matters to the visitor */
export async function registerServiceWorker(
  production: boolean = import.meta.env.PROD,
  host: ServiceWorkerHost = navigator,
): Promise<void> {
  if (!production || !host.serviceWorker) return
  try {
    await host.serviceWorker.register('/sw.js', { scope: '/' })
  } catch {
    // The site works the same without it
  }
}
