import { useI18n } from '../i18n/I18nContext'
import { IMAGE_RULES, type ImageRuleKind } from '../utils/imageRules'

/** Hár júklew qutısı astında: paydalanatuǵın ólshem, eń kishi ólshem, forma hám fayl túrleri, piksellerde jazılǵan. */
export function ImageRequirements({ kind }: { kind: ImageRuleKind }) {
  const { t } = useI18n()
  const rule = IMAGE_RULES[kind]
  return (
    <span className="field-hint image-requirements" data-testid="image-requirements">
      {t('image.hint', {
        recW: rule.recommended[0], recH: rule.recommended[1], recShape: rule.recommendedShape,
        minW: rule.minWidth, minH: rule.minHeight, low: rule.shapeLabels[0], high: rule.shapeLabels[1],
      })}
    </span>
  )
}
