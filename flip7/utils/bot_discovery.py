"""Automatic bot discovery utility.

Scans the flip7/bots directory and automatically imports all bot classes
that inherit from BaseBot.
"""

import importlib
import inspect
from pathlib import Path
from typing import Type

from flip7.bots.base import BaseBot


def discover_all_bots() -> list[Type[BaseBot]]:
    """Discover all bot classes in flip7/bots directory.

    Automatically finds and imports all classes that inherit from BaseBot.
    Excludes the BaseBot class itself and any abstract classes.

    Returns:
        List of bot classes found in the bots directory
    """
    bots: list[Type[BaseBot]] = []

    # Get the bots directory path
    bots_dir = Path(__file__).parent.parent / "bots"

    # Find all Python files in the bots directory
    for py_file in bots_dir.glob("*.py"):
        # Skip __init__.py, base.py, and sandbox.py
        if py_file.name in ("__init__.py", "base.py", "sandbox.py"):
            continue

        # Import the module
        module_name = f"flip7.bots.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)

            # Find all classes in the module that inherit from BaseBot
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of BaseBot (but not BaseBot itself)
                if (
                    issubclass(obj, BaseBot)
                    and obj is not BaseBot
                    and not inspect.isabstract(obj)
                    and obj.__module__ == module_name  # Defined in this module
                ):
                    bots.append(obj)

        except Exception as e:
            # Skip modules that fail to import
            print(f"Warning: Could not import {module_name}: {e}")
            continue

    return bots


def get_bot_names(bots: list[Type[BaseBot]]) -> list[str]:
    """Get list of bot class names.

    Args:
        bots: List of bot classes

    Returns:
        List of bot class names
    """
    return [bot.__name__ for bot in bots]
