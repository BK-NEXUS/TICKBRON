from django.conf import settings

from promotions.views import PromotionPublicThrottle


def test_public_banner_limit_is_a_setting_with_the_documented_default():
    assert settings.PROMOTION_PUBLIC_THROTTLE_RATE == '60/min'
    assert PromotionPublicThrottle.rate == settings.PROMOTION_PUBLIC_THROTTLE_RATE
