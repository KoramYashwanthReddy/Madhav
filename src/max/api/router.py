"""Centralized API router registration."""

from fastapi import APIRouter, FastAPI

from max.agents.api.routes import router as agents_router
from max.ai.api.routes import router as ai_router
from max.api.health import router as health_router
from max.browser.api.routes import router as browser_router
from max.computer.api.routes import computer_router
from max.context.api.routes import router as context_router
from max.conversation.api.routes import router as conversation_router
from max.filesystem.api.routes import router as filesystem_router
from max.identity.api.routes import router as identity_router
from max.knowledge.api.routes import router as knowledge_router
from max.memory.api.routes import router as memory_router
from max.models.api.routes import router as models_router
from max.rag.api.routes import router as rag_router
from max.reasoning.api.routes import plan_router, reasoning_router
from max.security.api.routes import router as security_router
from max.tasks.api.routes import plan_task_router, task_group_router, tasks_router
from max.tools.api.routes import router as tools_router
from max.web_intelligence.api.routes import router as web_intelligence_router
from max.coding.api.routes import router as coding_router
from max.developer.api.routes import router as developer_router
from max.document.api.routes import router as document_router
from max.vision.api.routes import router as vision_router
from max.speech.api.routes import router as speech_router
from max.notifications.api.routes import router as notifications_router
from max.scheduler.api.routes import automations_router, scheduler_router
from max.integrations.api.routes import (
    connections_router,
    integrations_router,
    webhooks_router,
)
from max.proactive.api.routes import router as proactive_router
from max.personalization.api.routes import router as personalization_router
from max.evaluation.api.routes import router as evaluation_router
from max.observability.api.routes import router as observability_router


def register_routers(app: FastAPI) -> None:
    """Register top-level and versioned API routers with the FastAPI app."""
    # Top level system foundation endpoints
    app.include_router(health_router)

    # API v1 Router prefix foundation
    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(identity_router)
    v1_router.include_router(ai_router)
    v1_router.include_router(models_router)
    v1_router.include_router(context_router)
    v1_router.include_router(conversation_router)
    v1_router.include_router(memory_router)
    v1_router.include_router(knowledge_router)
    v1_router.include_router(rag_router)
    v1_router.include_router(reasoning_router)
    v1_router.include_router(plan_router)
    v1_router.include_router(tasks_router)
    v1_router.include_router(task_group_router)
    v1_router.include_router(plan_task_router)
    v1_router.include_router(agents_router)
    v1_router.include_router(tools_router)
    v1_router.include_router(security_router)
    v1_router.include_router(computer_router)
    v1_router.include_router(filesystem_router)
    v1_router.include_router(browser_router)
    v1_router.include_router(web_intelligence_router)
    v1_router.include_router(coding_router)
    v1_router.include_router(developer_router)
    v1_router.include_router(document_router)
    v1_router.include_router(vision_router)
    v1_router.include_router(speech_router)
    v1_router.include_router(notifications_router)
    v1_router.include_router(scheduler_router)
    v1_router.include_router(automations_router)
    v1_router.include_router(integrations_router)
    v1_router.include_router(connections_router)
    v1_router.include_router(webhooks_router)
    v1_router.include_router(proactive_router)
    v1_router.include_router(personalization_router)
    v1_router.include_router(evaluation_router)
    v1_router.include_router(observability_router)
    app.include_router(v1_router)







