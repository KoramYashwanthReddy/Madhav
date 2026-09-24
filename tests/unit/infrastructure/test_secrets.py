"""Unit tests for Secret Management Architecture and Redaction Provider."""

from max.infrastructure.secrets import SecretManager, get_secret_manager


def test_secret_rotation_status() -> None:
    secret_mgr = SecretManager()
    rotation_list = secret_mgr.get_rotation_status()

    assert len(rotation_list) > 0
    item = rotation_list[0]
    assert item.secret_key_name == "SECURITY__SECRET_KEY"
    assert item.rotation_required is False


def test_secret_redaction_utility() -> None:
    assert SecretManager.redact_string("supersecret") == "sup...***REDACTED***"
    assert SecretManager.redact_string("12345") == "***REDACTED***"
    assert SecretManager.redact_string("") == ""


def test_get_secret_manager_singleton() -> None:
    sec1 = get_secret_manager()
    sec2 = get_secret_manager()
    assert sec1 is sec2
