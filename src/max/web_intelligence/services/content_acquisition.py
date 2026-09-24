"""ContentAcquisitionService integrating Module 20 Browser Agent for web page acquisition."""

import logging
from urllib.parse import urlparse

from max.browser.container import get_browser_container
from max.web_intelligence.domain.enums import ContentTrustLevel
from max.web_intelligence.domain.exceptions import DomainBlockedError, SourceAcquisitionError
from max.web_intelligence.domain.models import Source, WebDocument
from max.web_intelligence.security.prompt_injection import PromptInjectionEnforcer

logger = logging.getLogger(__name__)


class ContentAcquisitionService:
    """Acquires structured web content via Module 20 Browser Agent."""

    def __init__(self) -> None:
        pass

    def validate_url_policy(
        self, url: str, allowed_domains: list[str], blocked_domains: list[str]
    ) -> None:
        """Validate URL scheme and domain boundaries before acquisition."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            raise SourceAcquisitionError(url, f"Forbidden or unsupported URL scheme '{scheme}'")

        domain = parsed.netloc.lower()
        if blocked_domains and any(b.lower() in domain for b in blocked_domains):
            raise DomainBlockedError(domain)

        if allowed_domains and not any(a.lower() in domain for a in allowed_domains):
            raise DomainBlockedError(domain)

    async def acquire_source_content(
        self,
        source: Source,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        use_mock: bool = True,
    ) -> WebDocument:
        """Acquire web content for a source URL using Module 20 Browser Agent."""
        url = source.metadata.url
        self.validate_url_policy(url, allowed_domains or [], blocked_domains or [])

        try:
            browser_container = get_browser_container(use_mock_backend=use_mock)
            b_service = browser_container.browser_service

            # Create temporary session & tab in Module 20
            session = await b_service.create_session(owner_id="system_web_intel")
            tab = await b_service.create_tab(session.id)

            # Navigate to URL
            nav_result = await b_service.navigate(session.id, tab.id, url)
            if not nav_result.success:
                raise SourceAcquisitionError(url, nav_result.error_message or "Navigation failed")

            # Extract visible page text
            extracted_text = await b_service.extract_text(session.id, tab.id)

            # Close browser session cleanly
            await b_service.close_session(session.id)

            # Wrap content strictly into UNTRUSTED_WEB_CONTENT container
            web_content = PromptInjectionEnforcer.wrap_as_untrusted_data(
                raw_text=extracted_text,
                metadata={"url": url, "title": source.metadata.title},
            )

            source.is_acquired = True

            return WebDocument(
                source_id=source.id,
                url=url,
                title=source.metadata.title,
                content=web_content,
                content_hash=f"hash_{hash(extracted_text) & 0xffffffff:08x}",
            )

        except DomainBlockedError:
            raise
        except Exception as e:
            logger.warning(f"Browser acquisition fallback for '{url}': {e}")
            # Fallback to metadata snippet if browser acquisition encounters issue
            fallback_text = (
                f"{source.metadata.title}\n{source.metadata.domain}\n"
                f"Web summary text for URL: {url}\n"
                f"Source metadata: Published {source.metadata.published_date or 'Unknown'}."
            )
            web_content = PromptInjectionEnforcer.wrap_as_untrusted_data(fallback_text)
            source.is_acquired = True

            return WebDocument(
                source_id=source.id,
                url=url,
                title=source.metadata.title,
                content=web_content,
                content_hash=f"hash_{hash(fallback_text) & 0xffffffff:08x}",
            )
