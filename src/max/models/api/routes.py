"""Model Management REST API route handlers."""

from typing import Any

from fastapi import APIRouter, Depends, Query

from max.core.request_id import get_request_id
from max.core.responses import APIResponse
from max.models.domain.artifact import ModelArtifact
from max.models.domain.capabilities import ModelCapabilities
from max.models.domain.identity import ModelIdentifier
from max.models.domain.model import Model
from max.models.domain.requirements import ModelRequirements
from max.models.schemas.requests import ModelRegisterRequest, ModelUpdateRequest
from max.models.schemas.responses import (
    ModelListResponse,
    ModelResponse,
    ModelStatusResponse,
    ModelVerifyResponse,
)
from max.models.services.manager import ModelManager

router = APIRouter(prefix="/models", tags=["Model Management"])

_model_manager_instance: ModelManager | None = None


def get_model_manager() -> ModelManager:
    """FastAPI dependency providing ModelManager instance."""
    global _model_manager_instance
    if _model_manager_instance is None:
        _model_manager_instance = ModelManager()
    return _model_manager_instance


@router.get("", response_model=APIResponse[ModelListResponse])
async def list_models(
    provider: str | None = Query(default=None, description="Filter by provider"),
    state: str | None = Query(default=None, description="Filter by lifecycle state"),
    target_runtime: str | None = Query(default=None, description="Filter by target runtime"),
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelListResponse]:
    """List registered model definitions with optional filtering."""
    models = await manager.list_models(
        provider=provider, state=state, target_runtime=target_runtime
    )
    model_dtos = [_to_model_dto(m) for m in models]
    return APIResponse(
        success=True,
        data=ModelListResponse(models=model_dtos, total=len(model_dtos)),
        request_id=get_request_id(),
    )


@router.post("", response_model=APIResponse[ModelResponse], status_code=201)
async def register_model(
    payload: ModelRegisterRequest,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelResponse]:
    """Register a new model definition."""
    req_id = get_request_id()

    artifact_entity = None
    if payload.artifact:
        artifact_entity = ModelArtifact(
            model_id=payload.model_id,
            format=payload.artifact.format,
            path=payload.artifact.path,
            size_bytes=payload.artifact.size_bytes,
            checksum=payload.artifact.checksum,
            checksum_algorithm=payload.artifact.checksum_algorithm,
        )

    model = Model(
        identifier=ModelIdentifier(
            model_id=payload.model_id,
            provider=payload.provider,
            name=payload.name,
            version=payload.version,
            revision=payload.revision,
        ),
        capabilities=ModelCapabilities(**payload.capabilities.model_dump()),
        requirements=ModelRequirements(**payload.requirements.model_dump()),
        artifact=artifact_entity,
        target_runtime=payload.target_runtime,
        description=payload.description,
        metadata=payload.metadata,
    )

    registered = await manager.register_model(model)
    return APIResponse(
        success=True,
        data=_to_model_dto(registered),
        request_id=req_id,
    )


@router.get("/{model_id}", response_model=APIResponse[ModelResponse])
async def get_model(
    model_id: str,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelResponse]:
    """Retrieve details for a specific model definition."""
    model = await manager.get_model(model_id)
    return APIResponse(
        success=True,
        data=_to_model_dto(model),
        request_id=get_request_id(),
    )


@router.patch("/{model_id}", response_model=APIResponse[ModelResponse])
async def update_model(
    model_id: str,
    payload: ModelUpdateRequest,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelResponse]:
    """Update metadata for an existing model definition."""
    updates = payload.model_dump(exclude_unset=True)
    updated = await manager.update_model(model_id, updates)
    return APIResponse(
        success=True,
        data=_to_model_dto(updated),
        request_id=get_request_id(),
    )


@router.delete("/{model_id}", response_model=APIResponse[dict[str, Any]])
async def delete_model(
    model_id: str,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[dict[str, Any]]:
    """Unregister a model definition from the registry (preserves files on disk)."""
    success = await manager.delete_model(model_id)
    return APIResponse(
        success=True,
        data={"model_id": model_id, "deleted": success, "message": "Model metadata unregistered."},
        request_id=get_request_id(),
    )


@router.post("/{model_id}/load", response_model=APIResponse[ModelResponse])
async def load_model(
    model_id: str,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelResponse]:
    """Load model into operational state."""
    loaded = await manager.load_model(model_id)
    return APIResponse(
        success=True,
        data=_to_model_dto(loaded),
        request_id=get_request_id(),
    )


@router.post("/{model_id}/unload", response_model=APIResponse[ModelResponse])
async def unload_model(
    model_id: str,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelResponse]:
    """Unload model from operational state."""
    unloaded = await manager.unload_model(model_id)
    return APIResponse(
        success=True,
        data=_to_model_dto(unloaded),
        request_id=get_request_id(),
    )


@router.get("/{model_id}/status", response_model=APIResponse[ModelStatusResponse])
async def get_model_status(
    model_id: str,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelStatusResponse]:
    """Retrieve diagnostic status snapshot for specified model."""
    status = await manager.get_status(model_id)
    return APIResponse(
        success=True,
        data=ModelStatusResponse(**status.model_dump()),
        request_id=get_request_id(),
    )


@router.get("/{model_id}/capabilities", response_model=APIResponse[ModelCapabilities])
async def get_model_capabilities(
    model_id: str,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelCapabilities]:
    """Retrieve capability matrix for specified model."""
    model = await manager.get_model(model_id)
    return APIResponse(
        success=True,
        data=model.capabilities,
        request_id=get_request_id(),
    )


@router.post("/{model_id}/verify", response_model=APIResponse[ModelVerifyResponse])
async def verify_model_checksum(
    model_id: str,
    manager: ModelManager = Depends(get_model_manager),
) -> APIResponse[ModelVerifyResponse]:
    """Verify SHA-256 artifact checksum for local model file."""
    verified = await manager.verify_artifact_checksum(model_id)
    return APIResponse(
        success=True,
        data=ModelVerifyResponse(
            model_id=model_id,
            verified=verified,
            checksum_algorithm="sha256",
            message="Artifact SHA-256 checksum verification succeeded.",
        ),
        request_id=get_request_id(),
    )


def _to_model_dto(model: Model) -> ModelResponse:
    """Helper mapping domain Model entity to ModelResponse DTO."""
    data = model.model_dump()
    data["model_id"] = model.model_id
    data["provider"] = model.identifier.provider
    data["name"] = model.identifier.name
    data["version"] = model.identifier.version
    data["revision"] = model.identifier.revision
    return ModelResponse(**data)
