"""Tests for debug helper functions."""

from io import StringIO

from rich.console import Console

from flip7.types.cards import ActionCard, ActionType, ModifierCard, NumberCard
from flip7.types.game_state import GameState, PlayerTableau, ScoreBreakdown
from flip7.utils.debug_helpers import (
    format_card,
    print_game_state,
    print_score_breakdown,
    print_tableau,
)


class TestFormatCard:
    """Tests for format_card function."""

    def test_format_number_card(self) -> None:
        """Test formatting of NumberCard."""
        card = NumberCard(5)
        assert format_card(card) == "[5]"

    def test_format_action_card(self) -> None:
        """Test formatting of ActionCard."""
        card = ActionCard(ActionType.FREEZE)
        assert format_card(card) == "[FREEZE]"

    def test_format_modifier_card_additive(self) -> None:
        """Test formatting of additive ModifierCard."""
        card = ModifierCard("+10")
        assert format_card(card) == "[+10]"

    def test_format_modifier_card_multiplier(self) -> None:
        """Test formatting of multiplier ModifierCard."""
        card = ModifierCard("X2")
        assert format_card(card) == "[X2]"


class TestPrintTableau:
    """Tests for print_tableau function."""

    def test_print_active_tableau(self) -> None:
        """Test printing an active player's tableau."""
        tableau = PlayerTableau(
            player_id="test_player",
            number_cards=(NumberCard(3), NumberCard(5)),
            modifier_cards=(ModifierCard("+2"),),
            second_chance=True,
            is_active=True,
            is_busted=False,
            is_frozen=False,
            is_passed=False,
        )

        # Capture output
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_tableau(tableau, console)

        result = output.getvalue()
        assert "test_player" in result
        assert "[3]" in result
        assert "[5]" in result
        assert "[+2]" in result
        assert "Yes" in result  # Second Chance

    def test_print_busted_tableau(self) -> None:
        """Test printing a busted player's tableau."""
        tableau = PlayerTableau(
            player_id="busted_player",
            number_cards=(NumberCard(5), NumberCard(5)),
            modifier_cards=(),
            second_chance=False,
            is_active=False,
            is_busted=True,
            is_frozen=False,
            is_passed=False,
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_tableau(tableau, console)

        result = output.getvalue()
        assert "busted_player" in result
        assert "BUSTED" in result

    def test_print_empty_tableau(self) -> None:
        """Test printing a tableau with no cards."""
        tableau = PlayerTableau(
            player_id="empty_player",
            number_cards=(),
            modifier_cards=(),
            second_chance=False,
            is_active=True,
            is_busted=False,
            is_frozen=False,
            is_passed=False,
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_tableau(tableau, console)

        result = output.getvalue()
        assert "empty_player" in result
        assert "(none)" in result


class TestPrintGameState:
    """Tests for print_game_state function."""

    def test_print_in_progress_game(self) -> None:
        """Test printing an in-progress game state."""
        game_state = GameState(
            game_id="test_game",
            players=("player1", "player2"),
            scores={"player1": 50, "player2": 75},
            current_round=2,
            is_complete=False,
            winner=None,
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_game_state(game_state, console)

        result = output.getvalue()
        assert "test_game" in result
        assert "2" in result  # Round number
        assert "In Progress" in result
        assert "player1" in result
        assert "50" in result

    def test_print_complete_game(self) -> None:
        """Test printing a completed game state."""
        game_state = GameState(
            game_id="finished_game",
            players=("alice", "bob"),
            scores={"alice": 205, "bob": 180},
            current_round=5,
            is_complete=True,
            winner="alice",
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_game_state(game_state, console)

        result = output.getvalue()
        assert "finished_game" in result
        assert "Complete" in result
        assert "alice" in result
        assert "205" in result


class TestPrintScoreBreakdown:
    """Tests for print_score_breakdown function."""

    def test_print_simple_score(self) -> None:
        """Test printing a simple score breakdown."""
        breakdown = ScoreBreakdown(
            number_cards_sum=15,
            after_x2_multiplier=15,
            modifier_additions=0,
            flip_7_bonus=0,
            final_score=15,
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_score_breakdown(breakdown, "test_player", console)

        result = output.getvalue()
        assert "test_player" in result
        assert "15" in result

    def test_print_score_with_multiplier(self) -> None:
        """Test printing score with X2 multiplier."""
        breakdown = ScoreBreakdown(
            number_cards_sum=20,
            after_x2_multiplier=40,
            modifier_additions=0,
            flip_7_bonus=0,
            final_score=40,
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_score_breakdown(breakdown, "multiplier_player", console)

        result = output.getvalue()
        assert "X2" in result
        assert "40" in result

    def test_print_score_with_flip_7_bonus(self) -> None:
        """Test printing score with Flip 7 bonus."""
        breakdown = ScoreBreakdown(
            number_cards_sum=28,
            after_x2_multiplier=28,
            modifier_additions=0,
            flip_7_bonus=15,
            final_score=43,
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_score_breakdown(breakdown, "flip7_player", console)

        result = output.getvalue()
        assert "Flip 7" in result
        assert "15" in result
        assert "43" in result

    def test_print_busted_score(self) -> None:
        """Test printing a busted player's score."""
        breakdown = ScoreBreakdown(
            number_cards_sum=0,
            after_x2_multiplier=0,
            modifier_additions=0,
            flip_7_bonus=0,
            final_score=0,
        )

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        print_score_breakdown(breakdown, "busted_player", console)

        result = output.getvalue()
        assert "0" in result
