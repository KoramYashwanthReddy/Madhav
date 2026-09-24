"""In-memory repository for computer action sequences."""

import threading

from max.computer.domain.action import ComputerActionSequence


class ComputerSequenceRepository:
    """In-memory repository for computer action sequences."""

    def __init__(self) -> None:
        self._sequences: dict[str, ComputerActionSequence] = {}
        self._lock = threading.RLock()

    def save(self, sequence: ComputerActionSequence) -> ComputerActionSequence:
        """Save or update an action sequence."""
        with self._lock:
            self._sequences[sequence.sequence_id] = sequence
            return sequence

    def get_by_id(self, sequence_id: str) -> ComputerActionSequence | None:
        """Retrieve a sequence by ID."""
        with self._lock:
            return self._sequences.get(sequence_id)

    def list_sequences(self, limit: int = 50) -> list[ComputerActionSequence]:
        """List sequences ordered by creation time descending."""
        with self._lock:
            results = list(self._sequences.values())
            results.sort(key=lambda s: s.created_at, reverse=True)
            return results[:limit]

    def clear(self) -> None:
        """Clear all stored sequences."""
        with self._lock:
            self._sequences.clear()
