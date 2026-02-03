# Debugging Reference

## Interactive Round Stepper

Step through a single round turn-by-turn to debug bot behavior.

### Commands

```bash
# Default bots
uv run flip7-step

# Custom bots
uv run flip7-step my_bot.MyBot ConservativeBot

# Fixed seed
uv run flip7-step RandomBot ConservativeBot --seed 42

# Mid-game scenario (scores, round number)
uv run flip7-step RandomBot ConservativeBot --scores 100,150 --round 8
```

### Test Scenarios

```bash
# Close late-game
uv run flip7-step MyBot ConservativeBot --scores 180,185 --round 15

# Behind, needs catch-up
uv run flip7-step MyBot RandomBot --scores 120,180 --round 12

# Ahead, play conservative
uv run flip7-step MyBot RandomBot --scores 180,120 --round 12
```

### Output Phases

**Phase 1: Initial Deal**
- Each player receives first card
- Shows card drawn and tableau state

**Phase 2: Turn Cycle**
- All tableaus: number cards (unique count), modifiers, Second Chance, status
- Decision context (see below)
- Bot decision (HIT/PASS)
- Card drawn and effects
- Special events: bust, Second Chance decision, Flip 7, Freeze, Flip Three

**Phase 3: Final Scoring**
- Number cards sum
- After X2 multiplier
- Modifier additions (+2/+4/+6/+8/+10)
- Flip 7 bonus (+15)
- Final score

### Decision Context

What the bot receives at each decision point:

**My Tableau**
- Hand value
- Unique numbers (X/7)
- Number cards
- Modifier cards
- Second Chance available

**Opponents**
- Hand value
- Unique numbers
- Status (ACTIVE/PASSED/BUSTED/FROZEN)

**Game State**
- Cards remaining
- Current round
- Target score (200)

**Cumulative Scores**
- All player scores across rounds

### Debugging Techniques

**Reproduce scenarios**
```bash
uv run flip7-step MyBot RandomBot --seed 12345
```

**Compare strategies**
```bash
# Run same seed with different bots
uv run flip7-step MyBot RandomBot --seed 42
uv run flip7-step OtherBot RandomBot --seed 42
```

**Test game phases**
```bash
# Early game
uv run flip7-step MyBot RandomBot --scores 30,25 --round 3

# Mid game
uv run flip7-step MyBot RandomBot --scores 120,110 --round 10

# Late game
uv run flip7-step MyBot RandomBot --scores 185,195 --round 20
```

**Automate stepping**
```bash
# Skip all prompts
yes "" | head -50 | uv run flip7-step
```

### Troubleshooting

**Bot not found**
- Built-in: `RandomBot`, `ConservativeBot`
- Custom: `module.ClassName` format
- Check file in current directory or PYTHONPATH

**Bot timeout (5s default)**
- Check for infinite loops or blocking operations
- Add logging to identify bottlenecks

### Workflow

1. Step through rounds manually to develop strategy
2. Test edge cases with specific seeds
3. Test game phases with `--scores` and `--round`
4. Run small tournament (NUM_GAMES=100) for statistics
5. Iterate based on results
6. Scale to larger tournaments (1000+ games)

Stepper shows *why* decisions are made. Tournament shows *how well* they perform.
