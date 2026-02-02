"""Performance timing utilities for profiling game operations.

This module provides a context manager for measuring and tracking the duration
of operations, useful for performance analysis and optimization.
"""

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


class TimeTracker:
    """Context manager for tracking operation execution time.

    This class can be used as a context manager to measure how long
    an operation takes and optionally log the result.

    Attributes:
        operation_name: Descriptive name for the operation being timed
        elapsed_time: Time elapsed in seconds (None until operation completes)
        log_result: Whether to automatically log the timing result
        log_level: Logging level for automatic logging (default: DEBUG)

    Examples:
        >>> # Basic usage
        >>> with TimeTracker("deck_shuffle") as timer:
        ...     shuffle_deck()
        >>> print(f"Shuffle took {timer.elapsed_time:.3f}s")

        >>> # With automatic logging
        >>> with TimeTracker("score_calculation", log_result=True):
        ...     calculate_all_scores()
        [DEBUG] score_calculation completed in 0.042s

        >>> # Access elapsed time after completion
        >>> timer = TimeTracker("game_round")
        >>> with timer:
        ...     play_round()
        >>> if timer.elapsed_time > 1.0:
        ...     logger.warning(f"Round took {timer.elapsed_time:.3f}s")
    """

    def __init__(
        self,
        operation_name: str,
        log_result: bool = False,
        log_level: int = logging.DEBUG
    ) -> None:
        """Initialize the time tracker.

        Args:
            operation_name: Descriptive name for the operation being timed
            log_result: Whether to automatically log the timing result
            log_level: Logging level for automatic logging (default: DEBUG)
        """
        self.operation_name = operation_name
        self.log_result = log_result
        self.log_level = log_level
        self.elapsed_time: float | None = None
        self._start_time: float | None = None

    def __enter__(self) -> "TimeTracker":
        """Start timing when entering the context.

        Returns:
            Self for access to elapsed_time after completion
        """
        self._start_time = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any
    ) -> None:
        """Stop timing and optionally log the result when exiting the context.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self._start_time is not None:
            self.elapsed_time = time.perf_counter() - self._start_time

            if self.log_result:
                if exc_type is not None:
                    logger.log(
                        self.log_level,
                        f"{self.operation_name} failed after {self.elapsed_time:.3f}s"
                    )
                else:
                    logger.log(
                        self.log_level,
                        f"{self.operation_name} completed in {self.elapsed_time:.3f}s"
                    )


@contextmanager
def track_time(
    operation_name: str,
    log_result: bool = False,
    log_level: int = logging.DEBUG
) -> Generator[TimeTracker, None, None]:
    """Context manager function for tracking operation execution time.

    This is a convenience function that creates and yields a TimeTracker.
    Use this when you prefer a function-based context manager over a class.

    Args:
        operation_name: Descriptive name for the operation being timed
        log_result: Whether to automatically log the timing result
        log_level: Logging level for automatic logging (default: DEBUG)

    Yields:
        TimeTracker instance with elapsed_time available after operation completes

    Examples:
        >>> # Function-based usage
        >>> with track_time("tournament_execution", log_result=True, log_level=logging.INFO):
        ...     run_tournament()
        [INFO] tournament_execution completed in 12.456s

        >>> # Access elapsed time
        >>> with track_time("bot_decision") as timer:
        ...     decision = bot.decide_hit_or_pass(context)
        >>> print(f"Bot took {timer.elapsed_time * 1000:.1f}ms to decide")
    """
    tracker = TimeTracker(operation_name, log_result, log_level)
    with tracker:
        yield tracker
