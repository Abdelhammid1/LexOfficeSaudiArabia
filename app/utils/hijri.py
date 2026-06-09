"""Hijri / Gregorian conversion (Kuwaiti tabular algorithm).

Pure Python; no third-party dependency. Result can differ from Umm al-Qura by
±1 day, which is acceptable for display purposes (greetings, list rows, etc).
For legal/contract dates the user enters and stores Gregorian directly.
"""
from datetime import date
import math


HIJRI_MONTHS_AR = [
    'محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر', 'جمادى الأولى', 'جمادى الآخرة',
    'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة',
]


def gregorian_to_hijri(d):
    """Convert a date / datetime to a (year, month, day) Hijri tuple."""
    if d is None:
        return None
    g_year, g_month, g_day = d.year, d.month, d.day
    if g_month < 3:
        y = g_year - 1
        m = g_month + 12
    else:
        y = g_year
        m = g_month
    a = math.floor(y / 100.0)
    b = 2 - a + math.floor(a / 4.0)
    jd = (math.floor(365.25 * (y + 4716))
          + math.floor(30.6001 * (m + 1))
          + g_day + b - 1524)
    l = jd - 1948440 + 10632
    n = math.floor((l - 1) / 10631.0)
    l = l - 10631 * n + 354
    j = ((math.floor((10985 - l) / 5316.0))
         * (math.floor((50 * l) / 17719.0))
         + (math.floor(l / 5670.0))
         * (math.floor((43 * l) / 15238.0)))
    l = (l - (math.floor((30 - j) / 15.0)) * (math.floor((17719 * j) / 50.0))
         - (math.floor(j / 16.0)) * (math.floor((15238 * j) / 43.0)) + 29)
    h_month = math.floor((24 * l) / 709.0)
    h_day = l - math.floor((709 * h_month) / 24.0)
    h_year = 30 * n + j - 30
    return int(h_year), int(h_month), int(h_day)


def hijri_str(d, with_suffix=True):
    """Format a date as 'DD/MM/YYYY هـ'. Returns '' if d is falsy."""
    parts = gregorian_to_hijri(d)
    if not parts:
        return ''
    y, m, day = parts
    s = f'{day:02d}/{m:02d}/{y}'
    return f'{s} هـ' if with_suffix else s


def hijri_long(d):
    """Format a date as 'DD <month_ar> YYYY هـ' (long form, for headers)."""
    parts = gregorian_to_hijri(d)
    if not parts:
        return ''
    y, m, day = parts
    name = HIJRI_MONTHS_AR[m - 1] if 1 <= m <= 12 else ''
    return f'{day} {name} {y} هـ'
