"""
Multi-round game orchestration for Flipped Seven.

This module implements the GameEngine class which coordinates complete games from
start to finish, running rounds until a player reaches the WINNING_SCORE threshold.
The engine maintains game state across rounds, handles score accumulation, and
determines winners.

Example Usage:
    >>> from pathlib import Path
    >>> from flip7.core import GameEngine
    >>> from flip7.bots import RandomBot
    >>>
    >>> # Set up players and bots
    >>> player_ids = ['alice', 'bob', 'charlie']
    >>> bots = {
    ...     'alice': RandomBot('alice'),
    ...     'bob': RandomBot('bob'),
    ...     'charlie': RandomBot('charlie')
    ... }
    >>>
    >>> # Create game engine
    >>> engine = GameEngine(
    ...     game_id='game_001',
    ...     player_ids=player_ids,
    ...     bots=bots,
    ...     event_log_path=Path('./logs/game_001.jsonl'),
    ...     seed=42  # For deterministic gameplay
    ... )
    >>>
    >>> # Execute the complete game
    >>> final_state = engine.execute_game()
    >>>
    >>> # Check results
    >>> print(f"Winner: {final_state.winner}")
    >>> print(f"Final scores: {final_state.scores}")
    >>> print(f"Total rounds: {final_state.current_round}")
"""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from flip7.constants import WINNING_SCORE
from flip7.core.deck import create_deck, shuffle_deck
from flip7.core.round_engine import RoundEngine
from flip7.events.event_logger import EventLogger
from flip7.types.bot_interface import Bot
from flip7.types.cards import Card
from flip7.types.events import Event
from flip7.types.game_state import GameState


class GameEngine:
    """
    Orchestrates multi-round games until a player reaches WINNING_SCORE.

    The GameEngine is responsible for:
    - Initializing game state with zero scores
    - Running rounds sequentially using RoundEngine
    - Accumulating scores across rounds
    - Detecting when a player has reached the winning threshold
    - Determining the final winner (including tiebreaker logic)
    - Logging all game-level events

    Attributes:
        game_id: Unique identifier for this game instance
        player_ids: List of player IDs participating in the game
        bots: Dictionary mapping player IDs to their bot instances
        event_log_path: Path where game events will be logged
        seed: Random seed for deterministic gameplay (None for random)
        bot_timeout: Timeout in seconds for bot decisions
        game_state: Current state of the game (scores, completion status)
        deck: Persistent draw pile shared across all rounds
        discard_pile: Persistent discard pile shared across all rounds
    """

    def __init__(
        self,
        game_id: str,
        player_ids: list[str],
        bots: dict[str, Bot],
        event_log_path: Path,
        seed: int | None = None,
        bot_timeout: float = 5.0
    ) -> None:
        """
        Initialize the game engine.

        Args:
            game_id: Unique identifier for this game
            player_ids: List of player IDs participating
            bots: Dictionary mapping player IDs to bot instances
            event_log_path: Path to event log file
            seed: Optional random seed for deterministic gameplay
            bot_timeout: Timeout in seconds for bot decisions (default: 5.0)

        Raises:
            ValueError: If player_ids is empty or if bots dict doesn't contain
                       all player IDs
        """
        if not player_ids:
            raise ValueError("player_ids cannot be empty")

        if not all(pid in bots for pid in player_ids):
            raise ValueError("bots dictionary must contain all player IDs")

        self.game_id = game_id
        self.player_ids = player_ids
        self.bots = bots
        self.event_log_path = event_log_path
        self.seed = seed
        self.bot_timeout = bot_timeout

        # Initialize persistent deck and discard pile (shared across all rounds)
        self.deck: list[Card] = shuffle_deck(create_deck(), seed=seed)
        self.discard_pile: list[Card] = []

        # Initialize game state
        self.game_state = self._initialize_game_state()

    def _initialize_game_state(self) -> GameState:
        """
        Create initial game state with zero scores for all players.

        Returns:
            GameState with all scores at 0, round 0, not complete
        """
        return GameState(
            game_id=self.game_id,
            players=tuple(self.player_ids),
            scores={player_id: 0 for player_id in self.player_ids},
            current_round=0,
            is_complete=False,
            winner=None
        )

    def _execute_round(self, round_num: int, event_logger: EventLogger) -> dict[str, int]:
        """
        Execute a single round using RoundEngine.

        Args:
            round_num: The round number (1-indexed)
            event_logger: EventLogger instance for this round

        Returns:
            Dictionary mapping player IDs to their scores for this round
        """
        # Create RoundEngine with appropriate seed
        # Each round gets a different seed derived from the base seed
        round_seed = None if self.seed is None else self.seed + round_num

        round_engine = RoundEngine(
            player_ids=self.player_ids,
            bots=self.bots,
            event_logger=event_logger,
            deck=self.deck,
            discard_pile=self.discard_pile,
            round_number=round_num,
            game_id=self.game_id,
            seed=round_seed,
            bot_timeout=self.bot_timeout
        )

        # Execute the round and return scores
        return round_engine.execute_round()

    def _update_scores(self, round_scores: dict[str, int]) -> dict[str, int]:
        """
        Accumulate round scores into cumulative totals.

        Args:
            round_scores: Scores earned by each player this round

        Returns:
            Updated cumulative scores for all players
        """
        new_scores = {}
        for player_id in self.player_ids:
            current_score = self.game_state.scores[player_id]
            round_score = round_scores.get(player_id, 0)
            new_scores[player_id] = current_score + round_score

        return new_scores

    def _check_winner(self) -> str | None:
        """
        Check if there is a unique winner at or above WINNING_SCORE.

        Per game rules, if multiple players are tied at 200+, the game continues
        until one player has a higher score at the end of a round.

        Returns:
            Player ID if there is a unique highest score >= WINNING_SCORE, None otherwise
        """
        # Find all players at or above WINNING_SCORE
        qualified_players = [
            (player_id, score)
            for player_id, score in self.game_state.scores.items()
            if score >= WINNING_SCORE
        ]

        # No one has reached WINNING_SCORE yet
        if not qualified_players:
            return None

        # Find the highest score among qualified players
        max_score = max(score for _, score in qualified_players)

        # Count how many players have the highest score
        players_with_max_score = [
            player_id for player_id, score in qualified_players
            if score == max_score
        ]

        # Only return a winner if there's exactly one player with the highest score
        if len(players_with_max_score) == 1:
            return players_with_max_score[0]

        # Multiple players tied at the highest score - continue playing
        return None

    def _determine_winner(self) -> str:
        """
        Determine the winner from current scores (handles ties).

        In case of a tie at WINNING_SCORE or above, the player with the
        highest total score wins. This should only be called when at least
        one player has reached WINNING_SCORE.

        Returns:
            Player ID of the winner (player with highest score)

        Raises:
            ValueError: If no player has reached WINNING_SCORE
        """
        # Find all players who have reached WINNING_SCORE
        qualified_players = [
            (player_id, score)
            for player_id, score in self.game_state.scores.items()
            if score >= WINNING_SCORE
        ]

        if not qualified_players:
            raise ValueError(
                "Cannot determine winner: no player has reached WINNING_SCORE"
            )

        # Return the player with the highest score
        winner_id, _ = max(qualified_players, key=lambda x: x[1])
        return winner_id

    def execute_game(self) -> GameState:
        """
        Run a complete game until a player reaches WINNING_SCORE.

        This method:
        1. Logs game_started event
        2. Executes rounds sequentially until a winner is determined
        3. For each round:
           - Logs round_started event
           - Executes the round using RoundEngine
           - Updates cumulative scores
           - Logs round_ended event with updated scores
           - Checks for a winner
        4. Logs game_ended event with final results
        5. Returns the final GameState

        Returns:
            Final GameState with is_complete=True and winner set

        Raises:
            RuntimeError: If game has already been completed
        """
        if self.game_state.is_complete:
            raise RuntimeError("Game has already been completed")

        # Use EventLogger as context manager for proper resource management
        with EventLogger(self.event_log_path) as event_logger:
            # Log game started event
            self._log_game_started(event_logger)

            round_num = 1

            # Keep playing rounds until we have a winner
            while True:
                # Log round started
                self._log_round_started(round_num, event_logger)

                # Execute the round
                round_scores = self._execute_round(round_num, event_logger)

                # Update cumulative scores
                new_scores = self._update_scores(round_scores)

                # Update game state with new round number and scores
                self.game_state = replace(
                    self.game_state,
                    current_round=round_num,
                    scores=new_scores
                )

                # Log round ended
                self._log_round_ended(round_num, round_scores, event_logger)

                # Check if anyone has reached WINNING_SCORE
                if self._check_winner() is not None:
                    # Determine the final winner (handles ties)
                    winner = self._determine_winner()

                    # Update game state to mark completion
                    self.game_state = replace(
                        self.game_state,
                        is_complete=True,
                        winner=winner
                    )

                    # Log game ended
                    self._log_game_ended(event_logger)

                    return self.game_state

                # Continue to next round
                round_num += 1

    def _log_game_started(self, event_logger: EventLogger) -> None:
        """
        Log the game_started event.

        Args:
            event_logger: EventLogger instance to use for logging
        """
        event = Event(
            event_type="game_started",
            timestamp=datetime.now(timezone.utc),
            game_id=self.game_id,
            round_number=None,
            player_id=None,
            data={
                "players": self.player_ids,
                "seed": self.seed
            }
        )
        event_logger.log_event(event)

    def _log_round_started(self, round_num: int, event_logger: EventLogger) -> None:
        """
        Log the round_started event.

        Args:
            round_num: The round number being started
            event_logger: EventLogger instance to use for logging
        """
        event = Event(
            event_type="round_started",
            timestamp=datetime.now(timezone.utc),
            game_id=self.game_id,
            round_number=round_num,
            player_id=None,
            data={
                "cumulative_scores": self.game_state.scores
            }
        )
        event_logger.log_event(event)

    def _log_round_ended(
        self, round_num: int, round_scores: dict[str, int], event_logger: EventLogger
    ) -> None:
        """
        Log the round_ended event.

        Args:
            round_num: The round number that ended
            round_scores: Scores earned by each player this round
            event_logger: EventLogger instance to use for logging
        """
        event = Event(
            event_type="round_ended",
            timestamp=datetime.now(timezone.utc),
            game_id=self.game_id,
            round_number=round_num,
            player_id=None,
            data={
                "round_scores": round_scores,
                "cumulative_scores": self.game_state.scores
            }
        )
        event_logger.log_event(event)

    def _log_game_ended(self, event_logger: EventLogger) -> None:
        """
        Log the game_ended event with final results.

        Args:
            event_logger: EventLogger instance to use for logging
        """
        event = Event(
            event_type="game_ended",
            timestamp=datetime.now(timezone.utc),
            game_id=self.game_id,
            round_number=None,
            player_id=None,
            data={
                "winner": self.game_state.winner,
                "final_scores": self.game_state.scores,
                "total_rounds": self.game_state.current_round
            }
        )
        event_logger.log_event(event)
