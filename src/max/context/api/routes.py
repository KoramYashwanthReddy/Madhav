"""REST API endpoints for Module 06 Context Management."""

from fastapi import APIRouter, Depends, HTTPException

from max.config.settings import get_settings
from max.context.domain.budget import ContextBudget
from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.exceptions import ContextError
from max.context.schemas.requests import BuildContextRequest
from max.context.schemas.responses import (
    ContextItemSummary,
    ContextPackageResponse,
    ContextPoliciesResponse,
    ContextPolicySummary,
    ContextSourcesResponse,
    ContextSourceSummary,
)
from max.context.services.manager import ContextManager

router = APIRouter(prefix="/context", tags=["Context Management"])

# Singleton manager instance for REST API dependency injection
_context_manager_instance: ContextManager | None = None


def get_context_manager() -> ContextManager:
    """Dependency provider returning singleton ContextManager instance."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance


@router.post(
    "/build",
    response_model=ContextPackageResponse,
    summary="Assemble and inspect a context package",
    description=(
        "Processes a context request through candidate sources, policy, "
        "and budget to assemble a ContextPackage."
    ),
)
async def build_context_package(
    req: BuildContextRequest,
    manager: ContextManager = Depends(get_context_manager),
) -> ContextPackageResponse:
    """Build and return an assembled ContextPackage diagnostic response."""
    settings = get_settings()

    # 1. Resolve policy preset
    pname = (req.policy_name or "default").lower()
    if pname == "minimal":
        policy = ContextPolicy.minimal()
    elif pname == "full":
        policy = ContextPolicy.full()
    else:
        policy = ContextPolicy.default()

    if req.allow_sensitive_identity:
        policy.allow_sensitive_identity = True

    # 2. Resolve custom budget if requested
    budget = None
    if req.custom_max_tokens:
        budget = ContextBudget(
            max_tokens=req.custom_max_tokens,
            reserved_tokens=settings.context.reserved_output_tokens,
            safety_margin=settings.context.safety_margin_tokens,
        )

    # 3. Construct ContextRequest
    ctx_request = ContextRequest(
        user_request=req.user_request,
        model_reference=req.model_reference,
        policy=policy,
        budget=budget,
    )

    try:
        package = await manager.build_context(ctx_request)
    except ContextError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc

    # 4. Construct response DTO with privacy safeguards
    items_summary = [
        ContextItemSummary(
            context_id=item.context_id,
            category=item.category.value,
            priority=item.priority.name,
            token_estimate=item.token_estimate,
            source=item.source,
            required=item.required,
            truncated=item.metadata.get("truncated", False),
        )
        for item in package.items
    ]

    messages_payload = None
    if settings.context.debug_enabled:
        messages_payload = [
            {"role": msg.role.value, "content": msg.content} for msg in package.messages
        ]

    return ContextPackageResponse(
        request_id=package.request_id,
        message_count=len(package.messages),
        item_count=len(package.items),
        token_estimate=package.token_estimate,
        available_budget=package.budget.available_input_tokens,
        policy_used=policy.name,
        items_summary=items_summary,
        dropped_items=package.dropped_items,
        report=package.report,
        created_at=package.created_at,
        messages=messages_payload,
    )


@router.get(
    "/sources",
    response_model=ContextSourcesResponse,
    summary="List registered context sources",
    description="Retrieve all context sources currently registered in the ContextSourceRegistry.",
)
async def list_context_sources(
    manager: ContextManager = Depends(get_context_manager),
) -> ContextSourcesResponse:
    """Return list of registered context sources."""
    sources_data = manager.registry.list_sources()
    sources_list = [
        ContextSourceSummary(
            source_id=src["source_id"],
            category=str(src["category"]),
            priority=int(src["priority"]),
            enabled=bool(src["enabled"]),
        )
        for src in sources_data
    ]
    return ContextSourcesResponse(sources=sources_list, total=len(sources_list))


@router.get(
    "/policies",
    response_model=ContextPoliciesResponse,
    summary="List context policy presets",
    description="Retrieve available declarative context policy presets.",
)
async def list_context_policies() -> ContextPoliciesResponse:
    """Return available context policy presets."""
    presets = [ContextPolicy.default(), ContextPolicy.minimal(), ContextPolicy.full()]
    policy_summaries = [
        ContextPolicySummary(
            name=p.name,
            allowed_categories=[cat.value for cat in p.allowed_categories],
            required_categories=[cat.value for cat in p.required_categories],
            max_items=p.max_items,
            allow_sensitive_identity=p.allow_sensitive_identity,
        )
        for p in presets
    ]
    return ContextPoliciesResponse(policies=policy_summaries)
