"""Unit tests for path and domain normalization security utilities."""

from max.security.utils.domain_url import is_domain_allowed, normalize_domain_or_url
from max.security.utils.path import is_path_under_root, normalize_path


def test_path_normalization() -> None:
    assert normalize_path("/project/src/main.py") == "/project/src/main.py"
    assert normalize_path("project/src/main.py") == "/project/src/main.py"
    assert normalize_path("/project/src/../src/main.py") == "/project/src/main.py"
    assert normalize_path("/project/./src/main.py") == "/project/src/main.py"
    assert normalize_path("C:\\project\\src\\main.py") == "/C:/project/src/main.py"
    assert normalize_path("/project/src/..%2f..%2fsystem") == "/system"


def test_is_path_under_root() -> None:
    assert is_path_under_root("/project/src/main.py", "/project") is True
    assert is_path_under_root("/project/src/main.py", "/project/src") is True
    assert is_path_under_root("/system/etc/passwd", "/project") is False
    assert is_path_under_root("/project/../system/etc", "/project") is False


def test_domain_normalization_and_matching() -> None:
    norm = normalize_domain_or_url("https://api.example.com:8080/v1/test")
    assert norm["scheme"] == "https"
    assert norm["hostname"] == "api.example.com"
    assert norm["port"] == "8080"

    assert is_domain_allowed("api.example.com", "example.com") is True
    assert is_domain_allowed("sub.api.example.com", "*.example.com") is True
    assert is_domain_allowed("malicious.com", "example.com") is False
