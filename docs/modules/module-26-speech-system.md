# Module 26 — Speech System Architecture & Design Documentation

## Executive Summary
Module 26 introduces the **Speech System** to Max Personal AI. It provides a production-oriented, provider-neutral speech interface layer capable of audio capture, voice activity detection (VAD), audio validation, preprocessing, streaming/non-streaming speech-to-text (STT) transcription, transcript normalization, text-to-speech (TTS) synthesis, speech session management, and barge-in interruption handling.

The Speech System acts strictly as an interface layer (converting audio ↔ text). It does NOT make reasoning decisions, execute tools directly, or grant permissions. All spoken transcripts are marked as `UNTRUSTED_DATA` to defend against visual and spoken prompt injections.

---

## Architectural Principles & Conceptual Pipeline

### 1. Conceptual Audio Pipeline

```
MICROPHONE / AUDIO INPUT
          │
          ▼
    AUDIO CAPTURE & VALIDATION (Sample rate, channel, size, duration checks)
          │
          ▼
    VOICE ACTIVITY DETECTION (VAD) (Silence, possible speech, speech, pause, end of speech)
          │
          ▼
    AUDIO PREPROCESSING (Linear resampling, volume peak normalization)
          │
          ▼
    SPEECH-TO-TEXT (STT) (Mock, Local Whisper, Provider-neutral engines)
          │
          ▼
    TRANSCRIPT NORMALIZATION & SECURITY SHIELDING (Wrapped as UNTRUSTED_DATA)
          │
          ▼
    CONVERSATION ENGINE (Module 07) ──> AI RUNTIME (Module 04)
          │
          ▼
    TEXT-TO-SPEECH (TTS) SYNTHESIS (Mock, Local Piper, Provider-neutral voices)
          │
          ▼
    AUDIO STREAMING & SPEAKER PLAYBACK
```

### 2. Interruption / Barge-in Pipeline

```
SPEAKER PLAYBACK OUTPUT
          │
USER SPEECH DETECTED (VAD / Microphone input)
          │
          ▼
BARGE-IN TRIGGERED
          │
CANCEL TTS PLAYBACK STREAM
          │
TRANSITION SESSION STATE TO INTERRUPTED / LISTENING
```

---

## Core Directory Structure

```
src/max/speech/
├── __init__.py                     # Module entry point
├── container.py                    # DI container (SpeechContainer)
├── api/
│   ├── __init__.py
│   └── routes.py                   # FastAPI router (/api/v1/speech/*)
├── audio/
│   ├── __init__.py
│   ├── devices.py                  # AudioDeviceRegistry, microphone/speaker abstractions
│   ├── preprocessing.py            # Linear resampling & volume normalization
│   ├── streaming.py                # AudioInputStream, AudioOutputStream
│   └── validation.py               # Magic-byte format detection & limit validation
├── domain/
│   ├── __init__.py
│   ├── enums.py                    # SpeechSessionStatus, SpeechInputType, AudioFormat, etc.
│   ├── exceptions.py               # SpeechInputError, AudioPermissionError, etc.
│   └── models.py                   # SpeechSession, Transcript, SpeechSynthesisRequest, etc.
├── normalization/
│   ├── __init__.py
│   └── transcript_normalizer.py    # Whitespace cleanup & code-switching preservation
├── security/
│   ├── __init__.py
│   └── enforcer.py                 # PermissionGate integration, prompt injection shielding
├── services/
│   ├── __init__.py
│   ├── speech_service.py           # SpeechService facade orchestrator
│   └── tool_integration.py         # M14 ToolRegistry integration (5 tools)
├── sessions/
│   ├── __init__.py
│   └── manager.py                  # SpeechSessionManager & barge-in handler
├── stt/
│   ├── __init__.py
│   ├── base.py                     # SpeechToTextProvider interface
│   ├── local_stt.py                # Local Whisper-compatible adapter
│   ├── mock_stt.py                 # High-fidelity Mock STT provider
│   └── registry.py                 # STT Provider Registry
├── tts/
│   ├── __init__.py
│   ├── base.py                     # TextToSpeechProvider interface
│   ├── local_tts.py                # Local Piper-compatible adapter
│   ├── mock_tts.py                 # High-fidelity Mock TTS provider
│   └── registry.py                 # TTS Provider Registry
└── vad/
    ├── __init__.py
    ├── base.py                     # VoiceActivityDetector interface
    ├── mock_vad.py                 # Mock VAD provider
    └── states.py                   # VAD state machine
```

---

## Speech Session Lifecycle State Machine

A `SpeechSession` transitions through validated state machine boundaries:

- `CREATED` → `INITIALIZING` → `LISTENING` → `SPEECH_DETECTED` → `TRANSCRIBING` → `THINKING` → `SYNTHESIZING` → `PLAYING` → `COMPLETED`
- Interruption: `PLAYING` / `SYNTHESIZING` → `INTERRUPTED` → `LISTENING`
- Cooperative Cancellation: Any non-terminal state → `CANCELLED`
- Terminal States: `COMPLETED`, `CANCELLED`, `FAILED`

---

## Security & Defense Layer

1. **Microphone Authorization**: Integrates Module 15 `PermissionGate` checks (`MICROPHONE` permission required for `CAPTURE_AUDIO` or `LISTEN`).
2. **Prompt Injection Shielding**: Spoken transcripts are wrapped as `UNTRUSTED_DATA` (`is_untrusted_data=True`). Spoken phrases ("ignore all instructions", "system override") do not alter system instructions or grant permissions.
3. **Raw Audio Privacy**: Raw audio payloads are kept in memory only for immediate processing (`TEMPORARY` retention mode). Raw audio is never logged or permanently retained without explicit user policy consent.

---

## M14 Tool Registry Integration

Module 26 registers 5 controlled speech tools:
1. `speech.transcribe`: Transcribe spoken audio bytes to structured text.
2. `speech.synthesize`: Convert text into spoken audio stream.
3. `speech.detect_activity`: Analyze audio bytes for voice activity or silence.
4. `speech.list_voices`: List available TTS voice models.
5. `speech.list_devices`: Enumerate microphone and speaker hardware devices.

---

## Verification & Testing

- Unit test suite: `tests/unit/test_speech_system.py`
- Test Results: **36 / 36 PASSED** ✅
- Full Suite Regression (M24, M25, M26): **222 / 222 PASSED** ✅

```bash
python -m pytest tests/unit/test_speech_system.py -v --tb=short
```
