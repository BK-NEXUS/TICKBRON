export function sceneSettings(isMobile: boolean): { shapeCount: number; dpr: number } {
  return isMobile ? { shapeCount: 6, dpr: 1 } : { shapeCount: 14, dpr: 1.5 }
}
