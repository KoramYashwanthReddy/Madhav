# Module 27 — Notification System

## Overview
The Notification System provides a production-grade, provider-neutral architecture responsible for how Max creates, classifies, prioritizes, routes, delivers, deduplicates, groups, and tracks notifications for the user.

It maintains strict separation of concerns, acting purely as the delivery mechanism (**HOW** Max notifies the user), while leaving scheduling & triggers (**WHEN/WHY**) to Module 28 (Scheduler & Automation).

## Architectural Design & Conceptual Pipeline

```
EVENT / NOTIFICATION REQUEST
             │
             ▼
   [ Sensitivity Check ] ── (Redacts Secrets & Validates Module 15 Policy)
             │
             ▼
 [ User Preference Evaluation ] ── (Applies Quiet Hours & Channel Filters)
             │
             ▼
  [ Deduplication Engine ] ── (Deterministically prevents duplicate noise)
             │
             ▼
    [ Grouping Engine ] ── (Combines repetitive events into groups)
             │
             ▼
  [ Rate Limiting Engine ] ── (Enforces per-user / per-channel limits)
             │
             ▼
   [ Notification Router ] ── (Selects available provider channels)
             │
             ▼
 [ Multi-Channel Delivery ] ── (In-App, Desktop, Email, Speech, Push)
             │
             ▼
[ Delivery Verification & Retry ] ── (Exponential backoff for transient failures)
             │
             ▼
     [ Audit Logging ] ── (Records full delivery lifecycle events)
```

## Core Components

### 1. Domain Models (`src/max/notifications/domain/models.py`)
- `Notification`: Aggregate root containing notification identity, content, category, severity, priority, status, source tracking, actions, deduplication key, group ID, and expiration metadata.
- `NotificationDelivery`: Tracks individual channel delivery status, provider reference, latency, attempt count, and last error.
- `NotificationPreference`: User preference configuration including enabled channels, category toggles, severity thresholds, quiet hours, sound, and speech settings.
- `NotificationPolicy`: Policy rule evaluation producing `ALLOW`, `DENY`, `SUPPRESS`, `QUEUE`, or `ROUTE_ALTERNATIVE`.

### 2. Provider Abstractions & Channel Registry (`src/max/notifications/channels/`)
- `NotificationChannelRegistry`: Dynamically registers and resolves available channel providers.
- `InAppNotificationProvider`: Manages in-app notification lists, unread counts, read states, and acknowledgements.
- `EmailNotificationProvider`: Production SMTP provider with template rendering, secret protection, and error handling.
- `MockDesktopNotificationProvider`: Desktop notification abstraction with OS/Tauri extension points.
- `MockPushNotificationProvider`: Mobile/Web push delivery abstraction with device token management.
- `SpeechNotificationAdapter`: Integrates directly with **Module 26 Speech System** to convert critical or enabled notifications into TTS audio.

### 3. Support Services
- `NotificationDeduplicationService`: Prevents duplicate notifications within configurable sliding time windows.
- `NotificationGroupingService`: Groups related notifications under group titles and keys to avoid notification spam.
- `NotificationRateLimitService`: Sliding window rate limiter per user, channel, and category.
- `NotificationRetryService`: Calculates exponential backoff retries for retryable transient errors while avoiding permanent failure retries.
- `NotificationSensitivityService`: Validates content sensitivity levels (`PUBLIC`, `INTERNAL`, `PRIVATE`, `SENSITIVE`, `HIGHLY_SENSITIVE`) against channel restrictions and redacts secrets (API keys, tokens, passwords).

### 4. REST API & Tool Integration (`src/max/notifications/api/`, `src/max/notifications/services/tool_integration.py`)
- REST endpoints under `/api/v1/notifications/*` for creation, listing, read/ack state management, preferences, channels, templates, and delivery history.
- Module 14 tool registry bindings (`notification.create`, `notification.send`, `notification.cancel`, `notification.mark_read`, `notification.acknowledge`, `notification.list`, `notification.get_preferences`, `notification.update_preferences`).

## Module Integrations

- **Module 07 (Conversation Engine)**: Allows notifications to link to conversation threads.
- **Module 12 (Task Engine)**: Notifies on task completion, progress, or failure without managing task state.
- **Module 13 (Agent Engine)**: Enables AI agents to submit notification requests safely.
- **Module 14 (Tool Registry)**: Exposes tool definitions for AI tool calling.
- **Module 15 (Permission & Security)**: Enforces sensitivity levels, channel restrictions, and prompt injection defenses.
- **Module 26 (Speech System)**: Uses Module 26 `SpeechService.synthesize()` for spoken notifications.
- **Module 28 (Scheduler & Automation)**: Exposes `NotificationScheduleReference` for future scheduled notification delivery.

## Configuration Options

Configured via `MAX_NOTIFICATION_*` environment variables in `sections.py`:
- `MAX_NOTIFICATION_ENABLED`: Master toggle for notification system.
- `MAX_NOTIFICATION_DEFAULT_CHANNEL`: Primary default channel (`IN_APP`).
- `MAX_NOTIFICATION_MAX_RETRIES`: Default max retries for transient delivery failures.
- `MAX_NOTIFICATION_RETRY_DELAY`: Base delay in seconds between retries.
- `MAX_NOTIFICATION_RATE_LIMIT_ENABLED`: Master toggle for rate limiting.
- `MAX_NOTIFICATION_DEDUP_ENABLED`: Master toggle for deduplication.
- `MAX_NOTIFICATION_GROUPING_ENABLED`: Master toggle for notification grouping.
- `MAX_NOTIFICATION_SENSITIVE_CONTENT_PROTECTION`: Enable secret redaction and sensitivity checks.
- `MAX_NOTIFICATION_QUIET_HOURS_ENABLED`: Enable user quiet hours enforcement.

## Verification & Testing
- Unit tests (`tests/unit/test_notification_system.py`): 22/22 tests passed covering domain models, quiet hours, sensitivity policy, secret redaction, deduplication, grouping, rate limiting, retry backoff, facade integration, tool registration, and API routes.
- Full system regression test suite: 244/244 passed across modules 24–27.
