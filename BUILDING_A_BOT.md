# Building a Flip 7 Bot

Technical reference for creating competitive Flip 7 bots.

**Platform Requirement:** Unix signals required for bot sandboxing. Windows users must use WSL.

## Quick Start

Create `flip7/bots/my_bot.py` (must be in `flip7/bots/` directory):

```python
from flip7.bots.base import BaseBot
from flip7.types.events import BotDecisionContext
from flip7.types.cards import ActionType, NumberCard
from typing import Literal


class MyBot(BaseBot):
    """Your bot description here."""

    def decide_hit_or_pass(
        self, context: BotDecisionContext
    ) -> Literal["hit", "pass"]:
        """Decide whether to draw another card or lock in your score."""
        return "hit"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        """Decide whether to use Second Chance to avoid busting."""
        return True

    def choose_action_target(
        self, context: BotDecisionContext,
        action: ActionType,
        eligible: list[str]
    ) -> str:
        """Choose which player to target with an action card."""
        return eligible[0]
```

Run compliance tests (all must pass):

```bash
uv run pytest tests/test_bot_compliance.py::test_bot_implements_protocol[MyBot] -v
```

Test locally:

```bash
uv run flip7-step my_bot.MyBot ConservativeBot  # Interactive stepper
uv run flip7  # Tournament (edit tournament_config.py first)
```

## Bot Interface Requirements

### 1. `decide_hit_or_pass(context: BotDecisionContext) -> Literal["hit", "pass"]`

**Called:** On your turn when deciding whether to draw another card.

**Returns:** `"hit"` (draw card) or `"pass"` (lock in score, end turn)

**Called until:** You pass, bust, achieve Flip 7 (auto-pass), get frozen, or timeout.

### 2. `decide_use_second_chance(context: BotDecisionContext, duplicate: NumberCard) -> bool`

**Called:** When you draw a duplicate number card AND possess a Second Chance card.

**Parameters:**
- `duplicate`: The `NumberCard` that caused the duplicate (e.g., `NumberCard(value=7)`)

**Returns:** `True` (use Second Chance, discard both cards, end turn, score normally) or `False` (bust, score 0)

**Note:** Returning `True` immediately ends your turn.

### 3. `choose_action_target(context: BotDecisionContext, action: ActionType, eligible: list[str]) -> str`

**Called:** When you draw an action card.

**Parameters:**
- `action`: `ActionType.FREEZE`, `ActionType.FLIP_THREE`, or `ActionType.SECOND_CHANCE`
- `eligible`: Valid player IDs you can target (always non-empty)

**Returns:** One player ID from `eligible` list. Can target yourself (`context.my_tableau.player_id`).

**Effects:**
- `FREEZE`: Target immediately passes and locks in current score
- `FLIP_THREE`: Target must draw 3 cards immediately
- `SECOND_CHANCE`: Target receives Second Chance card

## Decision Context Reference

### BotDecisionContext

```python
@dataclass
class BotDecisionContext:
    my_tableau: PlayerTableau                      # Your cards and status
    opponent_tableaus: dict[str, PlayerTableau]    # All opponents' cards
    deck_remaining: int                            # Cards remaining in deck
    my_current_score: int                          # Your cumulative score
    opponent_scores: dict[str, int]                # Opponents' cumulative scores
    current_round: int                             # Round number (1-indexed)
    target_score: int                              # Score to win (usually 200)
```

### PlayerTableau

```python
@dataclass
class PlayerTableau:
    player_id: str                          # Player's unique ID
    number_cards: tuple[NumberCard, ...]    # Number cards (0-12)
    modifier_cards: tuple[ModifierCard, ...] # Modifiers (X2, +2, +4, +6, +8, +10)
    second_chance: bool                     # Has Second Chance card?
    is_active: bool                         # Still playing this round?
    is_busted: bool                         # Drew a duplicate?
    is_frozen: bool                         # Hit by Freeze action?
    is_passed: bool                         # Chose to pass?
```

### Card Types

```python
@dataclass
class NumberCard:
    value: int  # 0-12

@dataclass
class ModifierCard:
    modifier: Literal["+2", "+4", "+6", "+8", "+10", "X2"]

@dataclass
class ActionCard:
    action_type: ActionType  # FREEZE, FLIP_THREE, or SECOND_CHANCE
```

### Context Access Patterns

```python
def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
    # Hand value
    hand_value = sum(card.value for card in context.my_tableau.number_cards)

    # Unique numbers (for Flip 7)
    unique_numbers = len(set(card.value for card in context.my_tableau.number_cards))

    # Has X2 modifier
    has_x2 = any(m.modifier == "X2" for m in context.my_tableau.modifier_cards)

    # Has Second Chance
    has_second_chance = context.my_tableau.second_chance

    # Opponent card counts
    opponent_card_counts = {
        pid: len(tableau.number_cards)
        for pid, tableau in context.opponent_tableaus.items()
    }

    # Am winning
    am_winning = context.my_current_score == max(
        [context.my_current_score] + list(context.opponent_scores.values())
    )

    return "hit" if hand_value < 15 else "pass"
```

## Return Value Requirements

### `decide_hit_or_pass`

Must return: `"hit"` or `"pass"` (exact strings, lowercase)

Invalid: `"Hit"`, `"h"`, `True/False`, `None`

### `decide_use_second_chance`

Must return: `True` or `False` (boolean)

Invalid: `"True"`, `1`, `0`, `None`

### `choose_action_target`

Must return: One player ID from `eligible` list (string)

Invalid: Player ID not in `eligible`, `None`

## Testing

### 1. Compliance Tests (Required)

```bash
uv run pytest tests/test_bot_compliance.py -v -k MyBot
```

All 45 tests must pass: protocol implementation, return values, edge cases, no crashes.

### 2. Interactive Stepper

```bash
uv run flip7-step my_bot.MyBot ConservativeBot
```

Step through a round turn-by-turn to observe decisions and game state.

### 3. Multi-Game Test

```python
from pathlib import Path
from flip7.core.game_engine import GameEngine
from flip7.bots import RandomBot, ConservativeBot
from flip7.bots.my_bot import MyBot


def test_multiple_games():
    """Run 10 games and see win rate."""
    wins = 0
    total = 10

    for i in range(total):
        player_ids = ["mybot", "random"]
        bots = {
            "mybot": MyBot("mybot"),
            "random": RandomBot("random"),
        }

        engine = GameEngine(
            game_id=f"test_{i}",
            player_ids=player_ids,
            bots=bots,
            event_log_path=Path(f"./test_logs/game_{i}.jsonl"),
            seed=i,
        )

        final_state = engine.execute_game()

        if final_state.winner == "mybot":
            wins += 1

        print(f"Game {i+1}: Winner = {final_state.winner}, "
              f"Scores = {final_state.scores}")

    print(f"\nWin rate: {wins}/{total} ({wins/total*100:.1f}%)")


if __name__ == "__main__":
    test_multiple_games()
```

Run: `uv run python test_my_bot.py`

### 4. Tournament Test

Edit `tournament_config.py`:

```python
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100  # Default: 100,000
GAMES_PER_MATCHUP_ALL_VS_ALL = 100    # Default: 1,000,000
SAVE_REPLAYS = True
```

Run: `uv run flip7`

Results: `./tournament_results_head_to_head/tournament_results.json`, `./tournament_results_all_vs_all/tournament_results.json`

### 5. Scenario Testing

```bash
# Test early game
uv run flip7-step my_bot.MyBot RandomBot --round 1

# Test when behind
uv run flip7-step my_bot.MyBot RandomBot --scores 120,180 --round 10

# Test when ahead
uv run flip7-step my_bot.MyBot RandomBot --scores 180,120 --round 10
```

## Example Bots

### RandomBot

```python
class RandomBot(BaseBot):
    """Makes random decisions."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        return random.choice(["hit", "pass"])

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        return random.choice([True, False])

    def choose_action_target(
        self, context: BotDecisionContext,
        action: ActionType,
        eligible: list[str]
    ) -> str:
        return random.choice(eligible)
```

### ConservativeBot

```python
class ConservativeBot(BaseBot):
    """Plays conservatively to minimize busting."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        hand_value = sum(card.value for card in context.my_tableau.number_cards)
        return "pass" if hand_value >= 15 else "hit"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        return True

    def choose_action_target(
        self, context: BotDecisionContext,
        action: ActionType,
        eligible: list[str]
    ) -> str:
        return random.choice(eligible)
```

### Advanced Bot Template

```python
class AdvancedBot(BaseBot):
    """Template showing advanced techniques."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        hand_value = sum(card.value for card in context.my_tableau.number_cards)
        unique_count = len(set(card.value for card in context.my_tableau.number_cards))

        # Factor in modifiers
        has_x2 = any(m.modifier == "X2" for m in context.my_tableau.modifier_cards)
        modifier_bonus = sum(
            int(m.modifier[1:]) for m in context.my_tableau.modifier_cards
            if m.modifier != "X2"
        )

        expected_score = hand_value
        if has_x2:
            expected_score *= 2
        expected_score += modifier_bonus

        if unique_count == 7:
            expected_score += 15

        # Strategy based on game phase
        if context.current_round <= 3:
            # Early game: aggressive, go for Flip 7
            if unique_count < 7:
                return "hit"
            return "pass"
        elif context.current_round >= 10:
            # Late game: conservative
            return "pass" if expected_score >= 18 else "hit"
        else:
            # Mid game: balanced
            return "pass" if expected_score >= 15 else "hit"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        hand_value = sum(card.value for card in context.my_tableau.number_cards)

        # If hand is very low value, might be better to bust and start fresh
        if hand_value < 5 and context.current_round <= 5:
            return False

        return True

    def choose_action_target(
        self, context: BotDecisionContext,
        action: ActionType,
        eligible: list[str]
    ) -> str:
        if action == ActionType.FREEZE:
            # Freeze the player with the best hand
            best_player = max(
                eligible,
                key=lambda p: sum(
                    card.value
                    for card in context.opponent_tableaus[p].number_cards
                ) if p in context.opponent_tableaus else 0
            )
            return best_player

        elif action == ActionType.FLIP_THREE:
            # Give Flip Three to player most likely to bust
            target = max(
                eligible,
                key=lambda p: len(context.opponent_tableaus[p].number_cards)
                if p in context.opponent_tableaus else 0
            )
            return target

        else:  # SECOND_CHANCE
            # Give to yourself if eligible, otherwise first player
            if context.my_tableau.player_id in eligible:
                return context.my_tableau.player_id
            return eligible[0]
```

## Strategy

### Scoring Formula

```
Final Score = (Number Cards Sum) × (X2 if present) + (All +N modifiers) + (Flip 7 bonus if 7 unique)
```

**Example:** Cards [10, 11, 12, 9, 8, 7, 6] = 63, X2 = 126, +10 = 136, Flip 7 = 151 points

### Risk Assessment

**Bust Probability:** (Cards in Hand) / (Deck Remaining)

**Low Risk:** 2-3 cards, have Second Chance, early in round

**High Risk:** 5-6 cards, no Second Chance, many unique numbers

### Flip 7 Strategy

- +15 bonus AND auto-pass
- Worth ~2-3 extra cards of value
- Requires 7 unique numbers from 0-12 (13 possible)
- More achievable with larger deck

### Game Phases

**Early (Rounds 1-5):** Aggressive, go for Flip 7, build score foundation

**Mid (Rounds 6-10):** Balanced, monitor opponents, adjust based on position

**Late (Round 10+):** Conservative if ahead, aggressive if behind, calculate exact points needed

### Positional Play

```python
def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
    scores = [context.my_current_score] + list(context.opponent_scores.values())
    leader_score = max(scores)

    if context.my_current_score < leader_score:
        threshold = 18  # Take more risks when behind
    else:
        threshold = 15  # Play safer when ahead

    hand_value = sum(card.value for card in context.my_tableau.number_cards)
    return "pass" if hand_value >= threshold else "hit"
```

### Action Card Tactics

**Freeze:** Use on player with good hand or leader to deny Flip 7 opportunity

**Flip Three:** Force risky draws on opponents (higher bust chance, but can backfire)

**Second Chance:** Highly valuable, keep for yourself when possible

## Debugging

### Logging

```python
import logging

class MyBot(BaseBot):
    def __init__(self, bot_name: str):
        super().__init__(bot_name)
        self.logger = logging.getLogger(f"bot.{bot_name}")
        self.logger.setLevel(logging.DEBUG)

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        hand_value = sum(card.value for card in context.my_tableau.number_cards)

        self.logger.info(f"Hand value: {hand_value}")
        self.logger.info(f"Deck remaining: {context.deck_remaining}")

        decision = "hit" if hand_value < 15 else "pass"
        self.logger.info(f"Decision: {decision}")

        return decision
```

### Common Issues

**Bot Times Out:** Default timeout is 5 seconds. Avoid expensive computations, use pre-calculated probabilities and lookup tables.

**Bot Crashes:** Check return types, validate against compliance tests, handle empty collections, don't assume specific opponent count.

**Bad Decisions:** Add logging, test edge cases, review event logs.

**Compliance Failures:** Check return type (string vs bool vs player ID), verify values from `eligible` list, handle edge cases.

### Replay Analysis

Enable `SAVE_REPLAYS = True` in `tournament_config.py`:

```bash
# View event log
cat tournament_results_head_to_head/replays/game_001.jsonl | jq

# Replay with stepper
uv run flip7-step MyBot RandomBot --seed 42
```

Event logs contain: every card drawn, every decision, all game state transitions, final scores and outcome.
