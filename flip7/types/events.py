"""Event system types for Flip 7 game.

This module defines the event types and data structures used throughout the game
to track game state changes, player actions, and special card effects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

# Forward reference import - PlayerTableau will be defined in another module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flip7.types.game_state import PlayerTableau


# Event type literals for all possible game events
EventType = Literal[
    # Game lifecycle events
    "game_started",
    "round_started",
    "card_dealt",
    # Player action events
    "player_hit",
    "player_passed",
    "player_busted",
    # Special mechanic events
    "second_chance_used",
    "flip_7_achieved",
    # Action card events
    "action_card_drawn",
    "action_card_resolved",
    # Specific action card effects
    "freeze_applied",
    "flip_three_triggered",
    # End state events
    "round_ended",
    "game_ended",
]


@dataclass(frozen=True)
class Event:
    """Represents a single game event.

    Events are immutable records of state changes and actions that occur
    during gameplay. They can be used for game replay, analytics, debugging,
    and providing game history to bots.

    Attributes:
        event_type: The type of event that occurred
        timestamp: When the event occurred (UTC)
        game_id: Unique identifier for the game session
        round_number: The round in which this event occurred (None for game-level events)
        player_id: The player associated with this event (None for non-player events)
        data: Additional event-specific data (card values, scores, etc.)
    """

    event_type: EventType
    timestamp: datetime
    game_id: str
    round_number: int | None
    player_id: str | None
    data: dict[str, Any]


@dataclass(frozen=True)
class BotDecisionContext:
    """Context information provided to bots when making decisions.

    This provides all the information a bot needs to make informed decisions
    about hitting, passing, using Second Chance cards, or targeting action cards.
    Bots have perfect information about the game state.

    Attributes:
        my_tableau: The bot's current tableau (cards in play)
        opponent_tableaus: Dict mapping opponent player IDs to their tableaus
        deck_remaining: Number of cards remaining in the draw deck
        my_current_score: The bot's cumulative score across all rounds
        opponent_scores: Dict mapping opponent player IDs to their cumulative scores
        current_round: Which round number (1-indexed)
        target_score: Winning score (usually 200)
    """

    my_tableau: "PlayerTableau"
    opponent_tableaus: dict[str, "PlayerTableau"]
    deck_remaining: int
    my_current_score: int
    opponent_scores: dict[str, int]
    current_round: int
    target_score: int
