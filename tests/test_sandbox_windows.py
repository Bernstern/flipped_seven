"""Tests for Windows platform detection in sandbox."""

import sys
from unittest.mock import patch

import pytest

from flip7.bots.sandbox import execute_with_sandbox


class TestSandboxWindowsCheck:
    """Tests for Windows platform compatibility in sandbox."""

    def test_linux_platform_works(self) -> None:
        """Test that sandbox works on Linux."""
        with patch.object(sys, 'platform', 'linux'):
            # Should execute successfully
            result = execute_with_sandbox(
                bot_name="TestBot",
                timeout_seconds=1.0,
                func=lambda: "success",
            )
            assert result == "success"

    def test_darwin_platform_works(self) -> None:
        """Test that sandbox works on macOS."""
        with patch.object(sys, 'platform', 'darwin'):
            # Should execute successfully
            result = execute_with_sandbox(
                bot_name="TestBot",
                timeout_seconds=1.0,
                func=lambda: "success",
            )
            assert result == "success"

    def test_windows_platform_raises_error(self) -> None:
        """Test that sandbox raises clear error on Windows."""
        with patch.object(sys, 'platform', 'win32'):
            with pytest.raises(RuntimeError) as exc_info:
                execute_with_sandbox(
                    bot_name="TestBot",
                    timeout_seconds=1.0,
                    func=lambda: "success",
                )
            error_msg = str(exc_info.value)
            assert "Windows" in error_msg
            assert "not supported" in error_msg
            assert "signal.SIGALRM" in error_msg

    def test_windows_error_suggests_solutions(self) -> None:
        """Test that Windows error message includes helpful solutions."""
        with patch.object(sys, 'platform', 'win32'):
            with pytest.raises(RuntimeError) as exc_info:
                execute_with_sandbox(
                    bot_name="TestBot",
                    timeout_seconds=1.0,
                    func=lambda: "success",
                )
            error_msg = str(exc_info.value)
            assert "WSL" in error_msg
            assert "Solutions:" in error_msg
            assert "Linux" in error_msg
