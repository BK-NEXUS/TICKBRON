// Tayl deregi ushın bir orın: host CSP `img-src` ta da dizimlengen bolıwı kerek (.ai/RELEASE_CHECKLIST.md).
export const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

// OpenStreetMap tayl licenziyası hár kartada usı ataw jazıwın talap etedi
export const TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'

/** Ózbekstan, hesh nárse qayaqqa qarawdı aytpaǵanda kórsetiledi */
export const DEFAULT_CENTER: [number, number] = [41.3, 64.6]
export const DEFAULT_ZOOM = 5

// Sputnik súwretleri. Ádetde Esri World Imagery (kartada onıń atawı kerek). Onıń shártleri
// jeńil paydalanıw ushın: saytta haqıyqıy trafik payda bolmastan aldın kilti bar provayderdi tańlań hám eki ózgeriwshini de
// belgileń;
// onıń hosti CSP `img-src` ta da bolıwı kerek (.ai/RELEASE_CHECKLIST.md).
export const SATELLITE_URL: string =
  import.meta.env.VITE_SATELLITE_TILE_URL || 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

export const SATELLITE_ATTRIBUTION: string =
  import.meta.env.VITE_SATELLITE_ATTRIBUTION || 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community'
