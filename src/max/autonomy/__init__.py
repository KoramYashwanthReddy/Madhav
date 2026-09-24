"""Module 41 — Future Autonomous Intelligence package."""

from max.autonomy.domain import (
    ActionStatus,
    ApprovalRequest,
    ApprovalStatus,
    AutonomyHealth,
    AutonomyLevel,
    AutonomyPolicy,
    Milestone,
    Mission,
    MissionAction,
    MissionResult,
    MissionStatus,
    Objective,
    ResourceBudget,
    RiskLevel,
    SimulationMode,
)
from max.autonomy.policy import AutonomyPolicyService, AutonomyRiskService
from max.autonomy.approval import ApprovalService
from max.autonomy.budget import AutonomyBudgetService, MissionCircuitBreaker
from max.autonomy.orchestrator import (
    MissionExecutionService,
    MissionOrchestrator,
    MissionRecoveryService,
    MissionReplanningService,
    MissionVerificationService,
)
from max.autonomy.simulation import AutonomySimulationService
from max.autonomy.service import AutonomyService, get_autonomy_service

__all__ = [
    "ActionStatus",
    "ApprovalRequest",
    "ApprovalStatus",
    "AutonomyHealth",
    "AutonomyLevel",
    "AutonomyPolicy",
    "Milestone",
    "Mission",
    "MissionAction",
    "MissionResult",
    "MissionStatus",
    "Objective",
    "ResourceBudget",
    "RiskLevel",
    "SimulationMode",
    "AutonomyPolicyService",
    "AutonomyRiskService",
    "ApprovalService",
    "AutonomyBudgetService",
    "MissionCircuitBreaker",
    "MissionExecutionService",
    "MissionOrchestrator",
    "MissionRecoveryService",
    "MissionReplanningService",
    "MissionVerificationService",
    "AutonomySimulationService",
    "AutonomyService",
    "get_autonomy_service",
]
