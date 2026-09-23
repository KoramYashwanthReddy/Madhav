"""End-to-End integration test for Module 03 -> Module 06 -> Module 05 -> Module 04 context flow."""

import pytest

from max.ai.runtime.manager import AIRuntimeManager
from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.services.manager import ContextManager
from max.identity.domain.assistant import AssistantIdentity
from max.identity.domain.context import IdentityContext
from max.identity.domain.owner import OwnerIdentity
from max.identity.domain.profile import PersonalProfile
from max.models.services.manager import ModelManager


@pytest.mark.asyncio
async def test_end_to_end_context_to_ai_runtime_flow() -> None:
    """Verify end-to-end integration across Modules 03, 06, 05, and 04 completely offline."""
    # 1. Setup Module 03 Identity Context
    identity_ctx = IdentityContext(
        assistant=AssistantIdentity(name="Max"),
        owner=OwnerIdentity(display_name="Koram Yashwanth", preferred_name="Yashwanth"),
        profile=PersonalProfile(),
    )

    # 2. Instantiate Module 05 ModelManager and Module 04 AIRuntimeManager
    model_manager = ModelManager()
    ai_runtime_manager = AIRuntimeManager()

    # Verify development-stub model exists in Module 05
    stub_model = await model_manager.get_model("development-stub")
    assert stub_model is not None
    assert stub_model.requirements.context_length == 4096

    # 3. Instantiate Module 06 ContextManager
    context_manager = ContextManager(model_manager=model_manager)

    # 4. Construct ContextRequest with user request and identity context
    ctx_request = ContextRequest(
        user_request="Hello Max",
        identity_context=identity_ctx,
        model_reference="development-stub",
        policy=ContextPolicy.default(),
    )

    # 5. Build ContextPackage
    package = await context_manager.build_context(ctx_request)

    # Verify package components
    assert package.request_id == ctx_request.request_id
    assert len(package.items) >= 3  # System instruction, Safe identity, User request
    assert package.budget.max_tokens == 4096

    # Verify message categories present in package items
    categories = {item.category.value for item in package.items}
    assert "system" in categories
    assert "identity" in categories
    assert "request" in categories

    # 6. Convert ContextPackage into Module 04 AIRequest
    ai_request = await context_manager.prepare_ai_request(ctx_request)
    assert ai_request.model == "development-stub"
    assert len(ai_request.messages) >= 2  # System message + User request message

    # 7. Execute inference via Module 04 AI Runtime
    ai_response = await ai_runtime_manager.generate(ai_request)

    # Verify response from Module 04 runtime backend
    assert ai_response.request_id == ctx_request.request_id
    assert ai_response.content is not None
    assert len(ai_response.content) > 0

    assert ai_response.model_reference is not None
