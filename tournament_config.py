"""Tournament Configuration - Minimal config, all bots auto-discovered.

After editing, run: uv run flip7

This automatically executes TWO complete tournaments:

1. HEAD-TO-HEAD TOURNAMENT (2-player)
   - Every bot plays every other bot directly (round-robin)
   - Games per matchup: GAMES_PER_MATCHUP_HEAD_TO_HEAD
   - Shows head-to-head win/loss matrix
   - Results saved to: OUTPUT_DIR_HEAD_TO_HEAD/

2. ALL-VS-ALL TOURNAMENT (multiplayer)
   - All bots compete in the same game simultaneously
   - Total games: GAMES_PER_MATCHUP_ALL_VS_ALL
   - Shows multiplayer dynamics and overall performance
   - Results saved to: OUTPUT_DIR_ALL_VS_ALL/

All bots in flip7/bots/ directory are automatically discovered!
"""

from pathlib import Path

# ============================================================================
# TOURNAMENT CONFIGURATION - EDIT THESE VALUES
# ============================================================================

# Tournament identification
TOURNAMENT_NAME = "Bot Performance Analysis"

# How many games should each unique matchup play?
# Examples:
#   - 10-100: Quick testing
#   - 1,000: Good statistical sample
#   - 10,000: High confidence
#   - 100,000+: Production analysis
#
# VALIDATION: Must be > 0 (integers only)
# WARNING: Values > 100,000,000 will take very long to run
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 1_000  # For 2-player head-to-head
GAMES_PER_MATCHUP_ALL_VS_ALL = 10_000  # For all bots playing together

# Bot timeout (bots that exceed this will forfeit)
# 1.0 second allows reasonable computation
#
# VALIDATION: Must be > 0 (float or int)
# RECOMMENDED RANGE: 0.1 to 5.0 seconds
# WARNING: Values > 300 seconds are unreasonable
# WARNING: Values < 0.01 seconds may cause legitimate bots to timeout
BOT_TIMEOUT_SECONDS = 1.0

# Output directories
# VALIDATION: Must be Path objects with writable parent directories
OUTPUT_DIR_HEAD_TO_HEAD = Path("./tournament_results_head_to_head")
OUTPUT_DIR_ALL_VS_ALL = Path("./tournament_results_all_vs_all")

# Save individual game replays?
# Warning: Uses significant disk space for large tournaments
SAVE_REPLAYS = False

# Random seed for reproducibility (None = random)
TOURNAMENT_SEED = 42

# ============================================================================
# AUTOMATIC BOT DISCOVERY
# ============================================================================
# All bots in flip7/bots/ are automatically discovered and included.
# No need to manually add bots here!
#
# To add a new bot:
# 1. Create flip7/bots/my_bot.py
# 2. Define a class that inherits from BaseBot
# 3. Run the tournament - your bot is automatically included!
# ============================================================================
