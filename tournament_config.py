"""Tournament Configuration - Edit the constants below to customize your tournament.

After editing, run: uv run flip7 tournament
"""

from pathlib import Path

from flip7.bots import ConservativeBot, RandomBot

# ============================================================================
# TOURNAMENT CONFIGURATION - EDIT THESE VALUES
# ============================================================================

# Tournament name (used in output files)
TOURNAMENT_NAME = "Bot Performance Analysis"

# Number of players per game (2, 3, or 4)
PLAYERS_PER_GAME = 2

# Total number of games to run
# Examples:
#   - 100: Quick testing
#   - 1000: Medium testing
#   - 10000: Large scale
#   - 100000: Massive scale (will take hours)
NUM_GAMES = 1000

# List of bots to compete (must have unique class names)
# Games will rotate through all possible matchups
BOT_CLASSES = [
    RandomBot,
    ConservativeBot,
    # Add your bots here:
    # MyCustomBot,
    # AggressiveBot,
]

# Bot timeout in seconds (bots that exceed this will forfeit)
BOT_TIMEOUT_SECONDS = 5.0

# Output directory for results
OUTPUT_DIR = Path("./tournament_results")

# Save individual game replays (set to False for large tournaments to save disk space)
SAVE_REPLAYS = False

# Random seed for reproducibility (None = random)
TOURNAMENT_SEED = 42

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

# Note: The tournament will run NUM_GAMES total games, cycling through
# all possible matchups of PLAYERS_PER_GAME bots from BOT_CLASSES
