"""Enumerations for Module 26 — Speech System."""

from enum import Enum


class SpeechSessionStatus(str, Enum):
    """Lifecycle states of a Speech Session."""

    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    LISTENING = "LISTENING"
    SPEECH_DETECTED = "SPEECH_DETECTED"
    PROCESSING = "PROCESSING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    SYNTHESIZING = "SYNTHESIZING"
    PLAYING = "PLAYING"
    INTERRUPTED = "INTERRUPTED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class SpeechInputType(str, Enum):
    """Source categories for incoming speech audio input."""

    MICROPHONE = "MICROPHONE"
    AUDIO_FILE = "AUDIO_FILE"
    AUDIO_STREAM = "AUDIO_STREAM"
    BROWSER_AUDIO = "BROWSER_AUDIO"
    DESKTOP_AUDIO = "DESKTOP_AUDIO"
    MOBILE_AUDIO = "MOBILE_AUDIO"
    TEST_AUDIO = "TEST_AUDIO"


class AudioSourceType(str, Enum):
    """Audio source origin classifications."""

    MICROPHONE = "MICROPHONE"
    FILE = "FILE"
    STREAM = "STREAM"
    SYNTHETIC = "SYNTHETIC"


class AudioFormat(str, Enum):
    """Supported audio format codings & containers."""

    WAV = "WAV"
    PCM = "PCM"
    MP3 = "MP3"
    M4A = "M4A"
    OGG = "OGG"
    WEBM = "WEBM"
    FLAC = "FLAC"
    RAW = "RAW"
    UNKNOWN = "UNKNOWN"


class SpeechActivityType(str, Enum):
    """Voice activity detection states."""

    SILENCE = "SILENCE"
    POSSIBLE_SPEECH = "POSSIBLE_SPEECH"
    SPEECH = "SPEECH"
    PAUSE = "PAUSE"
    END_OF_SPEECH = "END_OF_SPEECH"


class SpeechProcessingStatus(str, Enum):
    """Status of STT / TTS processing tasks."""

    IDLE = "IDLE"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class InterruptionReason(str, Enum):
    """Triggers for speech interruption / barge-in."""

    USER_SPEECH = "USER_SPEECH"
    USER_STOP_COMMAND = "USER_STOP_COMMAND"
    SYSTEM_CANCEL = "SYSTEM_CANCEL"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class SpeechEventType(str, Enum):
    """Structured observable speech event types (NO raw audio in event payloads)."""

    SESSION_CREATED = "session_created"
    MICROPHONE_PERMISSION_REQUESTED = "microphone_permission_requested"
    MICROPHONE_PERMISSION_GRANTED = "microphone_permission_granted"
    MICROPHONE_PERMISSION_DENIED = "microphone_permission_denied"
    AUDIO_STARTED = "audio_started"
    SPEECH_DETECTED = "speech_detected"
    SPEECH_ENDED = "speech_ended"
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_PARTIAL = "transcription_partial"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    RESPONSE_STARTED = "response_started"
    TTS_STARTED = "tts_started"
    TTS_CHUNK_GENERATED = "tts_chunk_generated"
    TTS_COMPLETED = "tts_completed"
    SPEECH_INTERRUPTED = "speech_interrupted"
    SPEECH_CANCELLED = "speech_cancelled"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"


class TranscriptState(str, Enum):
    """Streaming transcript confidence & finality state."""

    PARTIAL = "PARTIAL"
    FINAL = "FINAL"
    CORRECTED = "CORRECTED"


class VoiceGender(str, Enum):
    """Voice gender attributes exposed by providers."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


class RawAudioRetention(str, Enum):
    """Privacy lifecycle for raw audio recordings."""

    TEMPORARY = "TEMPORARY"
    SESSION_ONLY = "SESSION_ONLY"
    PERSISTED = "PERSISTED"
    DELETED = "DELETED"
