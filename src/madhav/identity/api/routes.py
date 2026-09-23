"""Identity & Personal Profile REST API route handlers."""

from fastapi import APIRouter, Depends

from madhav.core.request_id import get_request_id
from madhav.core.responses import APIResponse
from madhav.identity.schemas.assistant import AssistantIdentityResponse
from madhav.identity.schemas.owner import OwnerIdentityResponse, SafeIdentitySummary
from madhav.identity.schemas.preferences import (
    CommunicationPreferencesResponse,
    CommunicationPreferencesUpdate,
    LocalePreferencesResponse,
    LocalePreferencesUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from madhav.identity.schemas.profile import (
    PersonalProfileResponse,
    PersonalProfileUpdate,
    ProfileCompletenessResponse,
)
from madhav.identity.services.identity_service import IdentityService

router = APIRouter(prefix="/identity", tags=["Identity & Personal Profile"])

# Singleton service instance dependency for FastAPI DI
_identity_service_instance = IdentityService()


def get_identity_service() -> IdentityService:
    """FastAPI dependency injecting IdentityService instance."""
    return _identity_service_instance


@router.get("/assistant", response_model=APIResponse[AssistantIdentityResponse])
async def get_assistant(
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[AssistantIdentityResponse]:
    """Retrieve active assistant identity metadata."""
    assistant = await service.get_assistant()
    return APIResponse(
        success=True,
        data=AssistantIdentityResponse(**assistant.model_dump()),
        request_id=get_request_id(),
    )


@router.get("/owner", response_model=APIResponse[OwnerIdentityResponse])
async def get_owner(
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[OwnerIdentityResponse]:
    """Retrieve active owner identity metadata."""
    owner = await service.get_owner()
    return APIResponse(
        success=True,
        data=OwnerIdentityResponse(**owner.model_dump()),
        request_id=get_request_id(),
    )


@router.get("/profile", response_model=APIResponse[PersonalProfileResponse])
async def get_profile(
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[PersonalProfileResponse]:
    """Retrieve complete personal profile."""
    profile = await service.get_profile()
    return APIResponse(
        success=True,
        data=PersonalProfileResponse(**profile.model_dump()),
        request_id=get_request_id(),
    )


@router.get("/summary", response_model=APIResponse[SafeIdentitySummary])
async def get_summary(
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[SafeIdentitySummary]:
    """Retrieve non-sensitive safe identity summary."""
    summary = await service.get_summary()
    return APIResponse(
        success=True,
        data=summary,
        request_id=get_request_id(),
    )


@router.get("/preferences", response_model=APIResponse[UserPreferencesResponse])
async def get_preferences(
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[UserPreferencesResponse]:
    """Retrieve general user preferences."""
    profile = await service.get_profile()
    return APIResponse(
        success=True,
        data=UserPreferencesResponse(**profile.preferences.model_dump()),
        request_id=get_request_id(),
    )


@router.put("/profile", response_model=APIResponse[PersonalProfileResponse])
async def update_profile(
    payload: PersonalProfileUpdate,
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[PersonalProfileResponse]:
    """Update complete personal profile sections."""
    profile = await service.update_profile(payload)
    return APIResponse(
        success=True,
        data=PersonalProfileResponse(**profile.model_dump()),
        request_id=get_request_id(),
    )


@router.patch("/preferences", response_model=APIResponse[UserPreferencesResponse])
async def update_preferences(
    payload: UserPreferencesUpdate,
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[UserPreferencesResponse]:
    """Update user interaction preferences."""
    prefs = await service.update_user_preferences(payload)
    return APIResponse(
        success=True,
        data=UserPreferencesResponse(**prefs.model_dump()),
        request_id=get_request_id(),
    )


@router.patch("/communication", response_model=APIResponse[CommunicationPreferencesResponse])
async def update_communication(
    payload: CommunicationPreferencesUpdate,
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[CommunicationPreferencesResponse]:
    """Update communication preferences."""
    comm = await service.update_communication_preferences(payload)
    return APIResponse(
        success=True,
        data=CommunicationPreferencesResponse(**comm.model_dump()),
        request_id=get_request_id(),
    )


@router.patch("/locale", response_model=APIResponse[LocalePreferencesResponse])
async def update_locale(
    payload: LocalePreferencesUpdate,
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[LocalePreferencesResponse]:
    """Update regional and locale preferences."""
    loc = await service.update_locale_preferences(payload)
    return APIResponse(
        success=True,
        data=LocalePreferencesResponse(**loc.model_dump()),
        request_id=get_request_id(),
    )


@router.get("/completeness", response_model=APIResponse[ProfileCompletenessResponse])
async def get_completeness(
    service: IdentityService = Depends(get_identity_service),
) -> APIResponse[ProfileCompletenessResponse]:
    """Retrieve profile completeness metrics and missing recommended fields."""
    completeness = await service.calculate_completeness()
    return APIResponse(
        success=True,
        data=completeness,
        request_id=get_request_id(),
    )
