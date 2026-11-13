"""Kiriw hám dizimnen ótiw shekleri hújjetlestirilgen ádettegi mánisli sazlamalar, sol sebepli bánt ortaq mánzildi kodsız
sazlawǵa boladı."""
from django.conf import settings

from users.throttles import LoginRateThrottle, RegisterRateThrottle


def test_login_limit_is_a_setting_with_the_documented_default():
    assert settings.LOGIN_THROTTLE_RATE == '10/min'
    assert LoginRateThrottle.rate == settings.LOGIN_THROTTLE_RATE


def test_register_limit_is_a_setting_with_the_documented_default():
    assert settings.REGISTER_THROTTLE_RATE == '5/min'
    assert RegisterRateThrottle.rate == settings.REGISTER_THROTTLE_RATE
