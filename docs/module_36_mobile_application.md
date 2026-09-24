# Module 36 — Mobile Application

## Overview
Module 36 implements the production-grade mobile application client for MAX. Built with React Native / TypeScript, it acts as a **CONTROLLED DEVICE INTERFACE** communicating with the Python backend API (Modules 01–35). The mobile client does not duplicate backend intelligence, AI reasoning, memory engines, RAG, or permission evaluation logic locally.

## Architecture

```
                         MAX CORE
                     Python Backend
                           │
                    Secure API Layer
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
        Desktop          Web           Mobile
       Module 34        Module 35      Module 36
                                            │
                                            ↓
                                      Mobile Agent
                                            │
                    ┌───────────────────────┼──────────────────────┐
                    ↓                       ↓                      ↓
                Android/iOS              Sensors              OS APIs
              capabilities             where allowed         where allowed
```

## Directory Structure (`mobile/`)
- `mobile/package.json`: Dependencies (React 18, Lucide React, TypeScript 5.7, Vite 6).
- `mobile/vite.config.ts`: Proxy configuration for backend communication (`/api/v1` -> `http://127.0.0.1:8000/api/v1`).
- `mobile/src/styles/index.css`: Mobile-native dark design system with safe areas, touch targets >= 44px, bottom nav styling, HSL color tokens.
- `mobile/src/types/index.ts`: TypeScript definitions matching backend DTOs, Mobile Action payloads, Device Info, Voice states, and Permission states.
- `mobile/src/services/`:
  - `SecureStorageService.ts`: Android Keystore / iOS Keychain backed secure token storage abstraction (tokens are never stored in unencrypted plain logs).
  - `DeviceCapabilityService.ts`: Mobile capability adapter with `isSupported()`, `getPermissionState()`, `requestPermission()`, `execute()`, and `getDeviceStatus()` for 12 mobile capabilities (`BATTERY_STATUS`, `NETWORK_STATUS`, `OPEN_APP`, `OPEN_URL`, `SHOW_NOTIFICATION`, `CALENDAR_READ`, `CALENDAR_WRITE`, `CONTACTS_READ`, `CONTACTS_WRITE`, `LOCATION`, `FILE_PICKER`, `CLIPBOARD`).
  - `MobileAgentService.ts`: Backend-controlled action executor enforcing 60s TTL action expiration, idempotency key deduplication, Module 15 security authorization verification, and Emergency Stop execution.
  - `VoiceService.ts`: Module 26 Speech System state machine (`IDLE` -> `LISTENING` -> `TRANSCRIBING` -> `THINKING` -> `SPEAKING` -> `STOPPED` -> `ERROR`).
- `mobile/src/api/client.ts`: Production Mobile REST API client with device registration and offline fallback.
- `mobile/src/context/MobileAppContext.tsx`: Global React Context managing navigation, connection modes (`LOCAL`, `REMOTE`, `OFFLINE`), telemetry, voice state, pending approvals, and emergency stop status.
- `mobile/src/components/`:
  - `MobileHeader.tsx`: Header displaying brand title, connection mode, battery/network telemetry, emergency stop button, and pending approval badge.
  - `BottomNavigation.tsx`: Bottom tab bar (`Home`, `Chat`, `Tasks`, `Alerts`, `More`).
  - `MoreDrawerModal.tsx`: Slide-up drawer listing remaining workspaces (`Voice`, `Memory`, `Knowledge`, `Automations`, `Activity`, `Integrations`, `Profile`, `Settings`, `Device`, `Help`).
  - `ApprovalModal.tsx`: Security authorization modal for Module 15 requests.
  - `EmergencyStopButton.tsx`: Floating emergency stop status banner to halt active actions.
- `mobile/src/views/`:
  1. `HomeView.tsx`: Mobile command center with greeting, backend readiness, battery/network metrics, and workspace shortcuts.
  2. `ChatView.tsx`: Mobile-first chat experience with streaming responses, tool execution steps, composer (text, voice, file picker, cancel), and citations.
  3. `VoiceView.tsx`: Speech System visualizer displaying real-time state machine, microphone permissions, and voice controls.
  4. `TasksView.tsx`: Task Engine workspace (Module 12) displaying step progress bars and task creation wizard.
  5. `AutomationsView.tsx`: Scheduler workspace (Module 28) displaying cron triggers and job toggles.
  6. `MemoryView.tsx`: Stored fact & preference search engine (Module 08) with importance ratings.
  7. `KnowledgeView.tsx`: Personal Knowledge graph visualizer (Module 09) showing node entities.
  8. `NotificationsView.tsx`: Proactive notification center (Module 27) with priority badges.
  9. `ActivityView.tsx`: User-safe audit log stream (Module 33).
  10. `IntegrationsView.tsx`: External connector status (Module 29).
  11. `ProfileView.tsx`: User identity profile view (Module 03).
  12. `SettingsView.tsx`: Autonomy policy selector (Levels 0–5), connection modes, and biometric lock.
  13. `DeviceView.tsx`: Registered device identity, OS version, and capability permission statuses.
  14. `HelpView.tsx`: Protocol version compatibility matrix and architectural boundaries.
- `mobile/src/tests/test_mobile_agent.test.ts`: Automated unit test suite verifying secure storage, Module 15 authorization boundary, 60s TTL action expiration, idempotency key deduplication, and Emergency Stop execution.

## Verification
- Mobile application compiled cleanly using `tsc && vite build` with 0 errors.
- All unit & security boundary tests passed.
