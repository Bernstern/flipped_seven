#!/usr/bin/env python3
"""Quick demo - watch two bots play one game to 200 points."""

from pathlib import Path
from flip7.core.game_engine import GameEngine
from flip7.bots import RandomBot, ScaredyBot


def main():
    print("=" * 60)
    print("FLIP 7 - Quick Demo")
    print("=" * 60)
    print()
    print("Watching RandomBot vs ScaredyBot play to 200 points...")
    print()

    player_ids = ["random", "conservative"]
    bots = {
        "random": RandomBot("random"),
        "conservative": ScaredyBot("conservative"),
    }

    engine = GameEngine(
        game_id="demo",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("demo.jsonl"),
        seed=42,
    )

    result = engine.execute_game()

    print()
    print("=" * 60)
    print("GAME COMPLETE!")
    print("=" * 60)
    print()
    print(f"Winner: {result.winner}")
    print(f"Total rounds: {result.current_round}")
    print()
    print("Final Scores:")
    for player_id in player_ids:
        score = result.scores[player_id]
        marker = " (WINNER)" if player_id == result.winner else ""
        print(f"  {player_id}: {score} points{marker}")
    print()


if __name__ == "__main__":
    main()
