"""Atomic dual-index publication management."""
from typing import Sequence

from src.indexes.dense import DenseIndex
from src.indexes.lexical import LexicalIndex
from src.ingestion.state import DocumentState, document_key
from src.models import Chunk


class PublicationError(Exception):
    """Raised when staged publication fails."""


class Publisher:
    def __init__(self, lexical_index: LexicalIndex, dense_index: DenseIndex) -> None:
        self.lexical_index = lexical_index
        self.dense_index = dense_index
        self._states: dict[str, DocumentState] = {}
        self._active_version: str | None = None

    @property
    def active_version(self) -> str | None:
        return self._active_version

    def publish(self, states: Sequence[DocumentState], corpus_version: str) -> str:
        """Atomically stage and publish dual-index state.

        If any index publication fails, active_version is not updated and partial state
        is not exposed to queries.
        """
        if not corpus_version:
            raise ValueError("Corpus version cannot be empty")

        # Create proposed state map by applying updates/deletions onto current state
        proposed_states = dict(self._states)
        for state in states:
            key = document_key(state.record)
            if state.record.deleted:
                proposed_states.pop(key, None)
            else:
                proposed_states[key] = state

        # Collect active published chunks and vectors
        entries: list[tuple[Chunk, tuple[float, ...]]] = []
        for state in proposed_states.values():
            for chunk, vector in zip(state.chunks, state.vectors, strict=True):
                entries.append((chunk, vector))

        # Staged atomic dual-index publish
        try:
            self.lexical_index.publish_version(corpus_version, entries)
            self.dense_index.publish_version(corpus_version, entries)
        except Exception as exc:
            raise PublicationError(f"Staged publication failed for {corpus_version}") from exc

        # Success: update active state and published version
        self._states = proposed_states
        self._active_version = corpus_version
        return corpus_version
