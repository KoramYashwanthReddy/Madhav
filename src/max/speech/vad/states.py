"""VAD State Machine for tracking real-time continuous speech activity."""

from __future__ import annotations

import logging

from max.speech.domain.enums import SpeechActivityType

logger = logging.getLogger(__name__)


class VADStateMachine:
    """Manages VAD state transitions across continuous audio frames.

    States:
    - SILENCE
    - POSSIBLE_SPEECH
    - SPEECH
    - PAUSE
    - END_OF_SPEECH
    """

    def __init__(
        self,
        speech_threshold: float = 0.5,
        silence_threshold: float = 0.3,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 500,
    ) -> None:
        self.speech_threshold = speech_threshold
        self.silence_threshold = silence_threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms

        self.current_state = SpeechActivityType.SILENCE
        self.speech_start_time_ms: float | None = None
        self.accumulated_speech_ms: float = 0.0
        self.accumulated_silence_ms: float = 0.0

    def process_frame(
        self, frame_energy: float, frame_duration_ms: float, current_timestamp_ms: float
    ) -> SpeechActivityType:
        """Update VAD state machine with frame observations."""
        is_speech_frame = frame_energy >= self.speech_threshold
        is_silence_frame = frame_energy < self.silence_threshold

        if self.current_state == SpeechActivityType.SILENCE:
            if is_speech_frame:
                self.current_state = SpeechActivityType.POSSIBLE_SPEECH
                self.accumulated_speech_ms = frame_duration_ms
                self.speech_start_time_ms = current_timestamp_ms

        elif self.current_state == SpeechActivityType.POSSIBLE_SPEECH:
            if is_speech_frame:
                self.accumulated_speech_ms += frame_duration_ms
                if self.accumulated_speech_ms >= self.min_speech_duration_ms:
                    self.current_state = SpeechActivityType.SPEECH
            else:
                self.current_state = SpeechActivityType.SILENCE
                self.accumulated_speech_ms = 0.0
                self.speech_start_time_ms = None

        elif self.current_state == SpeechActivityType.SPEECH:
            if is_silence_frame:
                self.current_state = SpeechActivityType.PAUSE
                self.accumulated_silence_ms = frame_duration_ms
            else:
                self.accumulated_silence_ms = 0.0

        elif self.current_state == SpeechActivityType.PAUSE:
            if is_silence_frame:
                self.accumulated_silence_ms += frame_duration_ms
                if self.accumulated_silence_ms >= self.min_silence_duration_ms:
                    self.current_state = SpeechActivityType.END_OF_SPEECH
            else:
                self.current_state = SpeechActivityType.SPEECH
                self.accumulated_silence_ms = 0.0

        elif self.current_state == SpeechActivityType.END_OF_SPEECH:
            # Reset back to silence after reporting end of speech
            self.current_state = SpeechActivityType.SILENCE
            self.accumulated_speech_ms = 0.0
            self.accumulated_silence_ms = 0.0
            self.speech_start_time_ms = None

        return self.current_state

    def reset(self) -> None:
        """Reset VAD state machine to initial silence."""
        self.current_state = SpeechActivityType.SILENCE
        self.accumulated_speech_ms = 0.0
        self.accumulated_silence_ms = 0.0
        self.speech_start_time_ms = None
