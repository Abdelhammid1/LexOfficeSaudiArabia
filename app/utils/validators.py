"""Input validation helpers."""
import re

from app.utils.market_config import get_config, DEFAULT_MARKET


def validate_email(email):
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone, market=None):
    """Validate a KSA mobile number.

    Empty input is considered valid (caller decides if the field is required).
    The `market` parameter is kept for signature compatibility but is ignored —
    this deployment is KSA only.
    """
    if not phone:
        return True
    normalized = normalize_phone(phone)
    if not normalized:
        return False
    return bool(re.match(get_config(DEFAULT_MARKET)['phone_regex'], normalized))


def normalize_phone(phone, market=None):
    """Normalize a KSA phone number to canonical local form 05XXXXXXXX.

    Strips +966 / 00966 / 966 prefix and spaces/dashes/parens.
    Returns None if input is empty after stripping. If the input doesn't match
    a recognizable KSA shape, returns the digit-stripped string so uniqueness
    checks still function — pair with validate_phone() for strict checks.
    """
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    if not digits:
        return None

    # Strip 966 / 00966 country prefix
    if digits.startswith('00966'):
        digits = digits[5:]
    elif digits.startswith('966') and len(digits) >= 12:
        digits = digits[3:]
    # Saudi mobile is 9 digits starting with 5; prepend 0 to canonicalize
    if digits.startswith('5') and len(digits) == 9:
        digits = '0' + digits
    return digits


def validate_national_id(nid):
    """Validate Saudi National ID / Iqama (10 digits).

    Saudi nationals carry a National ID starting with 1; non-Saudi residents
    have an Iqama starting with 2. Both are 10 digits total.
    """
    if not nid:
        return True
    return bool(re.match(r'^[12]\d{9}$', nid.strip()))


def validate_password(password):
    """Validate password policy: 8+ chars, uppercase, number, symbol."""
    if len(password) < 8:
        return False, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل'
    if not re.search(r'[A-Z]', password):
        return False, 'كلمة المرور يجب أن تحتوي على حرف كبير'
    if not re.search(r'\d', password):
        return False, 'كلمة المرور يجب أن تحتوي على رقم'
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'كلمة المرور يجب أن تحتوي على رمز خاص'
    return True, ''


def sanitize_string(s):
    """Basic sanitization for text input."""
    if not s:
        return s
    s = s.replace('<script', '&lt;script')
    s = s.replace('</script', '&lt;/script')
    return s.strip()
