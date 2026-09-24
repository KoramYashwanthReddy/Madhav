"""Audio device abstraction and registry for Module 26 — Speech System.

Exposes AudioInputDevice, AudioOutputDevice, AudioDeviceRegistry,
and mock device implementations for continuous integration and unit testing.
"""

from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel, Field

from max.speech.domain.enums import AudioFormat
from max.speech.domain.exceptions import AudioDeviceError

logger = logging.getLogger(__name__)


class AudioInputDevice(BaseModel):
    """Microphone / Audio capture device representation."""

    device_id: str
    name: str
    is_default: bool = True
    channels: int = 1
    sample_rates: list[int] = Field(default_factory=lambda: [16000, 44100, 48000])
    is_available: bool = True
    driver: str = "mock"


class AudioOutputDevice(BaseModel):
    """Speaker / Audio playback device representation."""

    device_id: str
    name: str
    is_default: bool = True
    channels: int = 2
    sample_rates: list[int] = Field(default_factory=lambda: [22050, 44100, 48000])
    is_available: bool = True
    driver: str = "mock"


class MockAudioInputDevice:
    """Mock microphone device generating synthetic audio samples for tests."""

    def __init__(self, device_info: AudioInputDevice | None = None) -> None:
        self.info = device_info or AudioInputDevice(
            device_id="mock_mic_0", name="Mock System Microphone", is_default=True
        )
        self._is_capturing = False

    def start_capture(self) -> None:
        self._is_capturing = True

    def read_chunk(self, chunk_size_bytes: int = 4096) -> bytes:
        if not self._is_capturing:
            raise AudioDeviceError("Cannot read from stopped microphone.")
        # Generate 16-bit zero PCM samples (silence/mock audio)
        return b"\x00" * chunk_size_bytes

    def stop_capture(self) -> None:
        self._is_capturing = False


class MockAudioOutputDevice:
    """Mock speaker device consuming audio chunks for test playback."""

    def __init__(self, device_info: AudioOutputDevice | None = None) -> None:
        self.info = device_info or AudioOutputDevice(
            device_id="mock_speaker_0", name="Mock System Speaker", is_default=True
        )
        self._played_bytes = 0
        self._is_playing = False

    def start_playback(self) -> None:
        self._is_playing = True

    def write_chunk(self, data: bytes) -> None:
        if not self._is_playing:
            raise AudioDeviceError("Cannot write audio to stopped speaker device.")
        self._played_bytes += len(data)

    def stop_playback(self) -> None:
        self._is_playing = False

    def clear(self) -> None:
        self._played_bytes = 0


class AudioDeviceRegistry:
    """Registry enumerating system microphone and speaker devices."""

    def __init__(self) -> None:
        self._input_devices: dict[str, AudioInputDevice] = {
            "default_mic": AudioInputDevice(
                device_id="default_mic", name="Default Microphone", is_default=True
            ),
            "mock_mic": AudioInputDevice(
                device_id="mock_mic", name="Mock Test Microphone", is_default=False
            ),
        }
        self._output_devices: dict[str, AudioOutputDevice] = {
            "default_speaker": AudioOutputDevice(
                device_id="default_speaker", name="Default Speaker", is_default=True
            ),
            "mock_speaker": AudioOutputDevice(
                device_id="mock_speaker", name="Mock Test Speaker", is_default=False
            ),
        }

    def list_input_devices(self) -> list[AudioInputDevice]:
        """Return registered microphone input devices."""
        return list(self._input_devices.values())

    def list_output_devices(self) -> list[AudioOutputDevice]:
        """Return registered speaker output devices."""
        return list(self._output_devices.values())

    def get_default_input_device(self) -> AudioInputDevice:
        """Get the default input device."""
        for dev in self._input_devices.values():
            if dev.is_default:
                return dev
        return list(self._input_devices.values())[0]

    def get_default_output_device(self) -> AudioOutputDevice:
        """Get the default output device."""
        for dev in self._output_devices.values():
            if dev.is_default:
                return dev
        return list(self._output_devices.values())[0]
