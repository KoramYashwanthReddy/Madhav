"""REST API endpoints for Module 07 Conversation Engine."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from max.conversation.domain.enums import ConversationStatus
from max.conversation.exceptions import ConversationEngineError
from max.conversation.schemas.requests import (
    CreateConversationRequest,
    SendMessageRequest,
    UpdateConversationRequest,
    UpdateTitleRequest,
)
from max.conversation.schemas.responses import (
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationSummaryResponse,
    MessageResponse,
    TurnResponse,
)
from max.conversation.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversation Engine"])

_conversation_service_instance: ConversationService | None = None


def get_conversation_service() -> ConversationService:
    """Dependency provider returning singleton ConversationService instance."""
    global _conversation_service_instance
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService()
    return _conversation_service_instance


def set_conversation_service(service: ConversationService | None) -> None:
    """Helper to set or reset singleton instance (useful for test isolation)."""
    global _conversation_service_instance
    _conversation_service_instance = service


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=201,
    summary="Create a new conversation",
    description="Initialize a new structured conversation aggregate.",
)
async def create_conversation(
    req: CreateConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Create conversation endpoint."""
    try:
        conv = await service.create_conversation(
            owner_id="default_owner",
            title=req.title,
            metadata=req.metadata,
        )
        if req.model_reference:
            conv.settings.model_reference = req.model_reference
        conv.settings.auto_title_enabled = req.auto_title_enabled
        await service.repository.update_conversation(conv)
        return ConversationResponse.from_domain(conv)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List conversations",
    description="Retrieve paginated list of conversations for owner.",
)
async def list_conversations(
    status: ConversationStatus | None = Query(default=None, description="Optional status filter"),
    limit: int = Query(default=50, ge=1, le=200, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    """List conversations endpoint."""
    try:
        summaries, total = await service.list_conversations(
            owner_id="default_owner", status=status, limit=limit, offset=offset
        )
        has_more = (offset + limit) < total
        return ConversationListResponse(
            conversations=[ConversationSummaryResponse.from_domain(s) for s in summaries],
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation by ID",
    description="Retrieve full details for a specific conversation.",
)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Get conversation endpoint."""
    try:
        conv = await service.get_conversation(conversation_id)
        return ConversationResponse.from_domain(conv)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation metadata",
    description="Modify title, settings, or metadata for a conversation.",
)
async def update_conversation(
    conversation_id: UUID,
    req: UpdateConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Update conversation endpoint."""
    try:
        conv = await service.get_conversation(conversation_id)

        if req.model_reference is not None:
            conv.settings.model_reference = req.model_reference
        if req.auto_title_enabled is not None:
            conv.settings.auto_title_enabled = req.auto_title_enabled

        updated = await service.update_conversation(
            conversation_id=conversation_id,
            title=req.title,
            settings=conv.settings,
            metadata=req.metadata,
        )
        return ConversationResponse.from_domain(updated)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.patch(
    "/{conversation_id}/title",
    response_model=ConversationResponse,
    summary="Explicitly update title",
    description="Update the title string of a conversation.",
)
async def update_title(
    conversation_id: UUID,
    req: UpdateTitleRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Update conversation title endpoint."""
    try:
        updated = await service.update_title(conversation_id=conversation_id, title=req.title)
        return ConversationResponse.from_domain(updated)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post(
    "/{conversation_id}/archive",
    response_model=ConversationResponse,
    summary="Archive conversation",
    description="Transition conversation state to ARCHIVED.",
)
async def archive_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Archive conversation endpoint."""
    try:
        archived = await service.archive_conversation(conversation_id)
        return ConversationResponse.from_domain(archived)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post(
    "/{conversation_id}/restore",
    response_model=ConversationResponse,
    summary="Restore archived conversation",
    description="Transition conversation state from ARCHIVED back to ACTIVE.",
)
async def restore_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Restore conversation endpoint."""
    try:
        restored = await service.restore_conversation(conversation_id)
        return ConversationResponse.from_domain(restored)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.delete(
    "/{conversation_id}",
    status_code=204,
    summary="Delete conversation",
    description="Soft-delete a conversation aggregate safely.",
)
async def delete_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> None:
    """Delete conversation endpoint."""
    try:
        await service.delete_conversation(conversation_id, soft_delete=True)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationHistoryResponse,
    summary="List message history",
    description="Retrieve paginated list of chronological messages in conversation.",
)
async def list_messages(
    conversation_id: UUID,
    limit: int = Query(default=50, ge=1, le=200, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    asc: bool = Query(default=True, description="Sort order: True for ascending sequence"),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationHistoryResponse:
    """List conversation messages endpoint."""
    try:
        history = await service.list_messages(
            conversation_id=conversation_id, limit=limit, offset=offset, asc=asc
        )
        return ConversationHistoryResponse.from_domain(history)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post(
    "/{conversation_id}/messages",
    response_model=TurnResponse,
    status_code=200,
    summary="Send message / execute turn",
    description="Send user message, assemble context, invoke AI runtime, and return turn response.",
)
async def send_message(
    conversation_id: UUID,
    req: SendMessageRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> TurnResponse:
    """Send message endpoint."""
    try:
        result = await service.send_message(
            conversation_id=conversation_id,
            content=req.content,
            client_message_id=req.client_message_id,
            model_override=req.model_override,
            owner_id="default_owner",
        )
        return TurnResponse.from_domain(result)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get(
    "/{conversation_id}/messages/{message_id}",
    response_model=MessageResponse,
    summary="Get message by ID",
    description="Retrieve a specific message by its unique identifier.",
)
async def get_message(
    conversation_id: UUID,
    message_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> MessageResponse:
    """Get message endpoint."""
    try:
        msg = await service.get_message(conversation_id, message_id)
        return MessageResponse.from_domain(msg)
    except ConversationEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc
