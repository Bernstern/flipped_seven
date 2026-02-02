"""JSON serialization and deserialization for game events.

This module provides utilities to convert Event objects to and from JSON strings,
handling special types like datetime, Card objects, and frozen dataclasses.
"""

import json
from datetime import datetime
from typing import Any

from flip7.types.cards import ActionCard, ActionType, Card, ModifierCard, NumberCard
from flip7.types.events import Event


class CardEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Card objects and datetime values.

    This encoder extends the default JSONEncoder to serialize:
    - datetime objects as ISO 8601 strings
    - Card objects (NumberCard, ActionCard, ModifierCard) as typed dictionaries
    - All other objects using the default encoder
    """

    def default(self, obj: Any) -> Any:
        """Convert special objects to JSON-serializable formats.

        Args:
            obj: The object to serialize

        Returns:
            A JSON-serializable representation of the object

        Raises:
            TypeError: If the object type is not serializable
        """
        if isinstance(obj, datetime):
            return obj.isoformat()

        if isinstance(obj, NumberCard):
            return {
                "_card_type": "NumberCard",
                "value": obj.value,
            }

        if isinstance(obj, ActionCard):
            return {
                "_card_type": "ActionCard",
                "action_type": obj.action_type.value,
            }

        if isinstance(obj, ModifierCard):
            return {
                "_card_type": "ModifierCard",
                "modifier": obj.modifier,
            }

        return super().default(obj)


def _decode_card(card_dict: dict[str, Any]) -> Card:
    """Decode a dictionary representation of a Card back into a Card object.

    Args:
        card_dict: Dictionary with _card_type key and card-specific fields

    Returns:
        The reconstructed Card object

    Raises:
        ValueError: If the card type is unknown or fields are invalid
    """
    card_type = card_dict.get("_card_type")

    if card_type == "NumberCard":
        return NumberCard(value=card_dict["value"])

    if card_type == "ActionCard":
        action_type = ActionType(card_dict["action_type"])
        return ActionCard(action_type=action_type)

    if card_type == "ModifierCard":
        return ModifierCard(modifier=card_dict["modifier"])

    raise ValueError(f"Unknown card type: {card_type}")


def _decode_event_data(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively decode event data, converting card dictionaries to Card objects.

    Args:
        data: The event data dictionary potentially containing card representations

    Returns:
        A new dictionary with card dictionaries converted to Card objects
    """
    decoded: dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, dict) and "_card_type" in value:
            # This is a card object
            decoded[key] = _decode_card(value)
        elif isinstance(value, list):
            # Recursively decode lists (might contain cards)
            decoded[key] = [
                _decode_card(item) if isinstance(item, dict) and "_card_type" in item
                else item
                for item in value
            ]
        elif isinstance(value, dict):
            # Recursively decode nested dictionaries
            decoded[key] = _decode_event_data(value)
        else:
            # Copy primitive values as-is
            decoded[key] = value

    return decoded


def serialize_event(event: Event) -> str:
    """Convert an Event object to a JSON string.

    The event is serialized as a single-line JSON string suitable for appending
    to a JSONL (JSON Lines) file. All Card objects and datetime values are
    properly encoded.

    Args:
        event: The Event object to serialize

    Returns:
        A JSON string representation of the event (no newline at end)

    Example:
        >>> from datetime import datetime
        >>> from flip7.types.events import Event
        >>> event = Event(
        ...     event_type="game_started",
        ...     timestamp=datetime(2025, 1, 1, 12, 0, 0),
        ...     game_id="game123",
        ...     round_number=None,
        ...     player_id=None,
        ...     data={"players": ["player1", "player2"]}
        ... )
        >>> json_str = serialize_event(event)
        >>> "game_started" in json_str
        True
    """
    event_dict = {
        "event_type": event.event_type,
        "timestamp": event.timestamp,
        "game_id": event.game_id,
        "round_number": event.round_number,
        "player_id": event.player_id,
        "data": event.data,
    }

    return json.dumps(event_dict, cls=CardEncoder, separators=(',', ':'))


def deserialize_event(json_str: str) -> Event:
    """Parse a JSON string into an Event object.

    Reconstructs an Event from its JSON representation, properly decoding
    Card objects and datetime values.

    Args:
        json_str: A JSON string representing an event

    Returns:
        The reconstructed Event object

    Raises:
        json.JSONDecodeError: If the string is not valid JSON
        KeyError: If required event fields are missing
        ValueError: If field values are invalid

    Example:
        >>> json_str = '{"event_type":"game_started","timestamp":"2025-01-01T12:00:00",...}'
        >>> event = deserialize_event(json_str)
        >>> event.event_type
        'game_started'
    """
    data = json.loads(json_str)

    # Parse timestamp from ISO format
    timestamp = datetime.fromisoformat(data["timestamp"])

    # Decode any Card objects in the event data
    event_data = _decode_event_data(data["data"])

    return Event(
        event_type=data["event_type"],
        timestamp=timestamp,
        game_id=data["game_id"],
        round_number=data["round_number"],
        player_id=data["player_id"],
        data=event_data,
    )
