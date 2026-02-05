# Flip 7 Tournament Harness

A lovingly over-engineered, strongly-typed, event-sourced Python harness for Flip 7 bot development and testing.

## What is Flip 7?

Draw numbered cards (0-12), modifiers (X2, +2/+4/+6/+8/+10), and action cards (Freeze, Flip Three, Second Chance). The goal is to reach exactly 7 unique number cards for bonus points without busting (drawing duplicates). First to 200 points wins.

## Hosted Competition

We run a hosted tournament service for submitted bots. Leaderboard results are updated nightly.

- Competitor instructions: `COMPETITOR_README.md`
- Hosted API/CLI: `hosted/README.md`
- Fair play: we may disqualify entries that violate the spirit of the game (e.g., exploiting system/infra limits or attempting to break isolation).

### Allowed Dependencies (Hosted Bots)

Hosted bots may only depend on Python stdlib plus:

- `numpy`
- `pandas`
- `scikit-learn`

If you need more packages, ask first.

## Installation

**Platform Requirement:** The bot sandbox uses Unix signals. Windows users must use WSL.

```bash
cd flipped_seven
uv sync --all-extras
```

## Quick Start

### 1) Create a Bot

Create `flip7/bots/my_bot.py` (auto-discovered):

```python
from flip7.bots.base import BaseBot
from flip7.types.events import BotDecisionContext
from flip7.types.cards import ActionType, NumberCard
from typing import Literal


class MyBot(BaseBot):
    """My custom strategy bot."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        hand_value = sum(c.value for c in context.my_tableau.number_cards)
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
        return max(eligible, key=lambda p: context.opponent_scores.get(p, 0))
```

**Note:** Bot files must be in `flip7/bots/` and inherit from `BaseBot`.

### 2) Run a Tournament

```bash
uv run flip7
```

This runs two tournaments:

- Head-to-head (2-player direct matchups)
- All-vs-all (all bots per game)

Results are written to separate output directories defined in `tournament_config.py`.

## CLI Tools

- `flip7` - Full tournament (head-to-head + all-vs-all)
- `flip7-step` - Interactive round debugger
- `flip7-demo` - Quick demo game
- `flip7-results <file>` - Display tournament results

## Debugging

Interactive round stepper:

```bash
# Default: RandomBot vs ScaredyBot
uv run flip7-step

# Test your bot
uv run flip7-step my_bot.MyBot ScaredyBot

# With seed for reproducibility
uv run flip7-step RandomBot ScaredyBot --seed 42
```

Full guide: `DEBUGGING.md`.

## Tournament Configuration

Edit `tournament_config.py`:

```python
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100_000
GAMES_PER_MATCHUP_ALL_VS_ALL = 1_000_000
BOT_TIMEOUT_SECONDS = 1.0
SAVE_REPLAYS = False  # True = detailed analysis (slower, disk-intensive)
OUTPUT_DIR_HEAD_TO_HEAD = Path("./tournament_results_head_to_head")
OUTPUT_DIR_ALL_VS_ALL = Path("./tournament_results_all_vs_all")
TOURNAMENT_SEED = 42  # Reproducibility
```

### Useful presets

```python
# Quick test
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100
GAMES_PER_MATCHUP_ALL_VS_ALL = 100
```

```python
# Medium analysis
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 10_000
GAMES_PER_MATCHUP_ALL_VS_ALL = 10_000
```

## Bot Decision Context (High-Level)

- `context.my_tableau` - Your cards and status
- `context.opponent_tableaus` - All opponents' cards
- `context.deck_remaining` - Cards left in deck
- `context.my_current_score` - Your cumulative score
- `context.opponent_scores` - Opponents' cumulative scores
- `context.current_round` - Round number
- `context.target_score` - Score needed to win (200)

Full guide: `BUILDING_A_BOT.md`.

## Reference Bots

- **RandomBot**: Random decisions (baseline)
- **ScaredyBot**: Passes at 15+ points
- **Hit17Bot**: Hits until 17 (Blackjack-style)

## Troubleshooting

**Bot not found**
- File must be in `flip7/bots/` and named `*_bot.py`
- Class must inherit from `BaseBot`
- Use `module.ClassName` format (e.g., `my_bot.MyBot`)

**Bot timeout**
- Default timeout: 1 second
- Avoid expensive computation in decision methods

**Import errors**
- Prefix all commands with `uv run`
- Reinstall dependencies: `uv sync --all-extras`

**Compliance tests**
- `uv run pytest tests/test_bot_compliance.py -v -k YourBotName`

## Development

```bash
# Type check
uvx --from mypy mypy flip7/ --strict

# Tests
uv run pytest

# Format
uvx ruff format flip7/
```

## Docs

- Rules: `RULES.md`
- Bot building guide: `BUILDING_A_BOT.md`
- Debugging: `DEBUGGING.md`
- Admin notes: `ADMIN_README.md`

## Architecture

- `flip7/constants.py` - Game rules (immutable)
- `flip7/types/` - Type definitions (frozen dataclasses)
- `flip7/core/` - Game engine
- `flip7/events/` - Event sourcing
- `flip7/bots/` - Bot implementations
- `flip7/tournament/` - Tournament system
- `flip7/utils/` - Analysis tools
- `flip7/cli/` - CLI

## License

TBD
