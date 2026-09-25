"""
Helpers for keeping personal data out of logs.
"""


def mask_phone(phone_number):
    """
    Mask a phone number for logging: keep the first 4 and last 2 characters.

    '+998901234567' -> '+998*******67'. Values too short to mask meaningfully
    (or empty) become '***'.
    """
    phone = str(phone_number or '')
    if len(phone) <= 6:
        return '***'
    return f"{phone[:4]}{'*' * (len(phone) - 6)}{phone[-2:]}"
