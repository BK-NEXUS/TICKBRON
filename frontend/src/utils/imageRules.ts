// Hár súwret júklewdiń ólshem qaǵıydaları. Backend penen birdey sanlar (`backend/common/image_rules.py`), ol
// tiykarǵı hújjet hám qayta tekseredi; bular tek ólshemlerdi adamǵa kórsetedi hám qáte súwretti jiberilmesten aldın biykar
// etedi.

export type ImageRuleKind = 'hotel' | 'room' | 'ad' | 'place'

export interface ImageRule {
  minWidth: number
  minHeight: number
  /** [eń tar, eń keń] eni : boyı, hárbiri qatnastıń [eni, boyı] bólekleri retinde */
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
  // Reklama karuseli telefonda 16:9 hám keń ekranda 16:5
  ad: { minWidth: 1600, minHeight: 600, shape: [[16, 9], [16, 5]], shapeLabels: ['16:9', '16:5'], recommended: [1920, 720], recommendedShape: '8:3' },
  // Bas bettiń "qayaqqa" kartaları 4:3
  place: { minWidth: 800, minHeight: 600, shape: [[6, 5], [9, 5]], shapeLabels: ['6:5', '9:5'], recommended: [1200, 900], recommendedShape: '4:3' },
}

export interface ImageSize { width: number; height: number }

type SizeMessageKey = 'image.errTooSmall' | 'image.errShape'
export interface SizeProblem {
  key: SizeMessageKey
  params: Record<string, string | number>
}

/** Usı túrdegi orın ushın usı ólshemdegi súwrette ne qáte, yamasa sıyssa null (anıq shegara sıyadı). */
export function imageSizeProblem({ width, height }: ImageSize, kind: ImageRuleKind): SizeProblem | null {
  const rule = IMAGE_RULES[kind]
  const params = {
    width, height, minW: rule.minWidth, minH: rule.minHeight, recW: rule.recommended[0], recH: rule.recommended[1],
    recShape: rule.recommendedShape, low: rule.shapeLabels[0], high: rule.shapeLabels[1],
  }
  if (width < rule.minWidth || height < rule.minHeight) return { key: 'image.errTooSmall', params }
  const [[lowW, lowH], [highW, highH]] = rule.shape
  // Kóbeytip salıstırıladı, sol sebepli shegaralar anıq pútin san salıstırıwları
  if (width * lowH < height * lowW || width * highH > height * highW) return { key: 'image.errShape', params }
  return null
}
