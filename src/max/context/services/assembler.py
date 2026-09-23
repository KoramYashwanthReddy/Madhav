"""ContextAssembler service converting ContextItems into Module 04 AIMessages."""

from typing import Any

from max.ai.domain.enums import AIRole
from max.ai.domain.messages import AIMessage
from max.ai.domain.requests import AIRequest
from max.context.domain.budget import ContextBudget
from max.context.domain.enums import ContextCategory
from max.context.domain.item import ContextItem
from max.context.domain.package import ContextPackage
from max.context.domain.report import ContextSelectionReport


class ContextAssembler:
    """Assembles ContextItems into ordered AIMessage objects and builds ContextPackage."""

    def assemble_messages(self, items: list[ContextItem]) -> list[AIMessage]:
        """Convert selected ContextItems into an ordered list of Module 04 AIMessage objects."""
        messages: list[AIMessage] = []

        # 1. System level messages (SYSTEM, IDENTITY, INSTRUCTION)
        system_categories = {
            ContextCategory.SYSTEM,
            ContextCategory.IDENTITY,
            ContextCategory.INSTRUCTION,
        }
        system_items = [item for item in items if item.category in system_categories]

        if system_items:
            system_blocks = [item.content for item in system_items]
            combined_system_text = "\n\n".join(system_blocks)
            messages.append(AIMessage(role=AIRole.SYSTEM, content=combined_system_text))

        # 2. Contextual background messages (MEMORY, KNOWLEDGE, TOOL_RESULT)
        bg_categories = {
            ContextCategory.MEMORY,
            ContextCategory.KNOWLEDGE,
            ContextCategory.TOOL_RESULT,
        }
        bg_items = [item for item in items if item.category in bg_categories]

        if bg_items:
            bg_blocks = [f"[{item.category.value.upper()}]\n{item.content}" for item in bg_items]
            combined_bg_text = "Contextual Background:\n\n" + "\n\n".join(bg_blocks)
            messages.append(AIMessage(role=AIRole.SYSTEM, content=combined_bg_text))

        # 3. Conversation history items (CONVERSATION)
        conv_items = [item for item in items if item.category == ContextCategory.CONVERSATION]
        for citem in conv_items:
            # Map role if present in metadata, default to user
            role_str = citem.metadata.get("role", "user").lower()
            role = AIRole.USER
            if role_str == "assistant":
                role = AIRole.ASSISTANT
            elif role_str == "system":
                role = AIRole.SYSTEM

            messages.append(AIMessage(role=role, content=citem.content))

        # 4. Current user request item (REQUEST) - mandatory final user message
        request_items = [item for item in items if item.category == ContextCategory.REQUEST]
        if request_items:
            # If multiple request items, combine them
            req_text = "\n\n".join([item.content for item in request_items])
            messages.append(AIMessage(role=AIRole.USER, content=req_text))
        elif not messages:
            # Fallback safety message if no request item was present
            messages.append(AIMessage(role=AIRole.USER, content="Hello"))

        return messages

    def assemble_package(
        self,
        request_id: str,
        items: list[ContextItem],
        budget: ContextBudget,
        truncated_items: list[ContextItem],
        dropped_items: list[dict[str, Any]],
        report: ContextSelectionReport,
    ) -> ContextPackage:
        """Construct ContextPackage holding selected items, converted messages, and metrics."""

        messages = self.assemble_messages(items)
        total_tokens = sum(item.token_estimate for item in items)

        return ContextPackage(
            request_id=request_id,
            messages=messages,
            items=items,
            token_estimate=total_tokens,
            budget=budget,
            truncated_items=truncated_items,
            dropped_items=dropped_items,
            report=report,
        )

    def to_ai_request(
        self,
        package: ContextPackage,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIRequest:
        """Convert assembled ContextPackage into a Module 04 AIRequest ready for inference."""
        meta = {"context_package_id": package.request_id, "token_estimate": package.token_estimate}
        if metadata:
            meta.update(metadata)

        return AIRequest(
            request_id=package.request_id,
            messages=package.messages,
            model=model,
            metadata=meta,
        )
