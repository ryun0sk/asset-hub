"""Signed IAP identity. Deny on any verification error."""
import math
import threading

import jwt

IAP_ISSUER = 'https://cloud.google.com/iap'
_KEYS = jwt.PyJWKClient('https://www.gstatic.com/iap/verify/public_key-jwk', cache_keys=True, lifespan=300)
_LOCK = threading.Lock()


def verify_iap(assertion, audience, allowed_emails):
    if not assertion or len(assertion) > 16384:
        raise PermissionError('Authentication required')
    try:
        header = jwt.get_unverified_header(assertion)
        if header.get('alg') != 'ES256' or not isinstance(header.get('kid'), str):
            raise ValueError('Invalid header')
        with _LOCK:
            key = _KEYS.get_signing_key_from_jwt(assertion).key
        claims = jwt.decode(assertion, key, algorithms=['ES256'], audience=audience,
                            issuer=IAP_ISSUER, leeway=30,
                            options={'require': ['exp', 'iat', 'aud', 'iss', 'sub', 'email'], 'strict_aud': True})
        issued, expires = claims['iat'], claims['exp']
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (issued, expires)) \
                or not 0 < expires - issued <= 660:
            raise ValueError('Invalid lifetime')
        email = claims['email']
        if not isinstance(email, str) or email.casefold() not in allowed_emails:
            raise ValueError('Not allowed')
        return email
    except Exception:
        raise PermissionError('Authentication required') from None
