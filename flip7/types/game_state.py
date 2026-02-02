"""
Game state type definitions for Flipped Seven.

This module defines the core data structures that represent the state of the game
at any point in time. All types are immutable frozen dataclasses to ensure state
transitions are explicit and traceable.
"""

from dataclasses import dataclass

from flip7.types.cards import Card, ModifierCard, NumberCard


@dataclass(frozen=True)
class PlayerTableau:
    """
    Represents a single player's cards and status during a round.

    The tableau tracks all cards a player has collected, along with their current
    state in the round (active, busted, frozen, passed).

    Attributes:
        player_id: Unique identifier for the player
        number_cards: Tuple of number cards (0-12) in the player's tableau
        modifier_cards: Tuple of modifier cards (+2, +4, +6, +8, +10, X2)
        second_chance: Whether the player currently holds a Second Chance card
        is_active: Whether the player can still take actions this round
        is_busted: Whether the player has busted (duplicate numbers)
        is_frozen: Whether the player has been frozen by a Freeze action
        is_passed: Whether the player has voluntarily passed this round
    """

    player_id: str
    number_cards: tuple[NumberCard, ...]
    modifier_cards: tuple[ModifierCard, ...]
    second_chance: bool
    is_active: bool
    is_busted: bool
    is_frozen: bool
    is_passed: bool


@dataclass(frozen=True)
class RoundState:
    """
    Represents the complete state of a single round.

    This captures all information needed to resume or replay a round, including
    the deck state, player tableaus, and turn order.

    Attributes:
        round_number: The current round number (1-indexed)
        tableaus: Map of player_id to their tableau state
        deck: Remaining cards in the draw pile (top card is at index 0)
        discard_pile: Cards that have been discarded (most recent on top)
        current_player_index: Index into player_order for the current turn
        player_order: Tuple of player IDs in turn order
    """

    round_number: int
    tableaus: dict[str, PlayerTableau]
    deck: tuple[Card, ...]
    discard_pile: tuple[Card, ...]
    current_player_index: int
    player_order: tuple[str, ...]


@dataclass(frozen=True)
class GameState:
    """
    Represents the complete state of a game across all rounds.

    This is the top-level state object that tracks cumulative scores and
    game completion status.

    Attributes:
        game_id: Unique identifier for this game instance
        players: Tuple of player IDs participating in the game
        scores: Map of player_id to their cumulative score across all rounds
        current_round: The current round number (0 if game hasn't started)
        is_complete: Whether the game has ended
        winner: The player_id of the winner, or None if game is not complete
    """

    game_id: str
    players: tuple[str, ...]
    scores: dict[str, int]
    current_round: int
    is_complete: bool
    winner: str | None


@dataclass(frozen=True)
class ScoreBreakdown:
    """
    Detailed breakdown of how a player's round score was calculated.

    This is primarily used for debugging, testing, and displaying score
    information to players or spectators.

    Attributes:
        number_cards_sum: Sum of all number card values
        after_x2_multiplier: Score after applying X2 modifier (if present)
        modifier_additions: Sum of all +N modifier bonuses
        flip_7_bonus: Bonus points for achieving exactly 7 unique numbers (0 or 15)
        final_score: The total score for the round
    """

    number_cards_sum: int
    after_x2_multiplier: int
    modifier_additions: int
    flip_7_bonus: int
    final_score: int
