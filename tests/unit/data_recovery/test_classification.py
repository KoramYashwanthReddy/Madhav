"""Unit tests for Data Classification Engine."""

from max.data_recovery.classification import ClassificationLevel, DataClassifier


def test_classify_domain_critical() -> None:
    tag = DataClassifier.classify_domain("identity")
    assert tag.level == ClassificationLevel.CRITICAL
    assert tag.encrypted_at_rest is True
    assert tag.contains_pii is True


def test_classify_domain_confidential() -> None:
    tag = DataClassifier.classify_domain("memory")
    assert tag.level == ClassificationLevel.CONFIDENTIAL
    assert tag.encrypted_at_rest is True


def test_classify_domain_sensitive() -> None:
    tag = DataClassifier.classify_domain("knowledge")
    assert tag.level == ClassificationLevel.SENSITIVE


def test_classify_payload_sensitive() -> None:
    payload = {"username": "user1", "api_key": "secret123"}
    tag = DataClassifier.classify_payload(payload)
    assert tag.level == ClassificationLevel.CRITICAL
    assert tag.encrypted_at_rest is True
