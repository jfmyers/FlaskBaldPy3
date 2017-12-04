import hashlib
import base64
import uuid


def hash_password(seed=None, length=None, strip_equals=True):
    value = base64.urlsafe_b64encode(hashlib.sha1(seed).digest())
    if strip_equals:
        value = value.rstrip('=')
    if length is not None and length > 0:
        return value[:length]
    return value


def generate_hashed_password(length=None):
    key = base64.urlsafe_b64encode(uuid.uuid4().get_bytes()).rstrip("=")
    if length:
        return key[:length]
    return key
