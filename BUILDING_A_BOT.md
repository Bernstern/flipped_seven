# Building a Flip 7 Bot

Complete guide to creating, testing, and deploying your own competitive Flip 7 bot.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Bot Interface Requirements](#bot-interface-requirements)
3. [Decision Context Reference](#decision-context-reference)
4. [Return Values](#return-values)
5. [Testing Your Bot](#testing-your-bot)
6. [Example Bots](#example-bots)
7. [Strategy Tips](#strategy-tips)
8. [Debugging](#debugging)

---

## Quick Start

### Step 1: Create Your Bot File

Create `flip7/bots/my_bot.py`:

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
        # Your strategy here
        return "hit"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        """Decide whether to use Second Chance to avoid busting."""
        # Your strategy here
        return True

    def choose_action_target(
        self, context: BotDecisionContext,
        action: ActionType,
        eligible: list[str]
    ) -> str:
        """Choose which player to target with an action card."""
        # Your strategy here
        return eligible[0]
```

### Step 2: Run Compliance Tests

```bash
uv run pytest tests/test_bot_compliance.py::test_bot_implements_protocol[MyBot] -v
```

All tests must pass before your bot can compete in tournaments.

### Step 3: Test Locally

```bash
uv run flip7 quick-game -p 2 -b flip7.bots.my_bot.MyBot -b random
```

---

## Bot Interface Requirements

Your bot MUST implement three methods from the `Bot` protocol:

### 1. `decide_hit_or_pass(context: BotDecisionContext) -> Literal["hit", "pass"]`

**When Called:** On your turn, when you must decide whether to draw another card.

**Must Return:** Exactly the string `"hit"` or `"pass"`

**Purpose:**
- `"hit"` = Draw another card from the deck
- `"pass"` = Lock in your current score and end your turn

**Called Every Turn Until:**
- You pass
- You bust (draw a duplicate number)
- You achieve Flip 7 (7 unique numbers - auto-passes)
- You get frozen by an action card
- You timeout

---

### 2. `decide_use_second_chance(context: BotDecisionContext, duplicate: NumberCard) -> bool`

**When Called:** When you draw a duplicate number card AND you have a Second Chance card.

**Parameters:**
- `context`: Current game state
- `duplicate`: The `NumberCard` that caused the duplicate (e.g., `NumberCard(value=7)`)

**Must Return:** `True` or `False`

**Purpose:**
- `True` = Use Second Chance (discard both the duplicate and Second Chance card, end turn, score normally)
- `False` = Don't use Second Chance (bust, score 0 this round)

**Important:** If you return `True`, your turn ends immediately even if you could draw more cards.

---

### 3. `choose_action_target(context: BotDecisionContext, action: ActionType, eligible: list[str]) -> str`

**When Called:** When you draw an action card and must choose who gets the effect.

**Parameters:**
- `context`: Current game state
- `action`: Which action card (`ActionType.FREEZE`, `ActionType.FLIP_THREE`, or `ActionType.SECOND_CHANCE`)
- `eligible`: List of valid player IDs you can target (always includes at least one player)

**Must Return:** One of the player IDs from the `eligible` list

**Purpose:**
- `ActionType.FREEZE`: Target player immediately passes and locks in their current score
- `ActionType.FLIP_THREE`: Target player must draw 3 cards immediately
- `ActionType.SECOND_CHANCE`: Target player receives a Second Chance card for later use

**Important:** You can target yourself! Your bot's player ID is in `context.my_tableau.player_id`.

---

## Decision Context Reference

Every decision method receives a `BotDecisionContext` object with complete game information.

### BotDecisionContext Fields

```python
@dataclass
class BotDecisionContext:
    # Your cards and status
    my_tableau: PlayerTableau

    # All opponents' cards (dict: player_id -> PlayerTableau)
    opponent_tableaus: dict[str, PlayerTableau]

    # Cards remaining in deck
    deck_remaining: int

    # Your cumulative score across all rounds
    my_current_score: int

    # Opponents' cumulative scores (dict: player_id -> score)
    opponent_scores: dict[str, int]

    # Which round (1-indexed)
    current_round: int

    # Score needed to win (usually 200)
    target_score: int
```

### PlayerTableau Fields

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

### Example: Accessing Context Data

```python
def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
    # Get your current hand value
    hand_value = sum(card.value for card in context.my_tableau.number_cards)

    # Count unique numbers (for Flip 7)
    unique_numbers = len(set(card.value for card in context.my_tableau.number_cards))

    # Check if you have X2 modifier
    has_x2 = any(m.modifier == "X2" for m in context.my_tableau.modifier_cards)

    # Check if you have Second Chance
    has_second_chance = context.my_tableau.second_chance

    # See how many cards opponents have
    opponent_card_counts = {
        pid: len(tableau.number_cards)
        for pid, tableau in context.opponent_tableaus.items()
    }

    # Check if you're winning
    am_winning = context.my_current_score == max(
        [context.my_current_score] + list(context.opponent_scores.values())
    )

    # Your decision logic here...
    return "hit" if hand_value < 15 else "pass"
```

---

## Return Values

### `decide_hit_or_pass` Return Values

**MUST return exactly one of these strings:**
- `"hit"` - Draw another card
- `"pass"` - End your turn

**Invalid returns will cause your bot to fail compliance tests:**
- ❌ `"Hit"` (wrong capitalization)
- ❌ `"h"` (abbreviation)
- ❌ `True/False` (wrong type)
- ❌ `None` (no return)

### `decide_use_second_chance` Return Values

**MUST return a boolean:**
- `True` - Use Second Chance (avoid bust, end turn)
- `False` - Don't use Second Chance (bust, score 0)

**Invalid returns:**
- ❌ `"True"` (string, not bool)
- ❌ `1` or `0` (int, not bool)
- ❌ `None`

### `choose_action_target` Return Values

**MUST return one of the player IDs from the `eligible` list:**

```python
def choose_action_target(
    self, context: BotDecisionContext,
    action: ActionType,
    eligible: list[str]
) -> str:
    # CORRECT: Return one of the eligible IDs
    return eligible[0]

    # CORRECT: Return your own ID (if in eligible list)
    if context.my_tableau.player_id in eligible:
        return context.my_tableau.player_id

    # INCORRECT: Return an ID not in eligible
    return "some_other_player"  # Will cause error!
```

---

## Testing Your Bot

### 1. Compliance Tests (REQUIRED)

```bash
# Test that your bot implements the interface correctly
uv run pytest tests/test_bot_compliance.py -v -k MyBot
```

**Your bot MUST pass all 45 compliance tests:**
- Protocol implementation
- Valid return values
- Edge case handling (empty hand, no opponents, etc.)
- No crashes on valid game states

**If tests fail:**
1. Read the error message carefully
2. Fix the specific method mentioned
3. Re-run tests
4. Repeat until all pass

### 2. Single Game Test

```bash
# Play one game against RandomBot
uv run flip7 quick-game -p 2 -b flip7.bots.my_bot.MyBot -b random
```

This runs a complete game to 200 points and shows:
- Winner
- Final scores
- Number of rounds

### 3. Multi-Game Test

Create `test_my_bot.py`:

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

Run it:
```bash
uv run python test_my_bot.py
```

### 4. Tournament Test

Create `my_tournament.py`:

```python
from pathlib import Path
from flip7.tournament.config import TournamentConfig
from flip7.bots import RandomBot, ConservativeBot
from flip7.bots.my_bot import MyBot


config = TournamentConfig(
    tournament_name="MyBot Test Tournament",
    players_per_game=3,
    best_of_n=5,  # Best of 5 per matchup
    bot_classes=[MyBot, RandomBot, ConservativeBot],
    bot_timeout_seconds=5.0,
    output_dir=Path("./tournament_results"),
    save_replays=True,
    max_workers=4,
    tournament_seed=42,
)
```

Run it:
```bash
uv run flip7 run-tournament my_tournament.py
```

Results saved to `./tournament_results/tournament_results.json`.

### 5. Human Testing (Play Against Your Bot)

```bash
uv run flip7 quick-game -p 2 -b human -b flip7.bots.my_bot.MyBot
```

This lets you:
- See exactly what your bot sees
- Understand decision points
- Test edge cases interactively

---

## Example Bots

### RandomBot (Baseline)

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

### ConservativeBot (Simple Strategy)

```python
class ConservativeBot(BaseBot):
    """Plays conservatively to minimize busting."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        # Pass at 15+ points
        hand_value = sum(card.value for card in context.my_tableau.number_cards)
        return "pass" if hand_value >= 15 else "hit"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        # Always use Second Chance to avoid busting
        return True

    def choose_action_target(
        self, context: BotDecisionContext,
        action: ActionType,
        eligible: list[str]
    ) -> str:
        # Random targeting
        return random.choice(eligible)
```

### Advanced Bot Template

```python
class AdvancedBot(BaseBot):
    """Template showing advanced techniques."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        # Calculate current expected score
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

        # Add Flip 7 bonus if we have 7 unique
        if unique_count == 7:
            expected_score += 15

        # Calculate bust probability
        cards_in_hand = {card.value for card in context.my_tableau.number_cards}
        # With perfect information, calculate exact probability of drawing duplicate
        # (requires tracking discard pile and opponent cards)

        # Strategy based on game phase
        rounds_remaining = (context.target_score - context.my_current_score) / 20  # rough estimate

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
        # Use Second Chance unless hand is worthless
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
            # (player with most cards = more likely to hit duplicate)
            target = max(
                eligible,
                key=lambda p: len(context.opponent_tableaus[p].number_cards)
                if p in context.opponent_tableaus else 0
            )
            return target

        else:  # SECOND_CHANCE
            # Give to yourself if you're in eligible list, otherwise random
            if context.my_tableau.player_id in eligible:
                return context.my_tableau.player_id
            return eligible[0]
```

---

## Strategy Tips

### 1. Understand Scoring

```
Final Score = (Number Cards Sum) × (X2 if present) + (All +N modifiers) + (Flip 7 bonus if 7 unique)
```

**Example:**
- Cards: [10, 11, 12, 9, 8, 7, 6] = 63 points
- Has X2: 63 × 2 = 126
- Has +10: 126 + 10 = 136
- 7 unique numbers: 136 + 15 = **151 points**

### 2. Risk Management

**Low Risk:**
- Few cards in hand (2-3)
- Have Second Chance
- Early in round

**High Risk:**
- Many cards (5-6)
- No Second Chance
- Cards are spread out (many different numbers)

**Bust Probability = (Cards in Hand) / (Deck Remaining)**

### 3. Flip 7 Strategy

- Flip 7 gives +15 bonus AND auto-passes
- Worth ~2-3 extra cards of value
- Requires 7 unique numbers (0-12, so 13 possible)
- More achievable with larger deck

### 4. Game Phases

**Early Game (Rounds 1-5):**
- Be aggressive
- Go for Flip 7
- Build score foundation

**Mid Game (Rounds 6-10):**
- Balanced approach
- Monitor opponents
- Adjust based on position

**Late Game (Round 10+):**
- Conservative if ahead
- Aggressive if behind
- Calculate exact points needed

### 5. Opponent Modeling

```python
# Track what opponents typically do
def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
    # Who's winning?
    scores = [context.my_current_score] + list(context.opponent_scores.values())
    leader_score = max(scores)

    # Am I behind?
    if context.my_current_score < leader_score:
        # Need to take more risks
        threshold = 18
    else:
        # Can play safer
        threshold = 15

    hand_value = sum(card.value for card in context.my_tableau.number_cards)
    return "pass" if hand_value >= threshold else "hit"
```

### 6. Action Card Tactics

**Freeze:**
- Use on player with good hand
- Use on leader
- Deny them Flip 7 opportunity

**Flip Three:**
- Force risky draws on opponents
- Higher chance they bust
- Can backfire if they get good cards

**Second Chance:**
- Very valuable - keep for yourself if possible
- Give to weak opponents to help them (if strategically beneficial)

---

## Debugging

### Enable Logging

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
        self.logger.info(f"Opponents: {list(context.opponent_tableaus.keys())}")

        decision = "hit" if hand_value < 15 else "pass"
        self.logger.info(f"Decision: {decision}")

        return decision
```

### Common Issues

**1. Bot Times Out**
- Timeout is 5 seconds by default
- Avoid expensive computations
- Pre-calculate probabilities
- Use lookup tables

**2. Bot Crashes**
- Check all return types
- Validate against compliance tests
- Handle empty lists/dicts
- Don't assume specific opponent count

**3. Bot Makes Bad Decisions**
- Add logging to see what it sees
- Play as human against it
- Review event logs
- Test edge cases

**4. Compliance Tests Fail**
- Read error message carefully
- Check return type (string vs bool vs player ID)
- Ensure you handle all edge cases
- Verify you're returning values from `eligible` list

### Replay Analysis

```bash
# Replay a specific game to see what happened
uv run flip7 replay-game tournament_results/replays/game_001.jsonl
```

This shows:
- Every card drawn
- Every decision made
- Final scores
- Who won and why

---

## Next Steps

1. **Build your bot** using the template
2. **Pass compliance tests** (`pytest tests/test_bot_compliance.py -k YourBot`)
3. **Test locally** against RandomBot and ConservativeBot
4. **Run tournaments** with increasing game counts (5 → 50 → 500)
5. **Analyze results** and iterate on strategy
6. **Compete** in official tournaments

Good luck!
