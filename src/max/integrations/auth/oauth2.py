"""Provider-neutral OAuth2 authorization and state validation handler for Module 29."""

import logging
import secrets
import threading
from datetime import UTC, datetime, timedelta

from max.integrations.domain.enums import AuthenticationType
from max.integrations.domain.exceptions import AuthenticationFailedError, OAuthStateValidationError
from max.integrations.domain.models import CredentialReference
from max.integrations.secrets.secret_store import SecretStore

logger = logging.getLogger(__name__)


class OAuth2StateRecord:
    """Internal OAuth2 state tracking record."""

    def __init__(self, state_token: str, provider_key: str, redirect_uri: str, expires_in_seconds: int = 600) -> None:
        self.state_token = state_token
        self.provider_key = provider_key
        self.redirect_uri = redirect_uri
        self.created_at = datetime.now(UTC)
        self.expires_at = self.created_at + timedelta(seconds=expires_in_seconds)


class OAuth2Handler:
    """OAuth2 authorization code flow & state validator abstraction."""

    def __init__(self) -> None:
        self._states: dict[str, OAuth2StateRecord] = {}
        self._lock = threading.RLock()

    def generate_authorization_url(
        self,
        provider_key: str,
        auth_endpoint: str,
        client_id: str,
        redirect_uri: str,
        scopes: list[str] | None = None,
    ) -> tuple[str, str]:
        """Generate authorization URL with secure state token."""
        state_token = secrets.token_urlsafe(32)
        record = OAuth2StateRecord(
            state_token=state_token,
            provider_key=provider_key,
            redirect_uri=redirect_uri,
        )
        with self._lock:
            self._states[state_token] = record

        scope_str = "%20".join(scopes or ["read", "write"])
        auth_url = (
            f"{auth_endpoint}?"
            f"response_type=code&"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope_str}&"
            f"state={state_token}"
        )
        logger.info("Generated OAuth2 authorization URL for provider '%s' (state token redacted)", provider_key)
        return auth_url, state_token

    def validate_state(self, state_token: str) -> OAuth2StateRecord:
        """Validate state token for CSRF protection and single-use consumption."""
        with self._lock:
            record = self._states.pop(state_token, None)
            if not record:
                raise OAuthStateValidationError("Invalid or unknown OAuth2 state token.")
            if datetime.now(UTC) > record.expires_at:
                raise OAuthStateValidationError("OAuth2 state token has expired.")
            return record

    def exchange_code_mock(
        self,
        code: str,
        state_token: str,
        secret_store: SecretStore,
        owner_id: str = "default_user",
    ) -> CredentialReference:
        """Exchange auth code for tokens and persist securely in SecretStore."""
        state_record = self.validate_state(state_token)

        if not code:
            raise AuthenticationFailedError(state_record.provider_key, "Authorization code is empty.")

        sec_id = f"cred_oauth_{secrets.token_hex(6)}"
        token_payload = {
            "access_token": f"mock_access_token_{secrets.token_hex(16)}",
            "refresh_token": f"mock_refresh_token_{secrets.token_hex(16)}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "obtained_at": datetime.now(UTC).isoformat(),
        }

        secret_store.store(sec_id, token_payload)

        logger.info(
            "Successfully exchanged OAuth2 code for provider '%s' (tokens stored securely under cred_id)",
            state_record.provider_key,
        )

        return CredentialReference(
            credential_id=sec_id,
            credential_type=AuthenticationType.OAUTH2,
            provider_key=state_record.provider_key,
            metadata={"scopes": ["read", "write"], "owner_id": owner_id},
        )

    def refresh_tokens(self, cred_ref: CredentialReference, secret_store: SecretStore) -> None:
        """Refresh OAuth2 access token using stored refresh token."""
        if not secret_store.exists(cred_ref.credential_id):
            raise AuthenticationFailedError(cred_ref.provider_key, "Credentials missing from SecretStore.")

        tokens = secret_store.retrieve(cred_ref.credential_id)
        tokens["access_token"] = f"mock_refreshed_token_{secrets.token_hex(16)}"
        tokens["refreshed_at"] = datetime.now(UTC).isoformat()
        secret_store.rotate(cred_ref.credential_id, tokens)

        logger.info("Refreshed OAuth2 token for provider '%s'", cred_ref.provider_key)
