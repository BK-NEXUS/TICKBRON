import { describe, it, expect } from 'vitest'
import { IMAGE_RULES, imageSizeProblem, type ImageRuleKind } from './imageRules'

const KINDS: ImageRuleKind[] = ['hotel', 'room', 'ad', 'place']

describe('IMAGE_RULES', () => {
  it('has the sizes of the backend (backend/common/image_rules.py)', () => {
    expect(IMAGE_RULES.hotel).toMatchObject({ minWidth: 1200, minHeight: 800, recommended: [1600, 1067], recommendedShape: '3:2', shapeLabels: ['4:3', '16:9'] })
    expect(IMAGE_RULES.room).toEqual(IMAGE_RULES.hotel)
    expect(IMAGE_RULES.ad).toMatchObject({ minWidth: 1600, minHeight: 600, recommended: [1920, 720], recommendedShape: '8:3', shapeLabels: ['16:9', '16:5'] })
    expect(IMAGE_RULES.place).toMatchObject({ minWidth: 800, minHeight: 600, recommended: [1200, 900], recommendedShape: '4:3', shapeLabels: ['6:5', '9:5'] })
  })
})

describe('imageSizeProblem', () => {
  it.each(KINDS)('accepts the smallest and the recommended size of %s', kind => {
    const { minWidth, minHeight, recommended } = IMAGE_RULES[kind]
    expect(imageSizeProblem({ width: recommended[0], height: recommended[1] }, kind)).toBeNull()
    const height = Math.max(minHeight, Math.round((recommended[1] * minWidth) / recommended[0]))
    expect(imageSizeProblem({ width: minWidth, height }, kind)).toBeNull()
  })

  it.each(KINDS)('says %s is too small, with both sizes', kind => {
    const { minWidth, minHeight, recommended } = IMAGE_RULES[kind]
    const problem = imageSizeProblem({ width: minWidth - 1, height: recommended[1] }, kind)
    expect(problem?.key).toBe('image.errTooSmall')
    expect(problem?.params).toMatchObject({
      width: minWidth - 1, height: recommended[1], minW: minWidth, minH: minHeight, recW: recommended[0], recH: recommended[1],
    })
  })

  it.each(KINDS)('keeps both edges of the shape of %s and refuses what is outside', kind => {
    const rule = IMAGE_RULES[kind]
    const [[lowN, lowD], [highN, highD]] = rule.shape
    expect(imageSizeProblem({ width: (1800 * lowN) / lowD, height: 1800 }, kind)).toBeNull()
    expect(imageSizeProblem({ width: (1800 * highN) / highD, height: 1800 }, kind)).toBeNull()
    const tooWide = imageSizeProblem({ width: (1800 * highN) / highD + 400, height: 1800 }, kind)
    const tooTall = imageSizeProblem({ width: (1800 * lowN) / lowD - 300, height: 1800 }, kind)
    for (const problem of [tooWide, tooTall]) {
      expect(problem?.key).toBe('image.errShape')
      expect(problem?.params).toMatchObject({ low: rule.shapeLabels[0], high: rule.shapeLabels[1] })
    }
  })

  it('refuses a portrait hotel photo', () => {
    expect(imageSizeProblem({ width: 1200, height: 1800 }, 'hotel')?.key).toBe('image.errShape')
  })
})
