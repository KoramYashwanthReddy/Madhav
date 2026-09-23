"""Core ContextManager facade orchestrating context gathering and package assembly."""

import logging
from typing import Any

from madhav.ai.domain.requests import AIRequest
from madhav.config.settings import get_settings
from madhav.context.domain.budget import ContextBudget
from madhav.context.domain.item import ContextItem
from madhav.context.domain.package import ContextPackage
from madhav.context.domain.policy import ContextPolicy
from madhav.context.domain.request import ContextRequest
from madhav.context.services.assembler import ContextAssembler
from madhav.context.services.estimator import ApproximateTokenEstimator, TokenEstimator
from madhav.context.services.selector import ContextSelector
from madhav.context.services.sources import ContextSourceRegistry
from madhav.context.services.truncator import ContextTruncator
from madhav.context.services.validator import ContextValidator
from madhav.models.services.manager import ModelManager

logger = logging.getLogger("madhav.context.manager")


class ContextManager:
    """Facade orchestrating Module 06 Context Management lifecycle and package building."""

    def __init__(
        self,
        registry: ContextSourceRegistry | None = None,
        estimator: TokenEstimator | None = None,
        model_manager: ModelManager | None = None,
    ) -> None:
        self._settings = get_settings()
        self._registry = registry or ContextSourceRegistry()
        self._estimator = estimator or ApproximateTokenEstimator()
        self._model_manager = model_manager or ModelManager()
        self._truncator = ContextTruncator(self._estimator)
        self._selector = ContextSelector(self._estimator, self._truncator)
        self._assembler = ContextAssembler()
        self._validator = ContextValidator()

    @property
    def registry(self) -> ContextSourceRegistry:
        """Expose inner context source registry."""
        return self._registry

    async def resolve_budget(
        self, request: ContextRequest, policy: ContextPolicy
    ) -> ContextBudget:
        """Resolve ContextBudget from request, Module 05 metadata, or fallback config."""

        if request.budget is not None:
            return request.budget

        max_tokens = self._settings.context.default_max_tokens
        model_ref = request.model_reference or self._settings.models.default_model

        if model_ref:
            try:
                model_entity = await self._model_manager.get_model(model_ref)
                if model_entity and model_entity.requirements:
                    max_tokens = model_entity.requirements.context_length
            except Exception as exc:
                logger.debug("Could not resolve model context length for '%s': %s", model_ref, exc)
                max_tokens = self._settings.context.default_max_tokens

        return ContextBudget(
            max_tokens=max_tokens,
            reserved_tokens=self._settings.context.reserved_output_tokens,
            safety_margin=self._settings.context.safety_margin_tokens,
        )

    async def build_context(self, request: ContextRequest) -> ContextPackage:
        """Process ContextRequest end-to-end and build a validated ContextPackage."""
        # 1. Validate incoming request
        self._validator.validate_request(request)

        # 2. Resolve policy
        policy = request.policy or ContextPolicy.default()

        # 3. Resolve budget
        budget = await self.resolve_budget(request, policy)

        # 4. Gather candidate context items from all registered sources
        candidate_items: list[ContextItem] = []
        sources = self._registry.list_sources()

        for src_meta in sources:
            source_id = src_meta["source_id"]
            source_obj = self._registry.get(source_id)
            if source_obj and getattr(source_obj, "enabled", True):
                try:
                    items = source_obj.provide(request)
                    candidate_items.extend(items)
                except Exception as exc:
                    logger.warning("ContextSource '%s' failed to provide items: %s", source_id, exc)

        # 5. Select, prioritize, truncate, and budget items
        included, truncated, dropped, report = self._selector.select(
            candidates=candidate_items,
            budget=budget,
            policy=policy,
        )

        # 6. Assemble ContextPackage
        package = self._assembler.assemble_package(
            request_id=request.request_id,
            items=included,
            budget=budget,
            truncated_items=truncated,
            dropped_items=dropped,
            report=report,
        )

        # 7. Validate final package
        self._validator.validate_package(package, policy)

        # 8. Safe structured logging
        logger.info(
            "ContextPackage built successfully: request_id=%s items=%d tokens=%d/%d policy=%s",
            package.request_id,
            len(package.items),
            package.token_estimate,
            budget.available_input_tokens,
            policy.name,
        )

        return package

    async def prepare_ai_request(
        self, request: ContextRequest, metadata: dict[str, Any] | None = None
    ) -> AIRequest:
        """Build ContextPackage and convert it directly into Module 04 AIRequest."""
        package = await self.build_context(request)
        model_target = request.model_reference or self._settings.models.default_model
        return self._assembler.to_ai_request(package, model=model_target, metadata=metadata)
