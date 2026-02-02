# Debugging Guide

## Interactive Round Stepper

The round stepper is a powerful tool for understanding bot behavior by stepping through a single round turn-by-turn.

### Basic Usage

```bash
# Run with default bots (RandomBot vs ConservativeBot)
uv run python step_round.py

# Test your custom bot
uv run python step_round.py my_bot.MyBot ConservativeBot

# Use a specific seed for reproducibility
uv run python step_round.py RandomBot ConservativeBot --seed 42

# Test with any bot class
uv run python step_round.py my_bot.AggressiveBot my_bot.DefensiveBot

# Simulate mid-game scenario (bot1 has 100 points, bot2 has 150 points, round 8)
uv run python step_round.py RandomBot ConservativeBot --scores 100,150 --round 8
```

### Simulating Mid-Game Scenarios

The stepper lets you test how bots behave in specific game situations:

```bash
# Close game in late rounds (both bots near 200)
uv run python step_round.py MyBot ConservativeBot --scores 180,185 --round 15

# Bot is behind and needs to catch up
uv run python step_round.py MyBot RandomBot --scores 120,180 --round 12

# Bot is ahead and should play conservatively
uv run python step_round.py MyBot RandomBot --scores 180,120 --round 12
```

This helps you verify your bot makes smart decisions based on:
- Whether it's ahead or behind
- How close opponents are to winning (200 points)
- Which round of the game it is

### What You'll See

#### 1. Initial Deal Phase
Each player receives their first card. You'll see:
- Which player is receiving the card
- What card was drawn
- The player's tableau after receiving the card

#### 2. Turn Cycle Phase
For each turn, you'll see:
- **Current player's turn** (highlighted)
- **All tableaus** showing each player's:
  - Number cards (with count of unique values)
  - Modifier cards
  - Second Chance availability
  - Status (ACTIVE, PASSED, BUSTED, FROZEN)

- **Complete decision context** that the bot receives:
  - **My Tableau**: Hand value, unique numbers, number cards, modifier cards, Second Chance
  - **Opponents**: Each opponent's hand value, unique numbers, and status
  - **Game State**: Cards remaining in deck, current round number, target score
  - **Cumulative Scores**: All players' scores across rounds

- **Bot's decision** (HIT or PASS)

- **Card drawn** (if hitting):
  - Number card: Shows if it causes a bust or Flip 7
  - Modifier card: Added to tableau
  - Action card: Bot chooses target, effect applied

- **Special events**:
  - Bust detection and Second Chance decision
  - Flip 7 achievement (auto-pass)
  - Freeze effect (forces pass)
  - Flip Three effect (draws 3 cards)

#### 3. Final Scoring Phase
Detailed score breakdown for each player:
- Number Cards Sum
- After X2 Multiplier
- Modifier Additions (+2/+4/+6/+8/+10)
- Flip 7 Bonus (+15)
- **FINAL SCORE**

### Example Session

```bash
$ uv run python step_round.py RandomBot ConservativeBot --seed 42 --scores 95,110 --round 6

────────────────────────── Interactive Round Stepper ───────────────────────────

Phase 1: Initial Deal

RandomBot_1 receives initial card...
Press Enter to continue...
  Drew: Number 12

      RandomBot_1's Tableau
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Card Type      ┃ Cards         ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Number Cards   │ 12 (1 unique) │
│ Modifier Cards │ None          │
│ Second Chance  │ ✗             │
│ Status         │ ACTIVE        │
└────────────────┴───────────────┘

ConservativeBot_2 receives initial card...
Press Enter to continue...
...

Phase 2: Turn Cycle

───────────────────────────────── Turn 1 ─────────────────────────────────────

>>> RandomBot_1's Turn

>>> RandomBot_1 (Current Player) <<<
      RandomBot_1's Tableau
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Card Type      ┃ Cards         ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Number Cards   │ 12 (1 unique) │
│ Modifier Cards │ None          │
│ Second Chance  │ ✗             │
│ Status         │ ACTIVE        │
└────────────────┴───────────────┘

ConservativeBot_2
      ConservativeBot_2's Tableau
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Card Type      ┃ Cards         ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Number Cards   │ 5 (1 unique)  │
│ Modifier Cards │ None          │
│ Second Chance  │ ✗             │
│ Status         │ ACTIVE        │
└────────────────┴───────────────┘

   Decision Context (What the Bot Sees)
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property                ┃ Value                        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ My Tableau              │                              │
│   Hand Value            │ 12                           │
│   Unique Numbers        │ 1/7                          │
│   Number Cards          │ 12                           │
│   Modifier Cards        │ None                         │
│   Has Second Chance     │ No                           │
│ Opponents               │                              │
│   ConservativeBot_2     │ Value: 5, Unique: 1, ACTIVE  │
│ Game State              │                              │
│   Cards Remaining       │ 92                           │
│   Current Round         │ 6                            │
│   Target Score          │ 200                          │
│ Cumulative Scores       │                              │
│   My Score              │ 95                           │
│   ConservativeBot_2     │ 110                          │
└─────────────────────────┴──────────────────────────────┘

Asking RandomBot_1 to decide: hit or pass?
Press Enter to continue...
→ Decision: HIT

RandomBot_1 draws a card...
Press Enter to continue...
  Drew: Number 7

      RandomBot_1's Tableau
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Card Type      ┃ Cards         ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Number Cards   │ 12, 7 (2 uni) │
│ Modifier Cards │ None          │
│ Second Chance  │ ✗             │
│ Status         │ ACTIVE        │
└────────────────┴───────────────┘
...
```

### Tips for Debugging

1. **Use a fixed seed** to reproduce specific scenarios:
   ```bash
   uv run python step_round.py MyBot RandomBot --seed 12345
   ```

2. **Watch for bust conditions**: See exactly when your bot draws duplicates and how it decides to use Second Chance

3. **Understand action cards**: See which targets your bot selects for Freeze/Flip Three

4. **Track Flip 7 progress**: Watch the unique number count as your bot draws cards

5. **Analyze score calculations**: See the full breakdown at the end to understand scoring

6. **Compare strategies**: Run the same seed with different bots to compare decisions

7. **Test mid-game scenarios**: Use `--scores` to see how your bot behaves when ahead/behind:
   ```bash
   # Test when behind
   uv run python step_round.py MyBot RandomBot --scores 120,180 --round 12

   # Test when ahead
   uv run python step_round.py MyBot RandomBot --scores 180,120 --round 12

   # Test close endgame
   uv run python step_round.py MyBot RandomBot --scores 185,195 --round 20
   ```

### Troubleshooting

**Bot not found?**
- Built-in bots: `RandomBot`, `ConservativeBot`
- Custom bots: Use `module.ClassName` format (e.g., `my_bot.MyBot`)
- Make sure your bot file is in the current directory or PYTHONPATH

**Bot times out?**
- The default timeout is 5 seconds per decision
- Check if your bot has infinite loops or blocking operations
- Add logging to see where it's getting stuck

**Want to automate stepping?**
- Pipe newlines: `yes "" | head -50 | uv run python step_round.py`
- Or use the test script: `./test_stepper.sh`

### Combining with Tournament Testing

1. **Develop strategy** by stepping through rounds manually
2. **Test edge cases** with specific seeds that cause interesting scenarios
3. **Test game phases** with `--scores` and `--round` to simulate early/mid/late game
4. **Run small tournament** (NUM_GAMES=100) to get statistics
5. **Iterate and refine** based on results
6. **Scale up** to larger tournaments (1000+ games)

The stepper is perfect for understanding *why* your bot made certain decisions, while the tournament system tells you *how well* those decisions perform at scale.

## What the Bot Sees

The decision context includes **everything** your bot has access to when making decisions:

### My Tableau
- Hand value (sum of number cards)
- Unique numbers count (X/7 for Flip 7)
- All number cards
- All modifier cards
- Second Chance availability

### Opponents
For each opponent:
- Hand value
- Unique numbers count
- Current status (ACTIVE, PASSED, BUSTED, FROZEN)

### Game State
- Cards remaining in the deck
- Current round number
- Target score (200)

### Cumulative Scores
- Your score across all rounds so far
- Each opponent's score across all rounds

**The stepper now shows ALL of this information** in the "Decision Context (What the Bot Sees)" table at each decision point. This is exactly what your bot's `decide_hit_or_pass`, `decide_use_second_chance`, and `choose_action_target` methods receive.
