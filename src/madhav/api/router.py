"""Centralized API router registration."""

from fastapi import APIRouter, FastAPI

from madhav.agents.api.routes import router as agents_router
from madhav.ai.api.routes import router as ai_router
from madhav.api.health import router as health_router
from madhav.context.api.routes import router as context_router
from madhav.conversation.api.routes import router as conversation_router
from madhav.identity.api.routes import router as identity_router
from madhav.knowledge.api.routes import router as knowledge_router
from madhav.memory.api.routes import router as memory_router
from madhav.models.api.routes import router as models_router
from madhav.rag.api.routes import router as rag_router
from madhav.reasoning.api.routes import plan_router, reasoning_router
from madhav.tasks.api.routes import plan_task_router, task_group_router, tasks_router


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
    app.include_router(v1_router)



