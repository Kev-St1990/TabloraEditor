"""Undo and redo stack management."""

from dataclasses import dataclass, field

from csv_xlsx_editor.actions.command import Command


@dataclass(slots=True)
class UndoRedoManager:
    """Keeps undo and redo stacks for reversible commands."""

    undo_stack: list[Command] = field(default_factory=list)
    redo_stack: list[Command] = field(default_factory=list)

    def execute(self, command: Command) -> Command:
        """Execute a command, push it onto the undo stack, and clear redo."""
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
        return command

    def undo(self) -> bool:
        """Undo the most recent command if one exists."""
        if not self.undo_stack:
            return False
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True

    def redo(self) -> bool:
        """Redo the most recently undone command if one exists."""
        if not self.redo_stack:
            return False
        command = self.redo_stack.pop()
        command.redo()
        self.undo_stack.append(command)
        return True

    def clear(self) -> None:
        """Clear both command stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def can_undo(self) -> bool:
        """Return whether there is at least one command to undo."""
        return bool(self.undo_stack)

    def can_redo(self) -> bool:
        """Return whether there is at least one command to redo."""
        return bool(self.redo_stack)
