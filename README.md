# Flip 7 Tournament Harness

A strongly-typed, event-sourced Python implementation of Flip 7 for bot development and testing.

## Overview

Flip 7 is a card game where players draw numbered cards (0-12), modifiers (X2, +2/+4/+6/+8/+10), and action cards (Freeze, Flip Three, Second Chance) trying to reach exactly 7 unique number cards for bonus points without busting (drawing duplicates). First player to 200 points wins.

## Installation

```bash
cd flipped_seven
uv sync --all-extras
```

## Usage

### 1. Edit tournament_config.py

```python
# Set number of games to run
NUM_GAMES = 1000  # 100, 1000, 10000, or 100000

# Add your bots
BOT_CLASSES = [
    RandomBot,
    ConservativeBot,
    MyBot,  # Your custom bot
]

# Enable detailed analysis (slower, uses disk space)
SAVE_REPLAYS = False  # Set True for behavioral analysis
```

### 2. Run Tournament

```bash
uv run flip7
```

That's it! The tournament will:
- Run NUM_GAMES sequentially
- Cycle through all bot matchups
- Show progress bar with time remaining
- Display final standings
- Auto-analyze behavior (if SAVE_REPLAYS=True)

## Creating Your Own Bot

Create `my_bot.py`:

```python
from flip7.bots.base import BaseBot
from flip7.types.events import BotDecisionContext
from flip7.types.cards import ActionType, NumberCard
from typing import Literal


class MyBot(BaseBot):
    """My custom strategy bot."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        # Your strategy here
        hand_value = sum(c.value for c in context.my_tableau.number_cards)
        return "pass" if hand_value >= 15 else "hit"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        return True  # Always avoid busting

    def choose_action_target(
        self, context: BotDecisionContext,
        action: ActionType,
        eligible: list[str]
    ) -> str:
        # Target player with highest score
        return max(eligible, key=lambda p: context.opponent_scores.get(p, 0))
```

Add to `tournament_config.py`:

```python
from flip7.bots.my_bot import MyBot

BOT_CLASSES = [RandomBot, ConservativeBot, MyBot]
```

Run:

```bash
uv run flip7
```

## Debugging Your Bot

### Interactive Round Stepper

Step through a single round turn-by-turn to see exactly what your bot is doing:

```bash
# Default: RandomBot vs ConservativeBot
uv run python step_round.py

# Test your bot
uv run python step_round.py my_bot.MyBot ConservativeBot

# With specific seed for reproducibility
uv run python step_round.py RandomBot ConservativeBot --seed 42
```

The stepper pauses at each decision point and shows:
- **Game State**: All player tableaus with cards and status
- **Decision Context**: Hand value, unique numbers, cards remaining
- **Bot Decisions**: What the bot decided (hit/pass) and why
- **Card Effects**: What card was drawn and what happened
- **Action Cards**: Target selection for Freeze/Flip Three/Second Chance
- **Bust Detection**: Duplicate detection and Second Chance usage
- **Score Breakdown**: Detailed score calculation at the end

Press Enter to advance through each turn. This is the best way to understand exactly what your bot is doing and debug edge cases!

See [DEBUGGING.md](DEBUGGING.md) for a complete debugging guide with examples and tips.

## Bot Decision Context

Your bot receives full game state:

- `context.my_tableau` - Your cards and status
- `context.opponent_tableaus` - All opponents' cards
- `context.deck_remaining` - Cards left in deck
- `context.my_current_score` - Your cumulative score
- `context.opponent_scores` - Opponents' cumulative scores
- `context.current_round` - Which round number
- `context.target_score` - Score needed to win (200)

## Tournament Configuration

Edit `tournament_config.py`:

```python
# Games to run
NUM_GAMES = 1000  # Quick: 100, Medium: 1000, Large: 10000, Massive: 100000

# Players per game
PLAYERS_PER_GAME = 2  # 2, 3, or 4

# Bots to test
BOT_CLASSES = [RandomBot, ConservativeBot, MyBot]

# Analysis
SAVE_REPLAYS = False  # True = detailed behavior analysis (slower, uses disk)

# Output
OUTPUT_DIR = Path("./tournament_results")
TOURNAMENT_SEED = 42  # For reproducibility
```

## Behavioral Analysis

Set `SAVE_REPLAYS = True` in config, then run tournament.

Analysis automatically shows:

**Overall Performance**
- Win rates and average scores
- Rounds played and won

**Decision Patterns**
- Hit vs pass percentages
- Average hand value when passing

**Risk Behavior**
- Bust rates
- Average hand value when busting
- Second Chance usage

**Special Achievements**
- Flip 7 achievement rates
- Action card usage patterns

## Examples

### Quick Test (100 games)
```python
NUM_GAMES = 100
SAVE_REPLAYS = False
```
Run time: ~2-3 minutes

### Medium Test (1,000 games)
```python
NUM_GAMES = 1000
SAVE_REPLAYS = False
```
Run time: ~20-30 minutes

### Large Scale (10,000 games)
```python
NUM_GAMES = 10000
SAVE_REPLAYS = False
```
Run time: ~3-5 hours

### Massive Scale (100,000 games)
```python
NUM_GAMES = 100000
SAVE_REPLAYS = False  # Don't save replays (too much disk space)
```
Run time: ~30-50 hours (1-2 days)

## Development

### Type Check
```bash
uvx --from mypy mypy flip7/ --strict
```

### Run Tests
```bash
uv run pytest
```

### Format
```bash
uvx ruff format flip7/
```

## Bot Development Tips

1. **Start Simple** - Basic threshold strategy first
2. **Test Small** - Run 100 games initially
3. **Scale Up** - 1000 → 10000 → 100000
4. **Analyze** - Use SAVE_REPLAYS=True on smaller runs
5. **Iterate** - Adjust based on behavioral patterns
6. **Think Strategic** - Early vs late game, ahead vs behind

## Game Rules

See [RULES.md](RULES.md) for complete rules.

## Architecture

- **`flip7/constants.py`** - Game rules (immutable)
- **`flip7/types/`** - Type definitions (frozen dataclasses)
- **`flip7/core/`** - Game engine
- **`flip7/events/`** - Event sourcing
- **`flip7/bots/`** - Bot implementations
- **`flip7/tournament/`** - Tournament system
- **`flip7/utils/`** - Analysis tools
- **`flip7/cli/`** - CLI

## License

TBD
