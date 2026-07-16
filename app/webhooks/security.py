import hmac
import hashlib

from app.config import settings


def verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if signature_header is None:
        return False

    expected = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)