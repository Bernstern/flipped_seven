"""
Custom exception hierarchy for Flipped Seven game errors.

This module defines all game-specific exceptions that can be raised during
gameplay, configuration, and bot execution.
"""


class GameRuleViolation(Exception):
    """
    Raised when a game rule is violated during gameplay.

    This includes violations such as:
    - Playing cards in invalid order
    - Attempting to use cards not in hand
    - Invalid action card usage
    - Violating modifier placement rules
    """

    pass


class InvalidMove(Exception):
    """
    Raised when a player attempts an invalid move.

    This is distinct from GameRuleViolation in that it represents moves
    that are structurally invalid (e.g., malformed move data) rather than
    rule violations within valid move structures.
    """

    pass


class BotTimeout(Exception):
    """
    Raised when a bot exceeds its allocated time for making a decision.

    Bots must respond within the configured time limit. This exception
    is raised when a bot fails to return a move in time.
    """

    pass


class InvalidConfiguration(Exception):
    """
    Raised when game or tournament configuration is invalid.

    This includes errors such as:
    - Invalid number of players
    - Malformed configuration parameters
    - Conflicting configuration options
    - Missing required configuration values
    """

    pass
