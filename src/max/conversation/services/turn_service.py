"""ConversationTurnService orchestrating multi-turn chat execution."""

import logging
from uuid import UUID

from max.ai.domain.enums import FinishReason
from max.ai.domain.usage import AIUsage
from max.ai.exceptions import AIRuntimeError
from max.ai.runtime.manager import AIRuntimeManager
from max.config.settings import get_settings
from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.services.manager import ContextManager
from max.conversation.domain.conversation import Conversation
from max.conversation.domain.enums import ConversationStatus, MessageRole, MessageStatus
from max.conversation.domain.message import Message
from max.conversation.exceptions import (
    ConversationArchivedError,
    ConversationDeletedError,
    ConversationNotFoundError,
    ConversationTurnError,
    MessageValidationError,
)
from max.conversation.repositories.base import ConversationRepository
from max.conversation.services.title_generator import DeterministicTitleGenerator
from max.identity.services.identity_service import IdentityService
from max.models.services.manager import ModelManager

logger = logging.getLogger(__name__)


class TurnResult:
    """Normalized response payload from a completed conversation turn execution."""

    def __init__(
        self,
        conversation: Conversation,
        user_message: Message,
        assistant_message: Message,
        usage: AIUsage | None = None,
        execution_time_ms: float | None = None,
    ) -> None:
        self.conversation = conversation
        self.user_message = user_message
        self.assistant_message = assistant_message
        self.usage = usage
        self.execution_time_ms = execution_time_ms


class ConversationTurnService:
    """Service orchestrating end-to-end multi-turn chat processing across Modules 03-07."""

    def __init__(
        self,
        repository: ConversationRepository,
        context_manager: ContextManager | None = None,
        ai_runtime_manager: AIRuntimeManager | None = None,
        identity_service: IdentityService | None = None,
        model_manager: ModelManager | None = None,
        title_generator: DeterministicTitleGenerator | None = None,
    ) -> None:
        self._repository = repository
        self._model_manager = model_manager or ModelManager()
        self._context_manager = context_manager or ContextManager(model_manager=self._model_manager)
        self._ai_runtime_manager = ai_runtime_manager or AIRuntimeManager()
        self._identity_service = identity_service or IdentityService()
        self._title_generator = title_generator or DeterministicTitleGenerator()
        self._settings = get_settings().conversation

    async def execute_turn(
        self,
        conversation_id: UUID,
        user_content: str,
        client_message_id: str | None = None,
        model_override: str | None = None,
        owner_id: str = "default_owner",
    ) -> TurnResult:
        """Execute a single conversational turn."""

        # 1. Validate content
        if not user_content or not user_content.strip():
            raise MessageValidationError(
                "Message content cannot be empty or whitespace-only.",
                details={"conversation_id": str(conversation_id)},
            )
        if len(user_content) > self._settings.max_message_characters:
            raise MessageValidationError(
                f"Message content length ({len(user_content)}) exceeds maximum "
                f"character limit ({self._settings.max_message_characters}).",
                details={"max_characters": self._settings.max_message_characters},
            )

        # 2. Retrieve conversation
        conv = await self._repository.get_conversation(conversation_id)
        if conv is None:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} not found.",
                details={"conversation_id": str(conversation_id)},
            )
        if conv.status == ConversationStatus.DELETED:
            raise ConversationDeletedError(
                f"Conversation {conversation_id} is deleted.",
                details={"conversation_id": str(conversation_id)},
            )
        if conv.status == ConversationStatus.ARCHIVED:
            raise ConversationArchivedError(
                f"Conversation {conversation_id} is archived.",
                details={"conversation_id": str(conversation_id)},
            )

        # 3. Idempotency Check
        if client_message_id:
            existing_user_msg = await self._repository.get_message_by_client_id(
                conversation_id, client_message_id
            )
            if existing_user_msg:
                # Retrieve next message if assistant response already created
                messages, _ = await self._repository.list_messages(
                    conversation_id, limit=10, offset=0, asc=True
                )
                for i, msg in enumerate(messages):
                    if msg.message_id == existing_user_msg.message_id and i + 1 < len(messages):
                        existing_asst_msg = messages[i + 1]
                        if existing_asst_msg.role == MessageRole.ASSISTANT:
                            return TurnResult(
                                conversation=conv,
                                user_message=existing_user_msg,
                                assistant_message=existing_asst_msg,
                            )

        # 4. Fetch prior history (before adding current message)
        prior_messages = await self._repository.get_latest_messages(
            conversation_id, limit=self._settings.history_retrieval_limit
        )

        # 5. Create USER message
        user_seq = await self._repository.get_next_sequence(conversation_id)
        user_msg = Message(
            conversation_id=conversation_id,
            sequence=user_seq,
            role=MessageRole.USER,
            content=user_content.strip(),
            status=MessageStatus.PROCESSING,
            client_message_id=client_message_id,
        )
        saved_user_msg = await self._repository.create_message(user_msg)

        # 6. Auto Title Generation on first turn
        if conv.settings.auto_title_enabled and (
            conv.title is None or conv.title == "New conversation"
        ):
            new_title = self._title_generator.generate_title(user_content)
            conv.title = new_title
            await self._repository.update_conversation(conv)

        # 7. Construct Identity Context
        identity_ctx = await self._identity_service.build_identity_context()

        # 8. Determine target model
        target_model = (
            model_override or conv.settings.model_reference or get_settings().models.default_model
        )

        # Validate model reference via Module 05
        model_meta = await self._model_manager.get_model(target_model)
        if model_meta is None:
            # Fallback to default stub if invalid
            target_model = get_settings().models.default_model

        # 9. Build ContextRequest for Module 06
        ctx_request = ContextRequest(
            user_request=user_content.strip(),
            identity_context=identity_ctx,
            model_reference=target_model,
            policy=ContextPolicy.default(),
            source_options={"conversation_messages": prior_messages},
        )

        # 10. Execute AI Runtime Inference
        assistant_msg: Message
        usage: AIUsage | None = None
        exec_time_ms: float | None = None

        try:
            ai_request = await self._context_manager.prepare_ai_request(ctx_request)
            ai_response = await self._ai_runtime_manager.generate(ai_request)

            saved_user_msg.status = MessageStatus.COMPLETED

            usage = ai_response.usage
            exec_time_ms = ai_response.execution.duration_ms

            asst_seq = await self._repository.get_next_sequence(conversation_id)
            asst_msg = Message(
                conversation_id=conversation_id,
                sequence=asst_seq,
                role=MessageRole.ASSISTANT,
                content=ai_response.content,
                status=MessageStatus.COMPLETED,
                metadata={
                    "model": ai_response.model_reference,
                    "provider": ai_response.provider,
                    "finish_reason": (
                        ai_response.finish_reason.value
                        if ai_response.finish_reason
                        else FinishReason.STOP.value
                    ),
                    "usage": ai_response.usage.model_dump() if ai_response.usage else {},
                    "latency_ms": ai_response.execution.duration_ms,
                },
            )
            assistant_msg = await self._repository.create_message(asst_msg)

        except Exception as exc:
            logger.error(
                "AI Runtime execution failed for conversation %s: %s", conversation_id, exc
            )
            saved_user_msg.status = MessageStatus.FAILED

            asst_seq = await self._repository.get_next_sequence(conversation_id)
            asst_msg = Message(
                conversation_id=conversation_id,
                sequence=asst_seq,
                role=MessageRole.ASSISTANT,
                content="[Assistant response failed due to runtime error.]",
                status=MessageStatus.FAILED,
                metadata={"error": str(exc)},
            )
            assistant_msg = await self._repository.create_message(asst_msg)
            if not isinstance(exc, AIRuntimeError):
                raise ConversationTurnError(
                    f"Conversation turn execution failed: {exc}",
                    details={"conversation_id": str(conversation_id)},
                ) from exc

        updated_conv = await self._repository.get_conversation(conversation_id)
        return TurnResult(
            conversation=updated_conv or conv,
            user_message=saved_user_msg,
            assistant_message=assistant_msg,
            usage=usage,
            execution_time_ms=exec_time_ms,
        )
