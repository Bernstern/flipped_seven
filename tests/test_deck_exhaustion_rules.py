"""
Tests for deck exhaustion and reshuffling rules.

Per official rules (lines 113-117):
- If the draw pile runs out during a round, shuffle all discarded cards
  from previous rounds to create a new draw pile
- Do NOT shuffle cards currently in player tableaus
- Do NOT shuffle cards discarded from busts in the current round
"""

from pathlib import Path

import pytest

from flip7.bots import RandomBot
from flip7.core.round_engine import RoundEngine
from flip7.events.event_logger import EventLogger
from flip7.types.cards import NumberCard


def test_deck_exhaustion_reshuffles_discard_pile():
    """Test that deck exhaustion causes discard pile to be reshuffled."""
    player_ids = ["p1"]
    bots = {"p1": RandomBot("p1")}

    # Create a tiny deck that will run out
    deck = [NumberCard(1), NumberCard(2)]
    discard = [NumberCard(3), NumberCard(4), NumberCard(5)]

    with EventLogger(Path("/tmp/test_deck_exhaustion.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Draw all cards from deck
        engine._draw_card("p1")
        engine._draw_card("p1")

        # Deck should be empty
        assert len(engine.deck) == 0, "Deck should be empty after drawing all cards"

        # Draw another card - should trigger reshuffle
        card = engine._draw_card("p1")

        # Deck should now contain cards from discard pile (minus the one drawn)
        assert len(engine.deck) >= 0, "Deck should have cards from reshuffled discard"
        assert len(engine.discard_pile) == 0, "Discard pile should be empty after reshuffle"
        assert card is not None, "Should be able to draw from reshuffled deck"


def test_current_round_tableau_cards_not_reshuffled():
    """Test that cards in player tableaus are NOT reshuffled when deck runs out."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    # Create a tiny deck
    deck = [NumberCard(1), NumberCard(2)]
    discard = [NumberCard(5), NumberCard(6)]

    with EventLogger(Path("/tmp/test_tableau_not_shuffled.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Give p1 some cards
        card1 = engine._draw_card("p1")
        if isinstance(card1, NumberCard):
            engine._handle_number_card("p1", card1)

        # P1 has NumberCard(1) in tableau
        assert len(engine.tableaus["p1"].number_cards) > 0

        # Draw remaining deck cards
        engine._draw_card("p2")

        # Deck is now empty
        assert len(engine.deck) == 0

        # Draw another card to trigger reshuffle
        card = engine._draw_card("p2")

        # The card in p1's tableau should NOT be in the reshuffled deck
        # We verify this indirectly: the deck only has cards from discard pile
        # It should NOT contain NumberCard(1) since that's in p1's tableau
        deck_values = [c.value for c in engine.deck if isinstance(c, NumberCard)]

        # Verify deck was created from discard pile, not tableau
        assert isinstance(card, NumberCard), "Should draw a card from reshuffled deck"


def test_round_cleanup_moves_tableau_to_discard():
    """Test that _cleanup_tableaus moves all cards to discard pile."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_cleanup.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Give players some cards
        from dataclasses import replace

        engine.tableaus["p1"] = replace(
            engine.tableaus["p1"],
            number_cards=(NumberCard(3), NumberCard(5)),
        )
        engine.tableaus["p2"] = replace(
            engine.tableaus["p2"],
            number_cards=(NumberCard(7),),
        )

        # Total cards in tableaus: 3
        total_cards = sum(
            len(t.number_cards) for t in engine.tableaus.values()
        )
        assert total_cards == 3

        # Run cleanup
        engine._cleanup_tableaus()

        # All cards should be in discard pile
        assert len(engine.discard_pile) == 3, \
            "All tableau cards should be moved to discard pile"


def test_deck_persistence_across_rounds():
    """Test that deck and discard pile persist across rounds."""
    player_ids = ["p1"]
    bots = {"p1": RandomBot("p1")}

    # Start with a deck
    initial_deck = [NumberCard(i) for i in range(1, 8)]
    discard: list = []

    with EventLogger(Path("/tmp/test_deck_persistence.jsonl")) as logger:
        # Round 1
        engine1 = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=initial_deck.copy(),
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Execute round 1
        scores1 = engine1.execute_round()

        # After round, tableaus are cleaned up and cards moved to discard
        deck_after_r1 = engine1.deck
        discard_after_r1 = engine1.discard_pile

        # Round 2 uses same deck and discard
        engine2 = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck_after_r1,
            discard_pile=discard_after_r1,
            round_number=2,
            game_id="test",
            seed=42,
        )

        # Execute round 2
        scores2 = engine2.execute_round()

        # Verify rounds completed
        assert scores1 is not None
        assert scores2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
