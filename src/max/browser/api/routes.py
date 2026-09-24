"""FastAPI API routes for Module 20 — Browser Agent."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from max.browser.container import BrowserContainer, get_browser_container
from max.browser.domain.exceptions import (
    BrowserDomainBlockedError,
    BrowserElementNotFoundError,
    BrowserError,
    BrowserNavigationBlockedError,
    BrowserPermissionDeniedError,
    BrowserSessionNotFoundError,
    BrowserTabNotFoundError,
)
from max.browser.domain.models import (
    BrowserClickRequest,
    BrowserClickResult,
    BrowserExtractResult,
    BrowserNavigationResult,
    BrowserObservation,
    BrowserScreenshotResult,
    BrowserScrollRequest,
    BrowserScrollResult,
    BrowserSelectRequest,
    BrowserSelectResult,
    BrowserSession,
    BrowserTab,
    BrowserTypeRequest,
    BrowserTypeResult,
    BrowserWaitRequest,
    BrowserWaitResult,
)
from max.browser.services.browser_service import BrowserService

router = APIRouter(prefix="/browser", tags=["Browser Agent"])


def get_service(
    container: BrowserContainer = Depends(get_browser_container),
) -> BrowserService:
    """Dependency injection helper for BrowserService."""
    return container.browser_service


@router.get("/health", status_code=status.HTTP_200_OK)
async def get_browser_health(
    container: BrowserContainer = Depends(get_browser_container),
) -> dict[str, Any]:
    """Expose browser subsystem health without spawning browser processes unnecessarily."""
    sessions = container.session_repo.list_all()
    active_count = sum(1 for s in sessions if s.is_active)
    playwright_available = False
    try:
        import playwright  # noqa: F401
        playwright_available = True
    except ImportError:
        playwright_available = False

    return {
        "status": "healthy",
        "backend": type(container.backend).__name__,
        "playwright_available": playwright_available,
        "configured_browser": container.settings.default_browser,
        "active_sessions": active_count,
        "enabled": container.settings.enabled,
    }


@router.post("/sessions", response_model=BrowserSession, status_code=status.HTTP_201_CREATED)
async def create_session(
    owner_id: str = "system",
    service: BrowserService = Depends(get_service),
) -> BrowserSession:
    """Create a new isolated browser session."""
    try:
        return await service.create_session(owner_id=owner_id)
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/sessions", response_model=list[BrowserSession])
async def list_sessions(
    owner_id: str | None = None,
    service: BrowserService = Depends(get_service),
) -> list[BrowserSession]:
    """List browser sessions filtered by owner."""
    return service.session_repo.list_all(owner_id=owner_id)


@router.get("/sessions/{session_id}", response_model=BrowserSession)
async def get_session(
    session_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserSession:
    """Get browser session details by session ID."""
    sess = service.session_repo.get(session_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Browser session '{session_id}' not found.",
        )
    return sess


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_session(
    session_id: str,
    service: BrowserService = Depends(get_service),
) -> None:
    """Close a browser session."""
    try:
        await service.close_session(session_id)
    except BrowserSessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Browser session '{session_id}' not found.",
        )


@router.get("/sessions/{session_id}/tabs", response_model=list[BrowserTab])
async def list_tabs(
    session_id: str,
    service: BrowserService = Depends(get_service),
) -> list[BrowserTab]:
    """List tabs in a session."""
    try:
        return await service.list_tabs(session_id)
    except BrowserSessionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")


@router.post("/sessions/{session_id}/tabs", response_model=BrowserTab, status_code=status.HTTP_201_CREATED)
async def create_tab(
    session_id: str,
    url: str = "about:blank",
    service: BrowserService = Depends(get_service),
) -> BrowserTab:
    """Create a new tab in a session."""
    try:
        return await service.create_tab(session_id, url=url)
    except BrowserSessionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/sessions/{session_id}/tabs/{tab_id}", response_model=BrowserTab)
async def get_tab(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserTab:
    """Get tab details."""
    tab = service.tab_repo.get(session_id, tab_id)
    if not tab:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tab not found")
    return tab


@router.post("/sessions/{session_id}/tabs/{tab_id}/activate", response_model=BrowserTab)
async def switch_tab(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserTab:
    """Switch active tab in a session."""
    try:
        return await service.switch_tab(session_id, tab_id)
    except (BrowserSessionNotFoundError, BrowserTabNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/sessions/{session_id}/tabs/{tab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_tab(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> None:
    """Close a tab in a session."""
    try:
        await service.close_tab(session_id, tab_id)
    except (BrowserSessionNotFoundError, BrowserTabNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/navigate", response_model=BrowserNavigationResult)
async def navigate(
    session_id: str,
    tab_id: str,
    url: str,
    service: BrowserService = Depends(get_service),
) -> BrowserNavigationResult:
    """Navigate tab to target URL with security validation."""
    try:
        return await service.navigate(session_id=session_id, url=url, tab_id=tab_id)
    except (BrowserNavigationBlockedError, BrowserDomainBlockedError, BrowserPermissionDeniedError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except (BrowserSessionNotFoundError, BrowserTabNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/back", response_model=BrowserNavigationResult)
async def go_back(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserNavigationResult:
    """Navigate tab back in history."""
    try:
        return await service.go_back(session_id, tab_id)
    except (BrowserSessionNotFoundError, BrowserTabNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/forward", response_model=BrowserNavigationResult)
async def go_forward(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserNavigationResult:
    """Navigate tab forward in history."""
    try:
        return await service.go_forward(session_id, tab_id)
    except (BrowserSessionNotFoundError, BrowserTabNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/reload", response_model=BrowserNavigationResult)
async def reload(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserNavigationResult:
    """Reload active page in tab."""
    try:
        return await service.reload(session_id, tab_id)
    except (BrowserSessionNotFoundError, BrowserTabNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/observe", response_model=BrowserObservation)
async def observe_page(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserObservation:
    """Observe active page and return bounded structured observation."""
    try:
        return await service.observe_page(session_id, tab_id)
    except (BrowserSessionNotFoundError, BrowserTabNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/click", response_model=BrowserClickResult)
async def click(
    session_id: str,
    tab_id: str,
    request: BrowserClickRequest,
    service: BrowserService = Depends(get_service),
) -> BrowserClickResult:
    """Click an interactive element on the page."""
    try:
        return await service.click(
            session_id=session_id,
            locator=request.locator,
            tab_id=tab_id,
        )
    except BrowserElementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BrowserPermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/type", response_model=BrowserTypeResult)
async def type_text(
    session_id: str,
    tab_id: str,
    request: BrowserTypeRequest,
    service: BrowserService = Depends(get_service),
) -> BrowserTypeResult:
    """Type text into an input field on the page."""
    try:
        return await service.type_text(
            session_id=session_id,
            locator=request.locator,
            text=request.text,
            clear_first=request.clear_first,
            tab_id=tab_id,
            is_sensitive=request.is_sensitive,
        )
    except BrowserElementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BrowserPermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/select", response_model=BrowserSelectResult)
async def select_option(
    session_id: str,
    tab_id: str,
    request: BrowserSelectRequest,
    service: BrowserService = Depends(get_service),
) -> BrowserSelectResult:
    """Select option from a dropdown element."""
    try:
        return await service.select_option(
            session_id=session_id,
            locator=request.locator,
            value=request.value,
            tab_id=tab_id,
        )
    except BrowserElementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/scroll", response_model=BrowserScrollResult)
async def scroll(
    session_id: str,
    tab_id: str,
    request: BrowserScrollRequest,
    service: BrowserService = Depends(get_service),
) -> BrowserScrollResult:
    """Scroll the active page."""
    try:
        return await service.scroll(
            session_id=session_id,
            direction=request.direction,
            amount_pixels=request.amount_pixels,
            tab_id=tab_id,
        )
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/wait", response_model=BrowserWaitResult)
async def wait_for_condition(
    session_id: str,
    tab_id: str,
    request: BrowserWaitRequest,
    service: BrowserService = Depends(get_service),
) -> BrowserWaitResult:
    """Wait for element or load condition."""
    try:
        return await service.wait_for_condition(
            session_id=session_id,
            condition=request.condition,
            locator=request.locator,
            expected_url=request.expected_url,
            timeout=request.timeout,
            tab_id=tab_id,
        )
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/screenshot", response_model=BrowserScreenshotResult)
async def take_screenshot(
    session_id: str,
    tab_id: str,
    full_page: bool = False,
    service: BrowserService = Depends(get_service),
) -> BrowserScreenshotResult:
    """Capture page screenshot."""
    try:
        return await service.take_screenshot(session_id=session_id, full_page=full_page, tab_id=tab_id)
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/extract/text", response_model=BrowserExtractResult)
async def extract_text(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserExtractResult:
    """Extract visible text content from page."""
    try:
        return await service.extract_content(session_id=session_id, target="text", tab_id=tab_id)
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/extract/links", response_model=BrowserExtractResult)
async def extract_links(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserExtractResult:
    """Extract links from active page."""
    try:
        return await service.extract_content(session_id=session_id, target="links", tab_id=tab_id)
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/extract/forms", response_model=BrowserExtractResult)
async def extract_forms(
    session_id: str,
    tab_id: str,
    service: BrowserService = Depends(get_service),
) -> BrowserExtractResult:
    """Extract forms from active page."""
    try:
        return await service.extract_content(session_id=session_id, target="forms", tab_id=tab_id)
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/download")
async def download_file(
    session_id: str,
    tab_id: str,
    url: str,
    destination_path: str,
    service: BrowserService = Depends(get_service),
) -> dict[str, Any]:
    """Download a file from the page with path validation."""
    try:
        dl = await service.download_file(
            session_id=session_id,
            tab_id=tab_id,
            url=url,
            target_path=destination_path,
        )
        return {"status": "success", "download": dl.model_dump(mode="json")}
    except (BrowserPermissionDeniedError, BrowserDomainBlockedError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/sessions/{session_id}/tabs/{tab_id}/upload")
async def upload_file(
    session_id: str,
    tab_id: str,
    selector: str,
    file_path: str,
    service: BrowserService = Depends(get_service),
) -> dict[str, Any]:
    """Upload a file with path and permission validation."""
    try:
        from max.browser.domain.models import BrowserElementLocator
        locator = BrowserElementLocator(css=selector)
        ul = await service.upload_file(
            session_id=session_id,
            tab_id=tab_id,
            locator=locator,
            file_path=file_path,
        )
        return {"status": "success", "upload": ul.model_dump(mode="json")}
    except (BrowserPermissionDeniedError, BrowserDomainBlockedError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except BrowserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
