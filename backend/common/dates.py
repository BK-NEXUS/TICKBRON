"""
Is sanası (R12).

TIME_ZONE UTC bolıp qaladı (saqlanǵan datetime lar, log lar). Bronlar, statistika hám
avtomat juwmaqlaw ushın "búgin" BUSINESS_TIME_ZONE degi sana (ádetde Asia/Tashkent, UTC+5),
sol sebepli Tashkent te 00:00 menen 05:00 aralıǵında ol ózi keyingi kún. Basqa
mámleketlerdegi mehmanxanalar házirshe sol is sanasın paydalanadı; mámleket boyınsha waqıt zonası keyingi
jaqsılaw.
"""
import zoneinfo

from django.conf import settings
from django.utils import timezone


def business_time_zone():
    return zoneinfo.ZoneInfo(settings.BUSINESS_TIME_ZONE)


def business_today():
    return timezone.now().astimezone(business_time_zone()).date()
