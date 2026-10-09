import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
import { PropertyPolicy } from '../adapters/propertyAdapter'

interface PropertyPoliciesDetailProps {
  policies?: PropertyPolicy[]
}

/**
 * PropertyPoliciesDetail component for displaying detailed property policies
 * Shows check-in, cancellation, and other property policies with strictness indicators
 */
export function PropertyPoliciesDetail({ policies = [] }: PropertyPoliciesDetailProps) {
  const { t } = useI18n()
  if (policies.length === 0) {
    return (
      <div className="property-policies-detail property-policies-detail--empty">
        <p className="property-policies-detail-empty">{t('policies.empty')}</p>
      </div>
    )
  }

  // Group policies by type for better organization
  const groupedPolicies = policies.reduce((acc, policy) => {
    if (!acc[policy.policy_type]) {
      acc[policy.policy_type] = []
    }
    acc[policy.policy_type].push(policy)
    return acc
  }, {} as Record<string, PropertyPolicy[]>)

  return (
    <div className="property-policies-detail">
      <h2 className="property-policies-detail-title">{t('policies.title')}</h2>
      
      {Object.entries(groupedPolicies).map(([policyType, typePolicies]) => (
        <div key={policyType} className="property-policies-group">
          <h3 className="property-policies-group-title">
            {formatPolicyType(policyType, t)}
          </h3>
          
          {typePolicies.map((policy, index) => (
            <div 
              key={index}
              className={`property-policy-item ${
                policy.is_strict ? 'property-policy-item--strict' : ''
              }`}
            >
              <div className="property-policy-item-header">
                <h4 className="property-policy-item-title">{policy.title}</h4>
                {policy.is_strict && (
                  <span className="property-policy-item-badge" aria-label={t('policies.strictLabel')}>
                    {t('policies.strict')}
                  </span>
                )}
              </div>
              
              <p className="property-policy-item-description">
                {policy.description}
              </p>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function formatPolicyType(policyType: string, t: (key: MessageKey) => string): string {
  switch (policyType) {
    case 'check_in':
      return t('policies.check_in')
    case 'cancellation':
      return t('policies.cancellation')
    case 'house_rules':
      return t('policies.house_rules')
    case 'payment':
      return t('policies.payment')
    case 'security':
      return t('policies.security')
    default:
      return policyType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
  }
}