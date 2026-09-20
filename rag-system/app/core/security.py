import re
import html


def sanitize_input(text: str) -> str:
    """
    Sanitize user query inputs to prevent injection attacks and clear hidden control characters.
    """
    if not text:
        return ""
    # Strip dangerous HTML tags
    cleaned = html.escape(text.strip())
    # Remove null bytes or non-printable ASCII/Unicode control chars
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    return cleaned


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive secrets/API keys for logging.
    """
    if not secret:
        return "NOT_SET"
    if len(secret) <= visible_chars * 2:
        return "*" * len(secret)
    return f"{secret[:visible_chars]}...{secret[-visible_chars:]}"
