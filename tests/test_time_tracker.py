"""Tests for time tracking utilities."""

import time

from flip7.utils.time_tracker import TimeTracker, track_time


class TestTimeTracker:
    """Tests for TimeTracker context manager."""

    def test_time_tracker_measures_elapsed_time(self) -> None:
        """Test that TimeTracker correctly measures elapsed time."""
        tracker = TimeTracker("test_operation")

        with tracker:
            time.sleep(0.01)  # Sleep for 10ms

        assert tracker.elapsed_time is not None
        assert tracker.elapsed_time >= 0.01
        assert tracker.elapsed_time < 0.1  # Should be well under 100ms

    def test_time_tracker_initially_none(self) -> None:
        """Test that elapsed_time is None before operation completes."""
        tracker = TimeTracker("test_operation")
        assert tracker.elapsed_time is None

    def test_time_tracker_on_exception(self) -> None:
        """Test that TimeTracker still records time on exception."""
        tracker = TimeTracker("test_operation")

        try:
            with tracker:
                time.sleep(0.01)
                raise ValueError("Test error")
        except ValueError:
            pass

        assert tracker.elapsed_time is not None
        assert tracker.elapsed_time >= 0.01

    def test_time_tracker_multiple_uses(self) -> None:
        """Test that TimeTracker can be reused."""
        tracker = TimeTracker("test_operation")

        with tracker:
            time.sleep(0.01)

        first_time = tracker.elapsed_time

        with tracker:
            time.sleep(0.02)

        second_time = tracker.elapsed_time

        assert first_time is not None
        assert second_time is not None
        assert second_time > first_time


class TestTrackTime:
    """Tests for track_time function."""

    def test_track_time_measures_elapsed(self) -> None:
        """Test that track_time correctly measures elapsed time."""
        with track_time("test_operation") as tracker:
            time.sleep(0.01)

        assert tracker.elapsed_time is not None
        assert tracker.elapsed_time >= 0.01

    def test_track_time_on_exception(self) -> None:
        """Test that track_time records time on exception."""
        try:
            with track_time("test_operation") as tracker:
                time.sleep(0.01)
                raise ValueError("Test error")
        except ValueError:
            pass

        assert tracker.elapsed_time is not None
        assert tracker.elapsed_time >= 0.01

    def test_track_time_zero_duration(self) -> None:
        """Test that track_time works with very short operations."""
        with track_time("instant_operation") as tracker:
            pass  # Do nothing

        assert tracker.elapsed_time is not None
        assert tracker.elapsed_time >= 0
