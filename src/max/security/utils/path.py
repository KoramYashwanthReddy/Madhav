"""Path normalization and security boundary utilities for permission evaluation."""

import posixpath
from urllib.parse import unquote


def normalize_path(path: str) -> str:
    """Normalize a resource path for secure policy comparison.

    - Resolves URI encoding (%2e%2e, %2f, etc.)
    - Replaces backslashes with forward slashes
    - Collapses duplicate slashes and removes '.' and '..' components safely
    - Strips trailing slash unless root '/'
    """
    if not path:
        return "/"

    # Decode URL encoding up to twice to catch double-encoded traversal attempts (%252e)
    decoded = unquote(unquote(path))

    # Standardize path separators to POSIX
    standardized = decoded.replace("\\", "/")

    # Normalize posix path
    normalized = posixpath.normpath(standardized)

    # Ensure leading slash for consistency if non-empty
    if not normalized.startswith("/"):
        normalized = "/" + normalized

    return normalized


def is_path_under_root(target_path: str, root_path: str) -> bool:
    """Check if normalized target_path resides within or matches root_path scope."""
    norm_target = normalize_path(target_path)
    norm_root = normalize_path(root_path)

    if norm_root == "/":
        return True

    if norm_target == norm_root:
        return True

    prefix = norm_root if norm_root.endswith("/") else norm_root + "/"
    return norm_target.startswith(prefix)
