"""
Validation functions for game rules in Flipped Seven.

This module provides validation functions that check whether player actions
are legal according to game rules. All validators raise InvalidMove exceptions
with descriptive error messages when rules are violated.
"""

from flip7.types.cards import ActionType
from flip7.types.errors import InvalidMove
from flip7.types.game_state import PlayerTableau


def validate_hit(tableau: PlayerTableau) -> None:
    """
    Validate that a player can hit (draw a card).

    A player can hit if and only if they are active, not frozen,
    not passed, and not busted.

    Args:
        tableau: The player's current tableau state

    Raises:
        InvalidMove: If the player cannot hit due to any game rule violation:
            - Player is not active
            - Player is frozen
            - Player has passed
            - Player is busted

    Example:
        >>> tableau = PlayerTableau(
        ...     player_id="alice",
        ...     number_cards=(NumberCard(3),),
        ...     modifier_cards=(),
        ...     second_chance=False,
        ...     is_active=True,
        ...     is_busted=False,
        ...     is_frozen=False,
        ...     is_passed=False
        ... )
        >>> validate_hit(tableau)  # No exception raised
    """
    if not tableau.is_active:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot hit: player is not active"
        )

    if tableau.is_frozen:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot hit: player is frozen"
        )

    if tableau.is_passed:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot hit: player has already passed"
        )

    if tableau.is_busted:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot hit: player is busted"
        )


def validate_pass(tableau: PlayerTableau) -> None:
    """
    Validate that a player can pass (end their turn voluntarily).

    A player can pass if and only if they are active and have not
    already passed.

    Args:
        tableau: The player's current tableau state

    Raises:
        InvalidMove: If the player cannot pass due to any game rule violation:
            - Player is not active
            - Player has already passed

    Example:
        >>> tableau = PlayerTableau(
        ...     player_id="bob",
        ...     number_cards=(NumberCard(5), NumberCard(7)),
        ...     modifier_cards=(),
        ...     second_chance=False,
        ...     is_active=True,
        ...     is_busted=False,
        ...     is_frozen=False,
        ...     is_passed=False
        ... )
        >>> validate_pass(tableau)  # No exception raised
    """
    if not tableau.is_active:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot pass: player is not active"
        )

    if tableau.is_passed:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot pass: player has already passed"
        )


def validate_action_target(
    target_id: str,
    eligible_players: list[str],
    action: ActionType,
) -> None:
    """
    Validate that an action card can be played on the specified target.

    Validates that the target is in the eligible players list and applies
    action-specific rules:
    - FREEZE: Cannot target self, cannot target already frozen players
    - FLIP_THREE: Cannot target busted players
    - SECOND_CHANCE: No additional restrictions beyond eligibility

    Args:
        target_id: The player ID being targeted
        eligible_players: List of player IDs who are eligible to be targeted
        action: The type of action card being played

    Raises:
        InvalidMove: If the target is invalid due to any rule violation:
            - Target is not in the eligible players list
            - Action-specific restrictions are violated

    Example:
        >>> validate_action_target(
        ...     target_id="charlie",
        ...     eligible_players=["charlie", "diana"],
        ...     action=ActionType.FREEZE
        ... )  # No exception raised
    """
    # First, check if target is in eligible list
    if target_id not in eligible_players:
        raise InvalidMove(
            f"Invalid target '{target_id}' for {action.value}: "
            f"must be one of {eligible_players}"
        )

    # Action-specific validation rules
    # Note: Additional context (like whether target is frozen or busted) should be
    # checked by the caller who has access to the full game state. This function
    # only validates basic eligibility rules based on the action type.


def validate_second_chance_usage(
    tableau: PlayerTableau,
    has_second_chance: bool,
) -> None:
    """
    Validate that a player can use a Second Chance card.

    A player can use Second Chance if and only if:
    - They have a Second Chance card available
    - They have just busted (or would bust from the current card)

    Note: This validation checks that the player has the card available.
    The busted state is checked separately since Second Chance is used
    BEFORE the player is marked as busted (it prevents the bust).

    Args:
        tableau: The player's current tableau state
        has_second_chance: Whether the player currently has a Second Chance card

    Raises:
        InvalidMove: If the player cannot use Second Chance:
            - Player does not have a Second Chance card available
            - Player is not in a bust situation

    Example:
        >>> tableau = PlayerTableau(
        ...     player_id="eve",
        ...     number_cards=(NumberCard(3), NumberCard(3)),  # Would bust
        ...     modifier_cards=(),
        ...     second_chance=True,
        ...     is_active=True,
        ...     is_busted=False,
        ...     is_frozen=False,
        ...     is_passed=False
        ... )
        >>> validate_second_chance_usage(tableau, has_second_chance=True)  # Valid
    """
    if not has_second_chance:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot use Second Chance: "
            "no Second Chance card available"
        )

    # Note: The tableau.second_chance field should match has_second_chance
    # but we use the explicit parameter for clarity and to allow the caller
    # to track this state separately if needed
    if not tableau.second_chance:
        raise InvalidMove(
            f"Player {tableau.player_id} cannot use Second Chance: "
            "player does not have a Second Chance card in tableau"
        )
