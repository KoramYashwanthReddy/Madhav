"""Domain and URL normalization utilities for permission evaluation."""

from urllib.parse import unquote, urlparse


def normalize_domain_or_url(url_or_domain: str) -> dict[str, str]:
    """Normalize a domain or URL resource string into components for policy matching.

    Returns dict with keys: scheme, hostname, port, path
    """
    if not url_or_domain:
        return {"scheme": "", "hostname": "", "port": "", "path": "/"}

    raw = unquote(url_or_domain).strip()

    # Prepend scheme if missing to allow urlparse to process hostname
    if "://" not in raw:
        parsed = urlparse(f"https://{raw}")
        # If input didn't specify scheme, default to empty scheme
        scheme = ""
    else:
        parsed = urlparse(raw)
        scheme = parsed.scheme.lower()

    hostname = (parsed.hostname or "").lower()
    port = str(parsed.port) if parsed.port else ""
    path = parsed.path or "/"

    return {
        "scheme": scheme,
        "hostname": hostname,
        "port": port,
        "path": path,
    }


def is_domain_allowed(target: str, allowed_pattern: str) -> bool:
    """Check if target domain/URL matches an allowed domain pattern.

    Supports exact match, wildcard subdomains (*.example.com), and root domains.
    """
    target_norm = normalize_domain_or_url(target)
    pattern_norm = normalize_domain_or_url(allowed_pattern)

    target_host = target_norm["hostname"]
    pattern_host = pattern_norm["hostname"]

    if not target_host or not pattern_host:
        return False

    if target_host == pattern_host or target_host.endswith("." + pattern_host):
        return True

    if pattern_host.startswith("*."):
        root_domain = pattern_host[2:]
        return target_host.endswith("." + root_domain) or target_host == root_domain

    return False
