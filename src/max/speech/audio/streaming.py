"""Audio streaming abstractions for Module 26 — Speech System.

Provides provider-neutral AudioInputStream and AudioOutputStream abstractions
supporting open, write, read, flush, close, and cooperative cancellation.
"""

from __future__ import annotations

import asyncio
import logging

from max.speech.domain.exceptions import SpeechCancelledError
from max.speech.domain.models import AudioChunk, AudioStreamConfiguration

logger = logging.getLogger(__name__)


class AudioInputStream:
    """Asynchronous input stream for incoming speech audio chunks."""

    def __init__(
        self, stream_id: str, config: AudioStreamConfiguration | None = None
    ) -> None:
        self.stream_id = stream_id
        self.config = config or AudioStreamConfiguration()
        self._queue: asyncio.Queue[AudioChunk | None] = asyncio.Queue()
        self._is_open = False
        self._is_cancelled = False

    async def open(self) -> None:
        """Open the audio input stream."""
        self._is_open = True
        self._is_cancelled = False
        logger.debug("AudioInputStream %s opened.", self.stream_id)

    async def write(self, chunk: AudioChunk) -> None:
        """Write an audio chunk to the stream."""
        if not self._is_open or self._is_cancelled:
            raise SpeechCancelledError(f"Stream {self.stream_id} is closed or cancelled.")
        await self._queue.put(chunk)

    async def read(self, timeout_seconds: float = 5.0) -> AudioChunk | None:
        """Read the next chunk from the stream."""
        if self._is_cancelled:
            raise SpeechCancelledError(f"Stream {self.stream_id} was cancelled.")

        try:
            chunk = await asyncio.wait_for(self._queue.get(), timeout=timeout_seconds)
            return chunk
        except asyncio.TimeoutError:
            return None

    async def flush(self) -> None:
        """Flush the input stream queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def close(self) -> None:
        """Mark end of input stream."""
        if self._is_open:
            self._is_open = False
            await self._queue.put(None)
            logger.debug("AudioInputStream %s closed.", self.stream_id)

    async def cancel(self) -> None:
        """Cooperatively cancel the stream."""
        self._is_cancelled = True
        self._is_open = False
        await self.flush()
        await self._queue.put(None)
        logger.debug("AudioInputStream %s cancelled.", self.stream_id)

    @property
    def is_open(self) -> bool:
        return self._is_open and not self._is_cancelled


class AudioOutputStream:
    """Asynchronous output stream for synthesized speech audio playback."""

    def __init__(
        self, stream_id: str, config: AudioStreamConfiguration | None = None
    ) -> None:
        self.stream_id = stream_id
        self.config = config or AudioStreamConfiguration()
        self._queue: asyncio.Queue[AudioChunk | None] = asyncio.Queue()
        self._is_open = False
        self._is_cancelled = False

    async def open(self) -> None:
        """Open output stream."""
        self._is_open = True
        self._is_cancelled = False
        logger.debug("AudioOutputStream %s opened.", self.stream_id)

    async def write(self, chunk: AudioChunk) -> None:
        """Enqueue audio chunk for playback."""
        if not self._is_open or self._is_cancelled:
            raise SpeechCancelledError(f"Stream {self.stream_id} is closed or cancelled.")
        await self._queue.put(chunk)

    async def read(self, timeout_seconds: float = 5.0) -> AudioChunk | None:
        """Consume next playback chunk."""
        if self._is_cancelled:
            raise SpeechCancelledError(f"Stream {self.stream_id} was cancelled.")

        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return None

    async def flush(self) -> None:
        """Flush unplayed audio chunks (for immediate barge-in)."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def close(self) -> None:
        """Close playback stream."""
        if self._is_open:
            self._is_open = False
            await self._queue.put(None)
            logger.debug("AudioOutputStream %s closed.", self.stream_id)

    async def cancel(self) -> None:
        """Cancel output stream immediately on interruption."""
        self._is_cancelled = True
        self._is_open = False
        await self.flush()
        await self._queue.put(None)
        logger.debug("AudioOutputStream %s cancelled for barge-in.", self.stream_id)

    @property
    def is_open(self) -> bool:
        return self._is_open and not self._is_cancelled
