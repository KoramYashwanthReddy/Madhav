"""Audio package for Module 26 — Speech System."""

from max.speech.audio.devices import (
    AudioDeviceRegistry,
    AudioInputDevice,
    AudioOutputDevice,
    MockAudioInputDevice,
    MockAudioOutputDevice,
)
from max.speech.audio.preprocessing import AudioPreprocessor, PreprocessedAudio
from max.speech.audio.streaming import AudioInputStream, AudioOutputStream
from max.speech.audio.validation import (
    AudioValidator,
    compute_audio_hash,
    detect_format_from_bytes,
    detect_format_from_extension,
)

__all__ = [
    "AudioDeviceRegistry",
    "AudioInputDevice",
    "AudioInputStream",
    "AudioOutputDevice",
    "AudioOutputStream",
    "AudioPreprocessor",
    "AudioValidator",
    "MockAudioInputDevice",
    "MockAudioOutputDevice",
    "PreprocessedAudio",
    "compute_audio_hash",
    "detect_format_from_bytes",
    "detect_format_from_extension",
]
