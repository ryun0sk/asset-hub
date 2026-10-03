import time
import unittest
from unittest.mock import Mock, patch

try:
    import jwt
    from cryptography.hazmat.primitives.asymmetric import ec
    from backend import cloud
except ImportError:  # requirements.txt not installed (CI installs it)
    cloud = None

AUDIENCE = '/projects/123/locations/asia-northeast1/services/asset-hub'
ALLOWED = frozenset({'viewer@example.com'})


@unittest.skipUnless(cloud, 'PyJWT[crypto] is not installed')
class VerifyIAPTest(unittest.TestCase):
    def setUp(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        keys = Mock()
        keys.get_signing_key_from_jwt.return_value = Mock(key=self.key.public_key())
        patcher = patch.object(cloud, '_KEYS', keys)
        patcher.start()
        self.addCleanup(patcher.stop)

    def token(self, key=None, algorithm='ES256', headers=None, **changes):
        now = int(time.time())
        claims = dict(iss='https://cloud.google.com/iap', aud=AUDIENCE, sub='accounts.google.com:1',
                      email='viewer@example.com', iat=now, exp=now + 600)
        claims.update(changes)
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, key or self.key, algorithm=algorithm, headers=headers if headers is not None else {'kid': 'k1'})

    def test_valid_assertion_returns_email(self):
        self.assertEqual(cloud.verify_iap(self.token(), AUDIENCE, ALLOWED), 'viewer@example.com')
        self.assertEqual(cloud.verify_iap(self.token(email='Viewer@Example.com'), AUDIENCE, ALLOWED), 'Viewer@Example.com')

    def test_invalid_assertions_are_denied(self):
        now = int(time.time())
        other = ec.generate_private_key(ec.SECP256R1())
        cases = {
            'empty': '',
            'oversized': 'x' * 20000,
            'garbage': 'not-a-jwt',
            'other key': self.token(key=other),
            'wrong audience': self.token(aud='/projects/1/global/backendServices/2'),
            'wrong issuer': self.token(iss='https://accounts.google.com'),
            'not allowed': self.token(email='intruder@example.com'),
            'missing email': self.token(email=None),
            'missing sub': self.token(sub=None),
            'expired': self.token(iat=now - 1200, exp=now - 600),
            'too long lived': self.token(exp=now + 3600),
            'missing kid': self.token(headers={}),
            'hs256': jwt.encode(dict(iss='https://cloud.google.com/iap', aud=AUDIENCE, sub='s', email='viewer@example.com',
                                     iat=now, exp=now + 600), 'secret' * 6, algorithm='HS256', headers={'kid': 'k1'}),
        }
        for name, assertion in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(PermissionError):
                    cloud.verify_iap(assertion, AUDIENCE, ALLOWED)

    def test_key_lookup_failure_is_denied(self):
        cloud._KEYS.get_signing_key_from_jwt.side_effect = RuntimeError('network')
        with self.assertRaises(PermissionError):
            cloud.verify_iap(self.token(), AUDIENCE, ALLOWED)


class StartupTest(unittest.TestCase):
    def test_cloud_mode_refuses_without_audience_viewers_or_bucket(self):
        from backend.server import cloud_settings
        for env in [{}, {'ASSET_IAP_AUDIENCE': AUDIENCE, 'ASSET_STATE_BUCKET': 'b'},
                    {'ASSET_IAP_AUDIENCE': AUDIENCE, 'ASSET_ALLOWED_EMAILS': 'nobody', 'ASSET_STATE_BUCKET': 'b'},
                    {'ASSET_ALLOWED_EMAILS': 'viewer@example.com', 'ASSET_STATE_BUCKET': 'b'},
                    {'ASSET_IAP_AUDIENCE': AUDIENCE, 'ASSET_ALLOWED_EMAILS': 'viewer@example.com'}]:
            with self.subTest(env=env), self.assertRaises(SystemExit):
                cloud_settings(env)
        self.assertEqual(cloud_settings({'ASSET_IAP_AUDIENCE': AUDIENCE, 'ASSET_ALLOWED_EMAILS': 'Viewer@Example.com,b@example.com',
                                         'ASSET_STATE_BUCKET': 'b'}),
                         (AUDIENCE, frozenset({'viewer@example.com', 'b@example.com'}), 'b'))


if __name__ == '__main__':
    unittest.main()
