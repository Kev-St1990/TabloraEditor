"""Command protocol for undoable actions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol


class Command(Protocol):
    """Undoable command interface."""

    def execute(self) -> None: ...

    def undo(self) -> None: ...

    def redo(self) -> None: ...

    def description(self) -> str: ...


class SnapshotCommand(ABC):
    """Base class for commands that can restore full worksheet snapshots."""

    def __init__(self) -> None:
        self._before = None
        self._after = None

    def execute(self) -> None:
        """Capture the current state, apply the command, and cache the result."""
        self._before = self._capture_snapshot()
        self._apply()
        self._after = self._capture_snapshot()
        self._mark_dirty()

    def undo(self) -> None:
        """Restore the snapshot captured before execution."""
        if self._before is None:
            raise RuntimeError("Command has not been executed yet.")
        self._restore_snapshot(self._before)
        self._mark_dirty()

    def redo(self) -> None:
        """Restore the snapshot captured after execution."""
        if self._after is None:
            raise RuntimeError("Command has not been executed yet.")
        self._restore_snapshot(self._after)
        self._mark_dirty()

    @abstractmethod
    def description(self) -> str:
        """Return a human-readable command label."""

    @abstractmethod
    def _capture_snapshot(self):
        """Capture the current target state."""

    @abstractmethod
    def _restore_snapshot(self, snapshot) -> None:
        """Restore a previously captured snapshot."""

    @abstractmethod
    def _apply(self) -> None:
        """Apply the command to the target object."""

    def _mark_dirty(self) -> None:
        """Hook for subclasses to mark documents dirty."""
        return None
