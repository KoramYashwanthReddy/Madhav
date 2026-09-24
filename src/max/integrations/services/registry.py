"""Integration Registry Service for Module 29."""

import logging
import threading

from max.integrations.adapters.adapters import Module14ToolRegistryAdapter
from max.integrations.domain.enums import IntegrationStatus
from max.integrations.domain.exceptions import ActionExecutionError, ProviderNotFoundError
from max.integrations.domain.models import (
    Integration,
    IntegrationAction,
    IntegrationCapability,
    IntegrationProvider,
)
from max.integrations.providers.base_provider import ExternalIntegrationProvider
from max.integrations.repositories.repositories import (
    BaseIntegrationRepository,
    BaseProviderRepository,
    MemoryIntegrationRepository,
    MemoryProviderRepository,
)

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """Central registry managing providers, integrations, capability discovery, and ToolRegistry sync."""

    def __init__(
        self,
        integration_repo: BaseIntegrationRepository | None = None,
        provider_repo: BaseProviderRepository | None = None,
        tool_adapter: Module14ToolRegistryAdapter | None = None,
    ) -> None:
        self._integration_repo = integration_repo or MemoryIntegrationRepository()
        self._provider_repo = provider_repo or MemoryProviderRepository()
        self._tool_adapter = tool_adapter or Module14ToolRegistryAdapter()
        self._providers: dict[str, ExternalIntegrationProvider] = {}
        self._lock = threading.RLock()

    def register_provider(self, provider: ExternalIntegrationProvider) -> IntegrationProvider:
        """Register an integration provider adapter, populate capabilities, and sync to ToolRegistry."""
        with self._lock:
            self._providers[provider.provider_key] = provider

            caps = provider.list_capabilities()

            prov_entity = IntegrationProvider(
                provider_key=provider.provider_key,
                name=provider.name,
                status=IntegrationStatus.ACTIVE,
                capabilities=caps,
            )
            saved_prov = self._provider_repo.save(prov_entity)

            # Build or update matching Integration definition entity
            intg_key = provider.provider_key
            existing_intg = self._integration_repo.get_by_key(intg_key)

            actions: list[IntegrationAction] = []
            intg_id = existing_intg.integration_id if existing_intg else f"intg_{provider.provider_key}"

            for cap in caps:
                act = IntegrationAction(
                    integration_id=intg_id,
                    capability_id=cap.capability_id,
                    name=cap.name,
                    description=cap.description,
                    input_schema=cap.input_schema,
                    output_schema=cap.output_schema,
                    risk_level=cap.risk_level,
                )
                actions.append(act)

                # Auto-sync capability to Module 14 ToolRegistry
                try:
                    self._tool_adapter.sync_capability_as_tool(
                        provider_key=provider.provider_key,
                        capability_name=cap.name,
                        description=cap.description,
                        category_name=cap.category.value,
                        risk_level_name=cap.risk_level.value,
                        input_schema=cap.input_schema,
                        output_schema=cap.output_schema,
                    )
                except Exception as exc:
                    logger.warning("Failed to sync capability '%s' to ToolRegistry: %s", cap.name, exc)

            intg_entity = Integration(
                integration_id=intg_id,
                integration_key=intg_key,
                name=provider.name,
                description=f"Integration provider for {provider.name}",
                category=provider.category,
                status=IntegrationStatus.ACTIVE,
                capabilities=caps,
                actions=actions,
            )
            self._integration_repo.save(intg_entity)

            logger.info("Registered integration provider '%s' with %d capabilities", provider.provider_key, len(caps))
            return saved_prov

    def get_provider(self, provider_key: str) -> ExternalIntegrationProvider:
        """Retrieve registered provider instance by provider_key."""
        with self._lock:
            prov = self._providers.get(provider_key)
            if not prov:
                raise ProviderNotFoundError(provider_key)
            return prov

    def list_providers(self) -> list[IntegrationProvider]:
        """List all registered provider entities."""
        return self._provider_repo.list()

    def list_integrations(self, category: str | None = None) -> list[Integration]:
        """List registered integration definitions."""
        return self._integration_repo.list(category=category)

    def discover_capabilities(self, provider_key: str) -> list[IntegrationCapability]:
        """Discover available capabilities for a provider."""
        provider = self.get_provider(provider_key)
        return provider.list_capabilities()

    def resolve_action(self, integration_id_or_key: str, action_name: str) -> tuple[Integration, IntegrationAction]:
        """Resolve integration and action entity by ID or key."""
        intg = self._integration_repo.get_by_id(integration_id_or_key) or self._integration_repo.get_by_key(integration_id_or_key)
        if not intg:
            raise ActionExecutionError(action_name, "NOT_FOUND", f"Integration '{integration_id_or_key}' not found.")

        matched_action = None
        for act in intg.actions:
            if act.name == action_name or act.capability_id == action_name:
                matched_action = act
                break

        if not matched_action:
            raise ActionExecutionError(action_name, "NOT_FOUND", f"Action '{action_name}' not found on integration '{intg.name}'.")

        return intg, matched_action
