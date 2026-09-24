"""Repositories for Module 20 — Browser Agent.

Provides thread-safe in-memory repositories for sessions, tabs, and audit logs.
"""

from threading import RLock

from max.browser.domain.enums import BrowserTabStatus
from max.browser.domain.models import BrowserAuditEvent, BrowserSession, BrowserTab


class BrowserSessionRepository:
    """Thread-safe in-memory repository for BrowserSession state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, BrowserSession] = {}

    def save(self, session: BrowserSession) -> BrowserSession:
        with self._lock:
            self._sessions[session.session_id] = session
            return session

    def get(self, session_id: str) -> BrowserSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def list_all(self, owner_id: str | None = None, active_only: bool = False) -> list[BrowserSession]:
        with self._lock:
            results = list(self._sessions.values())
            if owner_id:
                results = [s for s in results if s.owner_id == owner_id]
            if active_only:
                results = [s for s in results if s.is_active]
            return results

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def count_active(self) -> int:
        with self._lock:
            return sum(1 for s in self._sessions.values() if s.is_active)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()


class BrowserTabRepository:
    """Thread-safe in-memory repository for BrowserTab state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._tabs: dict[str, dict[str, BrowserTab]] = {}  # session_id -> {tab_id -> BrowserTab}

    def save(self, tab: BrowserTab) -> BrowserTab:
        with self._lock:
            sess_tabs = self._tabs.setdefault(tab.session_id, {})
            sess_tabs[tab.tab_id] = tab
            return tab

    def get(self, session_id: str, tab_id: str) -> BrowserTab | None:
        with self._lock:
            return self._tabs.get(session_id, {}).get(tab_id)

    def list_tabs(self, session_id: str, active_only: bool = False) -> list[BrowserTab]:
        with self._lock:
            tabs_dict = self._tabs.get(session_id, {})
            results = list(tabs_dict.values())
            if active_only:
                results = [t for t in results if t.status != BrowserTabStatus.CLOSED]
            return results

    def get_active_tab(self, session_id: str) -> BrowserTab | None:
        with self._lock:
            tabs_dict = self._tabs.get(session_id, {})
            for t in tabs_dict.values():
                if t.is_active and t.status != BrowserTabStatus.CLOSED:
                    return t
            return None

    def delete(self, session_id: str, tab_id: str) -> bool:
        with self._lock:
            if session_id in self._tabs and tab_id in self._tabs[session_id]:
                del self._tabs[session_id][tab_id]
                return True
            return False

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._tabs:
                del self._tabs[session_id]

    def clear(self) -> None:
        with self._lock:
            self._tabs.clear()


class BrowserAuditRepository:
    """Append-only thread-safe audit trail for browser actions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._events: list[BrowserAuditEvent] = []

    def record(self, event: BrowserAuditEvent) -> BrowserAuditEvent:
        with self._lock:
            self._events.append(event)
            return event

    def list_events(
        self,
        session_id: str | None = None,
        tab_id: str | None = None,
        owner_id: str | None = None,
        limit: int = 100,
    ) -> list[BrowserAuditEvent]:
        with self._lock:
            results = list(self._events)
            if session_id:
                results = [e for e in results if e.session_id == session_id]
            if tab_id:
                results = [e for e in results if e.tab_id == tab_id]
            if owner_id:
                results = [e for e in results if e.owner_id == owner_id]

            results.sort(key=lambda e: e.timestamp, reverse=True)
            return results[:limit]

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
