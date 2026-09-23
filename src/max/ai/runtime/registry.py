"""Runtime registry for mapping and resolving model runtime adapters."""

import logging

from max.ai.exceptions import AIRuntimeUnavailableError
from max.ai.runtime.base import ModelRuntime
from max.ai.runtime.stub import StubModelRuntime

logger = logging.getLogger("max.ai.registry")


class RuntimeRegistry:
    """Registry maintaining active AI model runtime provider adapters."""

    def __init__(self) -> None:
        self._runtimes: dict[str, ModelRuntime] = {}
        # Pre-register deterministic development stub runtime
        stub_runtime = StubModelRuntime()
        self.register_runtime(stub_runtime)

    def register(self, provider_name: str, runtime: ModelRuntime) -> None:
        """Register a ModelRuntime adapter under a provider name."""
        self._runtimes[provider_name.lower()] = runtime
        logger.info(
            "Registered AI model runtime provider: '%s' (%s)",
            provider_name.lower(),
            runtime.model_reference,
        )

    def register_runtime(self, runtime: ModelRuntime) -> None:
        """Register a ModelRuntime adapter under its provider_name."""
        self.register(runtime.provider_name, runtime)

    def resolve(self, provider_name: str | None = None) -> ModelRuntime:
        """Resolve a registered ModelRuntime adapter by provider name."""
        return self.resolve_runtime(provider_name)

    def resolve_runtime(self, provider_name: str | None = None) -> ModelRuntime:
        """Resolve a registered ModelRuntime adapter by provider name."""
        key = (provider_name or "stub").lower()
        if key not in self._runtimes:
            logger.error("Attempted to resolve unregistered AI runtime provider: '%s'", key)
            raise AIRuntimeUnavailableError(
                f"No AI runtime registered for provider '{key}'. "
                f"Available: {list(self._runtimes.keys())}",
                details={
                    "requested_provider": key,
                    "available_providers": list(self._runtimes.keys()),
                },
            )
        return self._runtimes[key]

    def has_provider(self, provider_name: str) -> bool:
        """Check if a provider is registered."""
        return provider_name.lower() in self._runtimes

    def unregister(self, provider_name: str) -> bool:
        """Unregister a provider by name."""
        key = provider_name.lower()
        if key in self._runtimes:
            del self._runtimes[key]
            return True
        return False

    def list_providers(self) -> list[str]:
        """Return list of registered runtime provider identifiers."""
        return list(self._runtimes.keys())
