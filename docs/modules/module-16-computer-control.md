# Module 16 — Computer Control

## 1. Purpose
Module 16 establishes a controlled, safe, platform-neutral bridge between Max's AI/security architecture and the user's actual operating system and desktop environment.

It provides structured primitives for:
- Screen capture and display detection
- Mouse pointer movement, clicking, dragging, and scrolling
- Keyboard key pressing, text typing, and shortcut execution
- Window enumeration, focus, minimization, maximization, restoration, movement, and resizing
- Controlled action sequencing, validation, execution, result normalization, and operational tracing

## 2. Architecture
The Computer Control module enforces a strict layered hierarchy:

```
Agent Engine (Module 13)
       ↓
Tool Registry (Module 14)
       ↓
Permission & Security (Module 15)
       ↓
Computer Control (Module 16)
       ↓
Operating System (Win32 / Backend API)
```

**Key Architectural Rule**: Direct access from agents to the backend/OS without passing through Module 15 `PermissionGate` is strictly prohibited.

## 3. Security Boundary
- **Core Principle**: Computer Control provides the *capability* to control the computer, but Module 15 decides *if an action is authorized*.
- **Authorization Context**: Every state-changing computer action (`MOVE_MOUSE`, `CLICK_MOUSE`, `TYPE_TEXT`, `PRESS_KEY`, `FOCUS_WINDOW`, `MOVE_WINDOW`) requires an active `AuthorizedExecutionRequest` or valid `permission_decision_id` from Module 15.
- **Revalidation**: Authorization expiry, action mismatches, target mismatches, security mode violations (`LOCKDOWN`), or active kill switches (`EMERGENCY_BLOCK`) cause execution to be immediately aborted without OS hardware mutation.

## 4. Supported Actions
Explicitly supported computer control primitives:
- `SCREEN_CAPTURE`
- `GET_SCREEN_INFO`
- `GET_CURSOR_POSITION`
- `MOVE_MOUSE`
- `CLICK_MOUSE`
- `DOUBLE_CLICK_MOUSE`
- `DRAG_MOUSE`
- `SCROLL_MOUSE`
- `PRESS_KEY`
- `TYPE_TEXT`
- `KEYBOARD_SHORTCUT`
- `GET_ACTIVE_WINDOW`
- `LIST_WINDOWS`
- `FOCUS_WINDOW`
- `MINIMIZE_WINDOW`
- `MAXIMIZE_WINDOW`
- `RESTORE_WINDOW`
- `MOVE_WINDOW`
- `RESIZE_WINDOW`

*Note: Unrestricted execution primitives such as `EXECUTE_ANYTHING` or `RAW_OS_COMMAND` are strictly forbidden.*

## 5. Screen Capture
- Supports full screen, specific monitor display ID, or rectangular `ScreenRegion(x, y, width, height)`.
- Operating policy: Captures are held in-memory; screenshots are **not** continuously recorded or saved to disk indefinitely.

## 6. Mouse Control
- Supports move, click (left/right/middle), double-click, click-and-drag, and scrolling (vertical/horizontal).
- Enforces strict parameter validation: non-negative coordinates, maximum click limits, and maximum movement durations.

## 7. Keyboard Control
- Supports single key press, typed text sequences, and modifier shortcut combinations (`ctrl`, `alt`, `shift`, `win`).
- Safeguards: typed text is subject to maximum length limits (`max_typed_text_length`), and sensitive text (passwords/secrets) is automatically redacted from logs and audit trace events.
- **Non-Surveillance Guarantee**: NO keylogging, NO background keystroke recording, and NO credential interception.

## 8. Window Control
- Supports window enumeration (`LIST_WINDOWS`), active window detection (`GET_ACTIVE_WINDOW`), window focusing (`FOCUS_WINDOW`), state controls (`MINIMIZE`, `MAXIMIZE`, `RESTORE`), and geometry adjustment (`MOVE_WINDOW`, `RESIZE_WINDOW`).

## 9. Multi-Monitor Support
- Multi-monitor systems are supported via `DisplayInfo` descriptors including display ID, dimensions, DPI scale factor, primary flag, orientation, and virtual desktop coordinates.

## 10. Backend Abstraction & Implementations
- `ComputerControlBackend`: Abstract interface for hardware desktop operations.
- `WindowsComputerControlBackend`: Windows 11 implementation utilizing standard Win32 `user32.dll` APIs via `ctypes`.
- `MockComputerControlBackend`: Thread-safe, deterministic mock implementation used for safe testing and default isolated operation.

## 11. Risk Classifications (Module 14 Tool Registry)
- `GET_SCREEN_INFO`, `GET_CURSOR_POSITION`, `GET_ACTIVE_WINDOW`, `SCROLL`, `MOVE_WINDOW`, `RESIZE_WINDOW`: **LOW**
- `SCREEN_CAPTURE`, `LIST_WINDOWS`, `MOVE_MOUSE`, `CLICK_MOUSE`, `DOUBLE_CLICK`, `FOCUS_WINDOW`, `PRESS_KEY`, `WINDOW_STATE`: **MEDIUM**
- `DRAG_MOUSE`, `TYPE_TEXT`, `KEYBOARD_SHORTCUT`: **HIGH**

## 12. Operational Tracing & Audit Log
Operational events (`ACTION_REQUESTED`, `ACTION_VALIDATED`, `PERMISSION_VERIFIED`, `ACTION_STARTED`, `ACTION_COMPLETED`, `ACTION_FAILED`, `ACTION_BLOCKED`, `ACTION_SIMULATED`, `SEQUENCE_STARTED`, `SEQUENCE_COMPLETED`) are recorded as immutable `ComputerTraceEvent` objects in `ComputerTraceRepository`.

## 13. REST API Endpoints
All endpoints are available under `/api/v1/computer`:
- `GET /status`, `GET /state`, `GET /displays`
- `GET /screen/info`, `POST /screen/capture`
- `GET /cursor`, `POST /cursor/move`
- `POST /mouse/click`, `POST /mouse/double-click`, `POST /mouse/drag`, `POST /mouse/scroll`
- `POST /keyboard/press`, `POST /keyboard/type`, `POST /keyboard/shortcut`
- `GET /windows`, `GET /windows/active`, `POST /windows/{id}/focus`, `POST /windows/{id}/minimize`, `POST /windows/{id}/maximize`, `POST /windows/{id}/restore`, `POST /windows/{id}/move`, `POST /windows/{id}/resize`
- `POST /actions`, `GET /actions`, `GET /actions/{id}`, `POST /actions/{id}/cancel`
- `POST /sequences`

## 14. Configuration
Key settings in `settings.py` (`ComputerControlSettings`):
- `MAX_COMPUTER_CONTROL_ENABLED`: Master flag (default `false`)
- `MAX_COMPUTER_CONTROL_DRY_RUN`: Dry run mode (default `true`)
- `MAX_COMPUTER_CONTROL_DEFAULT_TIMEOUT`: Action timeout seconds (default `30.0`)
- `MAX_COMPUTER_CONTROL_MAX_SEQUENCE_LENGTH`: Max sequence length (default `50`)
- `MAX_COMPUTER_CONTROL_MAX_CLICK_COUNT`: Max clicks per request (default `10`)
- `MAX_COMPUTER_CONTROL_MAX_TYPED_TEXT_LENGTH`: Max text length per request (default `1000`)

## 15. Manual Developer Smoke Test Procedure
1. Verify system status: `GET /api/v1/computer/status` -> `backend_available: true`.
2. Perform dry-run cursor move: `POST /api/v1/computer/cursor/move` with `{"x": 100, "y": 100}` -> status `SIMULATED`.
3. Query visible windows: `GET /api/v1/computer/windows`.
4. Test keyboard typing simulation: `POST /api/v1/computer/keyboard/type` with `{"text": "Test input"}` -> status `SIMULATED`.
5. For local hardware testing (optional): set `MAX_COMPUTER_CONTROL_ENABLED=true` and `MAX_COMPUTER_CONTROL_DRY_RUN=false` in environment with safe target windows. Disable when complete.
