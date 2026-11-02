export function sceneSettings(isMobile: boolean): { segments: number; dpr: number } {
  return isMobile ? { segments: 48, dpr: 1 } : { segments: 128, dpr: 1.5 }
}
