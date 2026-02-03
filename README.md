# Flip 7 Tournament Harness

Strongly-typed, event-sourced Python implementation of Flip 7 for bot development and testing.

## Overview

Flip 7: Draw numbered cards (0-12), modifiers (X2, +2/+4/+6/+8/+10), and action cards (Freeze, Flip Three, Second Chance). Goal: reach exactly 7 unique number cards for bonus points without busting (drawing duplicates). First to 200 points wins.

## CLI Tools

- `flip7` - Full tournament (head-to-head + all-vs-all)
- `flip7-step` - Interactive round debugger
- `flip7-demo` - Quick demo game
- `flip7-results <file>` - Display tournament results

## Installation

**Platform Requirement:** Requires Unix signals for bot sandboxing. Windows users must use WSL.

```bash
cd flipped_seven
uv sync --all-extras
```

## Quick Start

### 1. Create Your Bot

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

**Note:** Bot files must be in `flip7/bots/` directory.

### 2. (Optional) Configure Tournament

Edit `tournament_config.py`:

```python
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100_000  # 2-player matchups
GAMES_PER_MATCHUP_ALL_VS_ALL = 1_000_000  # All bots together
SAVE_REPLAYS = False  # Set True for detailed analysis (slower, disk-intensive)
```

### 3. Run Tournament

```bash
uv run flip7
```

Executes two tournaments:
- Head-to-head (2-player direct matchups)
- All-vs-all (all bots per game)
- Displays progress bars and final standings
- Saves results to separate directories

## Debugging

### Interactive Round Stepper

```bash
# Default: RandomBot vs ConservativeBot
uv run flip7-step

# Test your bot
uv run flip7-step my_bot.MyBot ConservativeBot

# With seed for reproducibility
uv run flip7-step RandomBot ConservativeBot --seed 42
```

Shows at each decision point:
- Game state (all player tableaus)
- Decision context (hand value, unique numbers, cards remaining)
- Bot decisions and rationale
- Card effects and outcomes
- Action card targeting
- Bust detection and Second Chance usage
- Score breakdown

See [DEBUGGING.md](DEBUGGING.md) for complete guide.

## Bot Decision Context

Available game state:
- `context.my_tableau` - Your cards and status
- `context.opponent_tableaus` - All opponents' cards
- `context.deck_remaining` - Cards left in deck
- `context.my_current_score` - Your cumulative score
- `context.opponent_scores` - Opponents' cumulative scores
- `context.current_round` - Round number
- `context.target_score` - Score needed to win (200)

## Tournament Structure

### 1. Head-to-Head (2-Player)
- Round-robin: every bot vs every other bot
- Games per matchup: `GAMES_PER_MATCHUP_HEAD_TO_HEAD` (default: 100,000)
- Output: `OUTPUT_DIR_HEAD_TO_HEAD/tournament_results.json`
- Shows overall standings + win/loss matrix

### 2. All-vs-All (Multiplayer)
- All bots compete simultaneously
- Total games: `GAMES_PER_MATCHUP_ALL_VS_ALL` (default: 1,000,000)
- Output: `OUTPUT_DIR_ALL_VS_ALL/tournament_results.json`
- Shows multiplayer dynamics performance

**Purpose:** Head-to-head reveals direct matchup strengths; all-vs-all shows multiplayer behavior.

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

## Behavioral Analysis

Set `SAVE_REPLAYS = True` in config. Auto-generated analysis includes:

**Overall Performance**
- Win rates, average scores
- Rounds played/won

**Decision Patterns**
- Hit/pass percentages
- Average hand value when passing

**Risk Behavior**
- Bust rates
- Average hand value when busting
- Second Chance usage

**Special Achievements**
- Flip 7 achievement rates
- Action card usage patterns

## Reference Bots

- **RandomBot**: Random decisions (baseline)
- **ConservativeBot**: Passes at 15+ points
- **Hit17Bot**: Hits until 17 (Blackjack-style)

Sample results (100 games head-to-head):

| Rank | Bot | Win Rate | Avg Score |
|------|-----|----------|-----------|
| 1 | Hit17Bot | 75.0% | 202.2 |
| 2 | ConservativeBot | 60.0% | 191.2 |
| 3 | RandomBot | 15.0% | 145.4 |

## Configuration Examples

### Quick Test
```python
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100
GAMES_PER_MATCHUP_ALL_VS_ALL = 100
SAVE_REPLAYS = False
```
Runtime: ~few minutes

### Medium Analysis
```python
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 10_000
GAMES_PER_MATCHUP_ALL_VS_ALL = 10_000
SAVE_REPLAYS = False
```
Runtime: ~1-2 hours

### Production Scale
```python
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100_000
GAMES_PER_MATCHUP_ALL_VS_ALL = 1_000_000
SAVE_REPLAYS = False
```
Runtime: ~30-50 hours

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

## Bot Development Workflow

1. Start with basic threshold strategy
2. Test with 100 games
3. Scale: 1000 → 10000 → 100000
4. Use SAVE_REPLAYS=True on smaller runs
5. Adjust based on behavioral patterns
6. Consider early/late game and ahead/behind scenarios

## Troubleshooting

**Bot Not Found**
- Ensure bot file is in `flip7/bots/` directory
- Built-in bots: `RandomBot`, `ConservativeBot`, `Hit17Bot`
- Custom bots: Use `module.ClassName` format (e.g., `my_bot.MyBot`)

**Bot Timeout**
- Default timeout: 1 second
- Avoid expensive computations in decision methods
- Pre-calculate probabilities or use lookup tables

**Import Errors**
- Use `uv run` prefix for all commands
- Run `uv sync --all-extras` to reinstall

**Tournament Doesn't Find Bot**
- File must be named `*_bot.py`
- Class must inherit from `BaseBot`
- File must be in `flip7/bots/` directory

**Compliance Tests Fail**
- Return types: `"hit"` or `"pass"` (strings), not booleans
- Second Chance: Return boolean, not string
- Action targets: Must return player ID from `eligible` list
- Run: `uv run pytest tests/test_bot_compliance.py -v -k YourBotName`

**No Output/Progress**
- Large tournaments take hours
- Reduce game counts in `tournament_config.py` for testing
- Check for infinite loops in bot logic
- Monitor progress bars

**Further Help**
- [DEBUGGING.md](DEBUGGING.md) - Detailed debugging guide
- [BUILDING_A_BOT.md](BUILDING_A_BOT.md) - Bot development guide
- Use `--help`: `uv run flip7 --help`, `uv run flip7-step --help`

## Game Rules

See [RULES.md](RULES.md) for complete rules.

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
