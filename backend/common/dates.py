"""
The business date (R12).

TIME_ZONE stays UTC (stored datetimes, logs). "Today" for bookings, statistics and
auto-completion is the date in BUSINESS_TIME_ZONE (default Asia/Tashkent, UTC+5),
so between 00:00 and 05:00 in Tashkent it is already the next day. Hotels in other
countries use the same business date for now; a per-country time zone is a later
improvement.
"""
import zoneinfo

from django.conf import settings
from django.utils import timezone


def business_time_zone():
    return zoneinfo.ZoneInfo(settings.BUSINESS_TIME_ZONE)


def business_today():
    return timezone.now().astimezone(business_time_zone()).date()
