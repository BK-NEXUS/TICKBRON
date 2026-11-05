// The size rules of every picture upload. Same numbers as the backend (`backend/common/image_rules.py`), which is the
// authority and checks again; these only show the sizes to the person and refuse a wrong picture before it is sent.

export type ImageRuleKind = 'hotel' | 'room' | 'ad' | 'place'

export interface ImageRule {
  minWidth: number
  minHeight: number
  /** [narrowest, widest] width : height, each as [width, height] parts of the ratio */
  shape: [[number, number], [number, number]]
  shapeLabels: [string, string]
  recommended: [number, number]
  recommendedShape: string
}

const PHOTO: ImageRule = {
  minWidth: 1200, minHeight: 800, shape: [[4, 3], [16, 9]], shapeLabels: ['4:3', '16:9'], recommended: [1600, 1067], recommendedShape: '3:2',
}

export const IMAGE_RULES: Record<ImageRuleKind, ImageRule> = {
  hotel: PHOTO,
  room: PHOTO,
  // The ad carousel is 16:9 on a phone and 16:5 on a wide screen
  ad: { minWidth: 1600, minHeight: 600, shape: [[16, 9], [16, 5]], shapeLabels: ['16:9', '16:5'], recommended: [1920, 720], recommendedShape: '8:3' },
  // The "where to" cards of the home page are 4:3
  place: { minWidth: 800, minHeight: 600, shape: [[6, 5], [9, 5]], shapeLabels: ['6:5', '9:5'], recommended: [1200, 900], recommendedShape: '4:3' },
}

export interface ImageSize { width: number; height: number }

type SizeMessageKey = 'image.errTooSmall' | 'image.errShape'
export interface SizeProblem {
  key: SizeMessageKey
  params: Record<string, string | number>
}

/** What is wrong with a picture of this size for this kind of place, or null when it fits (an exact edge fits). */
export function imageSizeProblem({ width, height }: ImageSize, kind: ImageRuleKind): SizeProblem | null {
  const rule = IMAGE_RULES[kind]
  const params = {
    width, height, minW: rule.minWidth, minH: rule.minHeight, recW: rule.recommended[0], recH: rule.recommended[1],
    recShape: rule.recommendedShape, low: rule.shapeLabels[0], high: rule.shapeLabels[1],
  }
  if (width < rule.minWidth || height < rule.minHeight) return { key: 'image.errTooSmall', params }
  const [[lowW, lowH], [highW, highH]] = rule.shape
  // Cross-multiplied, so the edges are exact whole-number comparisons
  if (width * lowH < height * lowW || width * highH > height * highW) return { key: 'image.errShape', params }
  return null
}
