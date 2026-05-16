"""
Generate VAPID keys for browser Web Push.

Run:
    python generate_vapid_keys.py

Copy the printed values into Railway environment variables:
    VAPID_PUBLIC_KEY
    VAPID_PRIVATE_KEY
    VAPID_CLAIM_EMAIL
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64url(data):
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


private_key = ec.generate_private_key(ec.SECP256R1())
public_numbers = private_key.public_key().public_numbers()

private_der = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

public_key = b'\x04' + public_numbers.x.to_bytes(32, 'big') + public_numbers.y.to_bytes(32, 'big')

print('VAPID_PUBLIC_KEY=' + b64url(public_key))
print('VAPID_PRIVATE_KEY=' + b64url(private_der))
print('VAPID_CLAIM_EMAIL=mailto:your-email@example.com')
