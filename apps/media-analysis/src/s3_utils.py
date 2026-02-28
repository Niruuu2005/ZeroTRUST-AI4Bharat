"""
Parse S3 URLs to bucket and key for AWS SDK calls.
"""
import re
from urllib.parse import unquote, urlparse


def parse_s3_url(url: str) -> tuple[str, str] | None:
    """
    Return (bucket, key) for s3:// or https:// *.s3.*.amazonaws.com/ URLs.
    """
    if not url or not url.strip():
        return None
    url = url.strip()
    if url.startswith("s3://"):
        # s3://bucket/key
        parts = url[5:].split("/", 1)
        if len(parts) == 2:
            return parts[0], unquote(parts[1])
        if len(parts) == 1 and parts[0]:
            return parts[0], ""
        return None
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https") and "s3" in (parsed.netloc or ""):
        # https://bucket.s3.region.amazonaws.com/key or https://s3.region.amazonaws.com/bucket/key
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").strip("/")
        if ".s3." in host and ".amazonaws.com" in host:
            bucket = host.split(".s3.")[0]
            key = unquote(path) if path else ""
            return bucket, key
        if host.startswith("s3.") and "amazonaws.com" in host and path:
            parts = path.split("/", 1)
            bucket = unquote(parts[0])
            key = unquote(parts[1]) if len(parts) > 1 else ""
            return bucket, key
    return None


def is_s3_url(url: str) -> bool:
    return parse_s3_url(url) is not None
