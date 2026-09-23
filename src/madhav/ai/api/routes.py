"""AI Runtime REST API route handlers."""

from typing import Any

from fastapi import APIRouter, Depends, Query

from madhav.ai.domain.messages import AIMessage
from madhav.ai.domain.parameters import GenerationParameters
from madhav.ai.domain.requests import AIRequest
from madhav.ai.runtime.manager import AIRuntimeManager
from madhav.ai.schemas.requests import AIGenerateRequest
from madhav.ai.schemas.responses import (
    AIGenerateResponse,
    RuntimeCapabilitiesResponse,
    RuntimeStatusResponse,
)
from madhav.core.request_id import get_request_id
from madhav.core.responses import APIResponse

router = APIRouter(prefix="/ai", tags=["AI Runtime"])

_ai_runtime_manager_instance = AIRuntimeManager()


def get_ai_runtime_manager() -> AIRuntimeManager:
    """FastAPI dependency injecting AIRuntimeManager instance."""
    return _ai_runtime_manager_instance


@router.post("/generate", response_model=APIResponse[AIGenerateResponse])
async def generate_text(
    payload: AIGenerateRequest,
    manager: AIRuntimeManager = Depends(get_ai_runtime_manager),
) -> APIResponse[AIGenerateResponse]:
    """Execute AI text generation request using active runtime backend."""
    req_id = get_request_id()

    try:
        domain_messages = [
            AIMessage(role=msg.role, content=msg.content) for msg in payload.messages
        ]
        domain_params = GenerationParameters(
            temperature=payload.generation.temperature,
            top_p=payload.generation.top_p,
            max_tokens=payload.generation.max_tokens,
            stop_sequences=payload.generation.stop_sequences,
        )
        ai_request = AIRequest(
            request_id=req_id,
            messages=domain_messages,
            generation=domain_params,
            metadata=payload.metadata,
            timeout=payload.timeout,
            stream=False,
        )
    except Exception as exc:
        from madhav.ai.exceptions import AIValidationError

        raise AIValidationError(
            f"Invalid request parameters: {exc!s}",
            details={"request_id": req_id},
        ) from exc

    response = await manager.generate(ai_request, provider_override=payload.provider)

    data: dict[str, Any] = response.model_dump()
    return APIResponse(
        success=True,
        data=AIGenerateResponse(**data),
        request_id=req_id,
    )


@router.get("/runtime/status", response_model=APIResponse[RuntimeStatusResponse])
async def get_runtime_status(
    provider: str | None = Query(default=None, description="Optional provider identifier filter"),
    manager: AIRuntimeManager = Depends(get_ai_runtime_manager),
) -> APIResponse[RuntimeStatusResponse]:
    """Retrieve operational status for active or specified runtime backend."""
    status = await manager.get_status(provider=provider)
    return APIResponse(
        success=True,
        data=RuntimeStatusResponse(**status.model_dump()),
        request_id=get_request_id(),
    )


@router.get("/runtime/capabilities", response_model=APIResponse[RuntimeCapabilitiesResponse])
async def get_runtime_capabilities(
    provider: str | None = Query(default=None, description="Optional provider identifier filter"),
    manager: AIRuntimeManager = Depends(get_ai_runtime_manager),
) -> APIResponse[RuntimeCapabilitiesResponse]:
    """Retrieve capability matrix for active or specified runtime backend."""
    caps = await manager.get_capabilities(provider=provider)
    return APIResponse(
        success=True,
        data=RuntimeCapabilitiesResponse(**caps.model_dump()),
        request_id=get_request_id(),
    )
