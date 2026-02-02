"""Tests for logging configuration."""

import logging
import tempfile
from pathlib import Path

from flip7.utils.logging_config import get_logger, setup_logging


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_basic(self) -> None:
        """Test basic logging setup."""
        setup_logging(level="INFO", use_rich=False)

        logger = logging.getLogger()
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logging_debug_level(self) -> None:
        """Test logging setup with DEBUG level."""
        setup_logging(level="DEBUG", use_rich=False)

        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self) -> None:
        """Test logging setup with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            setup_logging(level="INFO", use_rich=False, log_file=log_file)

            # Log a message
            logger = logging.getLogger("test")
            logger.info("Test message")

            # Verify file was created and contains message
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_setup_logging_creates_parent_dirs(self) -> None:
        """Test that setup_logging creates parent directories for log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "subdir" / "test.log"

            setup_logging(level="INFO", use_rich=False, log_file=log_file)

            # Log a message
            logger = logging.getLogger("test")
            logger.info("Test message")

            # Verify file and directories were created
            assert log_file.exists()
            assert log_file.parent.exists()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_same_instance(self) -> None:
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("same_logger")
        logger2 = get_logger("same_logger")
        assert logger1 is logger2
