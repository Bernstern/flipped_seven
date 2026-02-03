"""JSONL (JSON Lines) event logging for game events.

This module provides an EventLogger class that writes events to a JSONL file,
with context manager support for proper resource management and crash safety.
Also provides a NullEventLogger for performance-critical scenarios where logging
is not needed.
"""

from pathlib import Path
from typing import Any, TextIO

from flip7.types.events import Event
from flip7.events.event_serializer import serialize_event


class EventLogger:
    """Writes game events to a JSONL (JSON Lines) file.

    The EventLogger appends events to a log file, with each event on its own line.
    It supports context manager protocol for automatic file handling and ensures
    data is flushed after each write for crash safety.

    Example:
        >>> from pathlib import Path
        >>> log_path = Path("game_logs/game_123.jsonl")
        >>> with EventLogger(log_path) as logger:
        ...     logger.log_event(event1)
        ...     logger.log_event(event2)
        # File is automatically closed when exiting the context

    Attributes:
        log_path: Path to the JSONL log file
    """

    def __init__(self, log_path: Path) -> None:
        """Initialize the EventLogger with a target log file path.

        The log file and its parent directories will be created when entering
        the context manager (or when explicitly calling __enter__).

        Args:
            log_path: Path where the JSONL log file will be written
        """
        self.log_path = log_path
        self._file: TextIO | None = None

    def __enter__(self) -> "EventLogger":
        """Enter the context manager and open the log file for writing.

        Creates parent directories if they don't exist. Opens the file in
        append mode to preserve existing events if the file already exists.

        Returns:
            Self for use in with statements

        Raises:
            OSError: If the file or directories cannot be created
        """
        # Create parent directories if they don't exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file in append mode with explicit UTF-8 encoding
        self._file = self.log_path.open(mode='a', encoding='utf-8')

        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: Any | None) -> None:
        """Exit the context manager and close the log file.

        Ensures the file is properly closed even if an exception occurred.

        Args:
            exc_type: The exception type if an exception was raised
            exc_val: The exception instance if an exception was raised
            exc_tb: The exception traceback if an exception was raised
        """
        if self._file is not None:
            self._file.close()
            self._file = None

    def log_event(self, event: Event) -> None:
        """Append an event to the log file as a JSON line.

        Serializes the event to JSON and writes it to the file, followed by
        a newline. Flushes the file buffer immediately to ensure the event is
        persisted even if the program crashes.

        Args:
            event: The Event object to log

        Raises:
            RuntimeError: If called outside of a context manager
            OSError: If the file write operation fails

        Example:
            >>> with EventLogger(Path("game.jsonl")) as logger:
            ...     logger.log_event(event)
        """
        if self._file is None:
            raise RuntimeError(
                "EventLogger must be used as a context manager. "
                "Use 'with EventLogger(path) as logger:' syntax."
            )

        # Serialize event to JSON and write with newline
        json_str = serialize_event(event)
        self._file.write(json_str + '\n')

        # Flush immediately for crash safety
        self._file.flush()


class NullEventLogger:
    """A no-op event logger for performance-critical scenarios.

    This logger implements the same interface as EventLogger but discards
    all events without any I/O operations. Use this in tournaments or
    performance testing where event logging is not needed.

    Example:
        >>> logger = NullEventLogger()
        >>> with logger as log:
        ...     log.log_event(event)  # Does nothing
    """

    def __enter__(self) -> "NullEventLogger":
        """Enter context manager (no-op)."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: Any | None) -> None:
        """Exit context manager (no-op)."""
        pass

    def log_event(self, event: Event) -> None:
        """Discard event without logging (no-op)."""
        pass
