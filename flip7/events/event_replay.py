"""Event replay engine for reconstructing game state from event logs.

This module provides utilities to load events from JSONL files and replay them
to reconstruct the final game state. This is useful for debugging, analytics,
and game history visualization.
"""

from pathlib import Path

from flip7.types.events import Event
from flip7.types.game_state import GameState
from flip7.events.event_serializer import deserialize_event


def load_events(log_path: Path) -> list[Event]:
    """Read a JSONL event log file and parse all events.

    Reads the file line by line, deserializing each JSON line into an Event object.
    Empty lines and whitespace-only lines are skipped.

    Args:
        log_path: Path to the JSONL event log file

    Returns:
        A list of Event objects in the order they were logged

    Raises:
        FileNotFoundError: If the log file doesn't exist
        json.JSONDecodeError: If any line contains invalid JSON
        ValueError: If any event has invalid field values

    Example:
        >>> from pathlib import Path
        >>> events = load_events(Path("game_logs/game_123.jsonl"))
        >>> len(events)
        42
        >>> events[0].event_type
        'game_started'
    """
    events: list[Event] = []

    # Read file with explicit UTF-8 encoding
    with log_path.open(mode='r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            # Skip empty lines
            line = line.strip()
            if not line:
                continue

            try:
                event = deserialize_event(line)
                events.append(event)
            except Exception as e:
                # Provide helpful error context
                raise ValueError(
                    f"Failed to deserialize event on line {line_num}: {e}"
                ) from e

    return events


def replay_game(events: list[Event]) -> GameState:
    """Reconstruct the final game state by replaying a sequence of events.

    This function processes events in order and builds up the game state.
    Currently provides a basic implementation that validates the event sequence
    and constructs the final GameState from terminal events.

    Args:
        events: A list of Event objects to replay, in chronological order

    Returns:
        The final GameState after all events have been processed

    Raises:
        ValueError: If the event sequence is invalid or incomplete

    Example:
        >>> events = load_events(Path("game_logs/game_123.jsonl"))
        >>> final_state = replay_game(events)
        >>> final_state.is_complete
        True
        >>> final_state.winner
        'player1'

    Note:
        This is a foundational implementation. A full replay engine would need
        to process each event type and incrementally build up RoundState and
        GameState objects. For now, this validates the basic event sequence
        and extracts final state from completion events.
    """
    if not events:
        raise ValueError("Cannot replay game: event list is empty")

    # Validate that we have a game_started event
    if events[0].event_type != "game_started":
        raise ValueError(
            f"Expected first event to be 'game_started', got '{events[0].event_type}'"
        )

    # Extract game ID and validate consistency
    game_id = events[0].game_id
    for i, event in enumerate(events):
        if event.game_id != game_id:
            raise ValueError(
                f"Event {i} has mismatched game_id: expected '{game_id}', "
                f"got '{event.game_id}'"
            )

    # Validate that timestamps are monotonically increasing
    for i in range(1, len(events)):
        if events[i].timestamp < events[i - 1].timestamp:
            raise ValueError(
                f"Event {i} has timestamp earlier than previous event: "
                f"{events[i].timestamp} < {events[i - 1].timestamp}"
            )

    # Find the game_started event to get player list
    game_started_event = events[0]
    players = tuple(game_started_event.data.get("players", []))

    if not players:
        raise ValueError("game_started event missing 'players' data")

    # Initialize scores for all players
    scores: dict[str, int] = {player_id: 0 for player_id in players}

    # Process events to build final state
    current_round = 0
    is_complete = False
    winner: str | None = None

    for event in events:
        if event.event_type == "round_started":
            current_round = event.round_number or 0

        elif event.event_type == "round_ended":
            # Update scores from round results
            round_scores = event.data.get("scores", {})
            for player_id, round_score in round_scores.items():
                if player_id in scores:
                    scores[player_id] += round_score

        elif event.event_type == "game_ended":
            is_complete = True
            winner = event.data.get("winner")

    # Construct and return final GameState
    return GameState(
        game_id=game_id,
        players=players,
        scores=scores,
        current_round=current_round,
        is_complete=is_complete,
        winner=winner,
    )
